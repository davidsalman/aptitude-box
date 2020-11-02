from datetime import datetime
from firebase import db, store
from gpiozero import Button, LED
from os import path
from pygame import mixer
from time import sleep
import RPi.GPIO as GPIO
import serial

# Constants

GAME_DB = 'games'
GAME_ID = 'proto-box-dial-it-in'
GAME_NAME = 'Dial It In Game'
MAX_LEVEL = 3
MAX_SCORE = MAX_LEVEL * 3
MAX_STRIKES = 3
PINS = [[27, 22], [23, 24], [10, 9]]
ARDUINO_RESET_PIN = 18
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/dial_it_in'
ACTIVATE_GAME_BUTTON = 15
START_BUTTON = 14
START_LED = 4

# Variables

activate_feedback = True
activate_dial_1_feedback_success = True
activate_dial_2_feedback_success = True
activate_dial_3_feedback_success = True
activate_dial_1_feedback_failure = True
activate_dial_2_feedback_failure = True
activate_dial_3_feedback_failure = True
last_value = 0
io = [[None, None], [None, None], [None, None]]
coms = None
baud = 57600
level = 1
port = '/dev/ttyACM0'
score = 0
strikes = 0
activate_game_button = Button(ACTIVATE_GAME_BUTTON)
start_led = LED(START_LED)
start_button = Button(START_BUTTON)

# Functions

def read_dial(dial_index):
  done = False
  mistake = False
  if io[dial_index][1].value == 0:
    done = True
  if io[dial_index][0].value == 0:
    mistake = True
  return done, mistake

def check_dial(dial_index, done, mistake):
  global activate_dial_1_feedback_success, activate_dial_2_feedback_success, activate_dial_3_feedback_success, activate_dial_1_feedback_failure, activate_dial_2_feedback_failure, activate_dial_3_feedback_failure
  if done:
    if activate_dial_1_feedback_success and dial_index == 0 or activate_dial_2_feedback_success and dial_index == 1 or activate_dial_3_feedback_success and dial_index == 2:
      right_position()
    if dial_index == 0:
      activate_dial_1_feedback_success = False
    elif dial_index == 1:
      activate_dial_2_feedback_success = False
    else:
      activate_dial_3_feedback_success = False 
  if mistake:
    if activate_dial_1_feedback_failure and dial_index == 0 or activate_dial_2_feedback_failure and dial_index == 1 or activate_dial_3_feedback_failure and dial_index == 2:  
      wrong_position()
    if dial_index == 0:
      activate_dial_1_feedback_failure = False
    elif dial_index == 1:
      activate_dial_2_feedback_failure = False
    else:
      activate_dial_3_feedback_failure = False 
  if not done:
    if dial_index == 0:
      activate_dial_1_feedback_success = True
    elif dial_index == 1:
      activate_dial_2_feedback_success = True
    else:
      activate_dial_3_feedback_success = True
  if not mistake:
    if dial_index == 0:
      activate_dial_1_feedback_failure = True
    elif dial_index == 1:
      activate_dial_2_feedback_failure = True
    else:
      activate_dial_3_feedback_failure = True

def read_dials():
  value = None
  try:
    coms.reset_input_buffer()
    blob = coms.readline()
    value = blob.decode('utf-8').replace('\r','').replace('\n','')
    if value == '':
      value = '0'
    value = int(value)
    if value > 20:
      value = 0
  except (UnicodeDecodeError, ValueError):
    value = 0
  return value

def right_position():
  global score
  sfx_locked = mixer.Sound(SOUNDS_PATH + '/sfx/locked.wav')
  sfx_locked.play()
  score += 1

def wrong_position():
  global strikes
  sfx_unlocked = mixer.Sound(SOUNDS_PATH + '/sfx/unlocked.wav')
  sfx_unlocked.play()
  strikes += 1

def reset_game():
  global activate_feedback, activate_dial_1_feedback_success, activate_dial_2_feedback_success, activate_dial_3_feedback_success, activate_dial_1_feedback_failure, activate_dial_2_feedback_failure, activate_dial_3_feedback_failure, last_value, level, score, strikes
  activate_feedback = True
  activate_dial_1_feedback_success = True
  activate_dial_2_feedback_success = True
  activate_dial_3_feedback_success = True
  activate_dial_1_feedback_failure = True
  activate_dial_2_feedback_failure = True
  activate_dial_3_feedback_failure = True
  last_value = 0
  level = 1
  score = 0
  strikes = 0

def reset_arduino():
  GPIO.output(ARDUINO_RESET_PIN, 0)
  sleep(0.1)
  GPIO.output(ARDUINO_RESET_PIN, 1)
  sleep(0.1)

def setup_io():
  setup_serial()
  setup_dials()

def setup_serial():
  global coms
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(ARDUINO_RESET_PIN, GPIO.OUT, initial=1)
  reset_arduino()
  sleep(5)
  coms = serial.Serial(port, baud)

def setup_dials():
  global io
  for i in range(3):
    for j in range(2):
      if io[i][j] is not None:
        io[i][j].close()
      io[i][j] = Button(PINS[i][j])

# Main

def init():
  mixer.init()
  db_connection = False
  while db_connection is False:
    try:
      game_ref = db.reference(GAME_DB).child(GAME_ID)
      game_ref.get()
      db_connection = True
    except:
      print('Unable to find game databse reference. Trying again in 10 seconds ...')
      sleep(10)
  if game_ref.get() == None:
    game_ref.set({
      'name': GAME_NAME,
      'alive': True,
      'status': 'Initializing',
      'score': score,
      'max_score': MAX_SCORE,
      'strikes': strikes,
      'max_strikes': MAX_STRIKES,
      'started_at': 0,
      'completed_at': 0
    })
  else:
    game_ref.update({
      'alive': True,
      'status': 'Initailizing',
      'score': score,
      'strikes': strikes,
      'started_at': 0,
      'completed_at': 0
    })
  sleep(2)

def start():
  reset_game()
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  game_ref.update({
    'status': 'Ready',
    'score': score,
    'strikes': strikes,
    'started_at': 0,
    'completed_at': 0
  })
  dialog_start_counter = 0
  while not start_button.is_pressed:
    if dialog_start_counter == 0:
      dialog_start = mixer.Sound(SOUNDS_PATH + '/dialog/start.wav')
      dialog_start.play()
    start_led.blink(0.5, 0.5, 1, False)
    dialog_start_counter += 1
    if dialog_start_counter > 30:
      dialog_start_counter = 0
  start_led.off()
  dialog_instructions = mixer.Sound(SOUNDS_PATH + '/dialog/instructions.wav')
  dialog_instructions.play()
  game_ref.update({
    'status': 'Playing',
    'started_at': datetime.utcnow().timestamp()
  })
  setup_io()
  sleep(25)

def loop():
  global activate_feedback, last_value, level, score, strikes
  dials_value = 0
  while dials_value != 16 and level <= MAX_LEVEL and strikes < MAX_STRIKES:
    dials_value = read_dials()
    if dials_value != last_value:
      last_value = dials_value
      sfx_click = mixer.Sound(SOUNDS_PATH + '/sfx/click.wav')
      sfx_click.play()
    if dials_value == 16:
      if activate_feedback:
        reset_arduino()
        sleep(2)
        level += 1
        if level <= MAX_LEVEL:
          dialog_right_positions = mixer.Sound(SOUNDS_PATH + '/dialog/right_positions.wav')
          dialog_right_positions.play()
        activate_feedback = False
    elif dials_value >= 18:
      if activate_feedback:
        dialog_wrong_positions = mixer.Sound(SOUNDS_PATH + '/dialog/wrong_positions.wav')
        dialog_wrong_positions.play()
        activate_feedback = False
    else:
      activate_feedback = True
    for i in range(3):
      done, mistake = read_dial(i)
      check_dial(i, done, mistake)
    if start_button.is_pressed:
      break
    sleep(1)

def complete():
  global score
  sleep(2)
  score -= strikes
  if score < 0:
    score = 0
  if strikes < MAX_STRIKES:
    dialog_success = mixer.Sound(SOUNDS_PATH + '/dialog/on_success.wav')
    dialog_success.play()
  else:
    dialog_failure = mixer.Sound(SOUNDS_PATH + '/dialog/on_failure.wav')
    dialog_failure.play()
  print('Result: [ Score: {}, Strikes {} ]'.format(score, strikes))
  end_time = datetime.utcnow().timestamp()
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  game_ref.update({
    'status': 'Finished',
    'score': score,
    'strikes': strikes,
    'completed_at': end_time
  })
  game_snapshot = game_ref.get()
  start_time = 0
  for key, val in game_snapshot.items():
    if key == 'started_at':
      start_time = val
  store.collection('results').add({
    'game_reference': GAME_ID,
    'started_at': start_time,
    'completed_at': end_time,
    'score': score,
    'strikes': strikes,
    'max_score': MAX_SCORE,
    'max_strikes': MAX_STRIKES
  })
  sleep(10)
  coms.close()

def clean_up():
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  game_ref.update({
    'alive': False,
    'status': 'Inactive',
    'started_at': 0,
    'completed_at': 0
  })
  mixer.quit()

if __name__ == '__main__':
  try:
    print('Initializing ...')
    init()
    print('Dial It In Game is now active!')
    while True:
      if not activate_game_button.is_pressed:
        sleep(1)
        continue
      print('Press the start button to play ...')
      start()
      while level <= MAX_LEVEL and strikes < MAX_STRIKES:
        print('Score: {}, Strikes: {}'.format(score, strikes))
        loop()
        if start_button.is_pressed:
          break
      print('Dial It In Game completed!')
      complete()
  except KeyboardInterrupt:
    print('Keyboard interrupt detected! Closing ...')
  except:
    print('Error detected! Closing ...')
  finally:
    clean_up()

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
MAX_LEVEL = 5
MAX_SCORE = MAX_LEVEL * 3
MAX_STRIKES = 3
ARDUINO_RESET_PIN = 18
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/dial_it_in'
START_PIN = 26
START_LED = 25

# Variables

activate_feedback = True
last_value = 0
coms = None
baud = 57600
level = 1
port = '/dev/ttyACM0'
score = 0
strikes = 0

def read_dials():
  value = None
  try:
    coms.reset_input_buffer()
    blob = coms.readline()
    value = blob.decode('utf-8').replace('\r','').replace('\n','')
    if value == '':
      value = '0'
    value = int(value)
    if value > 36:
      value = 0
  except (UnicodeDecodeError, ValueError):
    value = 0
  return value

def reset_game():
  global last_value, level, score, strikes
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
  global coms
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(ARDUINO_RESET_PIN, GPIO.OUT, initial=1)
  reset_arduino()
  sleep(2)
  coms = serial.Serial(port, baud)

def init():
  mixer.init()
  game_ref = db.reference(GAME_DB).child(GAME_ID)
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
  dialog_start = mixer.Sound(SOUNDS_PATH + '/dialog/start.wav')
  dialog_start.play()
  start_led = LED(START_LED)
  start_led.blink(0.5, 0.5, None, True)
  start_button = Button(START_PIN)
  start_button.wait_for_press()
  start_led.close()
  dialog_instructions = mixer.Sound(SOUNDS_PATH + '/dialog/instructions.wav')
  dialog_instructions.play()
  game_ref.update({
    'status': 'Playing',
    'started_at': datetime.utcnow().timestamp()
  })
  setup_io()
  sleep(1)

def loop():
  global activate_feedback, last_value, level, score, strikes
  dials_value = 0
  while dials_value != 16:
    dials_value = read_dials()
    if dials_value != last_value:
      last_value = dials_value
      sfx_click = mixer.Sound(SOUNDS_PATH + '/sfx/click.wav')
      sfx_click.play()
    if dials_value == 16:
      if activate_feedback:
        sfx_locked = mixer.Sound(SOUNDS_PATH + '/sfx/locked.wav')
        sfx_locked.play()
        reset_arduino()
        if level <= MAX_LEVEL:
          dialog_right_position = mixer.Sound(SOUNDS_PATH + '/dialog/right_position.wav')
          dialog_right_position.play()
        activate_feedback = False
        level += 1
        score += 3
    elif dials_value >= 18:
      if activate_feedback:
        dialog_wrong_position = mixer.Sound(SOUNDS_PATH + '/dialog/wrong_position.wav')
        dialog_wrong_position.play()
        activate_feedback = False
        strikes += 1
    else:
      activate_feedback = True

def complete():
  global score 
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
  coms.close()
  sleep(10)

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
      print('Press the start button to play ...')
      start()
      while level <= MAX_LEVEL and strikes < MAX_STRIKES:
        print('Score: {}, Strikes: {}'.format(score, strikes))
        loop()
      print('Dial It In Game completed!')
      complete()
  except KeyboardInterrupt:
    print('Keyboard interrupt detected! Closing ...')
  finally:
    clean_up()
from datetime import datetime
from firebase import db, store
from gpiozero import Button, LED
import RPi.GPIO as GPIO
from os import path
from pygame import mixer
import serial
from time import sleep

# Constants

GAME_DB = 'games'
GAME_ID = 'proto-box-under-pressure'
GAME_NAME = 'Under Pressure Game'
MAX_LEVEL = 3
MAX_SCORE = MAX_LEVEL
MAX_STRIKES = 3
ARDUINO_RESET_PIN = 18
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/under_pressure'
START_PIN = 26
START_LED = 25

# Variables

achieved = 0
activate_instructions = True
input_received_time = 0
baud = 57600
level = 1
port = '/dev/ttyACM0'
mode = 'low'
coms = None
score = 0
strikes = 0

# Functions

def check_pressure(current_pressure, min_pressure, max_pressure):
  global achieved, input_received_time, level, score, strikes
  tmp = None
  try:
    tmp = current_pressure.decode('utf-8').replace('\r','').replace('\n','')
    if tmp == '':
      tmp = '0'
  except UnicodeDecodeError:
    tmp = '0'
  try:
    current_pressure = int(tmp)
    if current_pressure > 999:
      current_pressure = 0
  except ValueError:
    current_pressure = 0
  if current_pressure > min_pressure and current_pressure < max_pressure:
    if achieved % 2 != 0 :
      level += 1
      score += 1
      sfx_good = mixer.Sound(SOUNDS_PATH + '/sfx/good.wav')
      sfx_good.play()
      dialog_target_achieved = mixer.Sound(SOUNDS_PATH + '/dialog/target_achieved.wav')
      dialog_target_achieved.play()
      sleep(4)
    achieved += 1
    input_received_time = datetime.utcnow().timestamp()
  elif current_pressure > max_pressure:
    strikes += 1
    sfx_bad = mixer.Sound(SOUNDS_PATH + '/sfx/bad.wav')
    sfx_bad.play()
    dialog_too_much_pressure = mixer.Sound(SOUNDS_PATH + '/dialog/too_much_pressure.wav')
    dialog_too_much_pressure.play()
    sleep(4)

def reset_game():
  global achieved, activate_instructions, coms, input_received_time, level, mode, score, strikes
  achieved = 0
  activate_instructions = True
  input_received_time = 0
  level = 1
  mode = 'low'
  coms = None
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

# Main

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
  start_button.close()
  dialog_instructions = mixer.Sound(SOUNDS_PATH + '/dialog/instructions.wav')
  dialog_instructions.play()
  game_ref.update({
    'status': 'Playing',
    'started_at': datetime.utcnow().timestamp()
  })
  sleep(25)
  setup_io()

def loop():
  global achieved, activate_instructions, mode
  pressure = coms.readline()
  if mode == 'low':
    if activate_instructions:
      dialog_between_two_to_three = mixer.Sound(SOUNDS_PATH + '/dialog/between_200_to_300.wav')
      dialog_between_two_to_three.play()
      activate_instructions = False
    check_pressure(pressure, 200, 300)
  elif mode == 'medium':
    if activate_instructions:
      dialog_between_four_to_five = mixer.Sound(SOUNDS_PATH + '/dialog/between_400_to_500.wav')
      dialog_between_four_to_five.play()
      activate_instructions = False
    check_pressure(pressure, 400, 500)
  elif mode == 'high':
    if activate_instructions:
      dialog_between_six_to_seven = mixer.Sound(SOUNDS_PATH + '/dialog/between_600_to_700.wav')
      dialog_between_six_to_seven.play()
      activate_instructions = False
    check_pressure(pressure, 600, 700)
  if achieved > 2:
    achieved = 0
    activate_instructions = True
    if mode == 'low':
      mode = 'medium'
    elif mode == 'medium':
      mode = 'high'
    else:
      mode = 'low'
    game_ref = db.reference(GAME_DB).child(GAME_ID)
    game_ref.update({
      'score': score,
      'strikes': strikes
    })

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
    print('Under Pressure Game is now active!')
    while True:
      print('Press the start button to play ...')
      start()
      while level <= MAX_LEVEL and strikes < MAX_STRIKES:
        print('Score: {}, Strikes: {}'.format(score, strikes))
        loop()
      print('Under Pressure Game completed!')
      complete()
  except KeyboardInterrupt:
    print('Keyboard interrupt detected! Closing ...')
  finally:
    clean_up()
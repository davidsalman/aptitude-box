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
MAX_LEVEL = 1
MAX_SCORE = MAX_LEVEL
MAX_STRIKES = 3
ARDUINO_RESET_PIN = 18
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/dial_it_in'
START_PIN = 26
START_LED = 25

# Variables

activate_instructions = True
coms = None
baud = 57600
level = 1
port = '/dev/ttyACM0'
score = 0
strikes = 0

def reset_game():
  global level, score, strikes
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
  global activate_instructions
  noise = coms.readline()
  tmp = None
  try:
    tmp = noise.decode('utf-8').replace('\r','').replace('\n','')
    if tmp == '':
      tmp = '0'
  except UnicodeDecodeError:
    tmp = '0'
  try:
    noise = int(tmp)
    if noise > 999:
      noise = 0
  except ValueError:
    noise = 0
  if noise >= 16 and noise < 18:
    if activate_instructions:
      sfx_good = mixer.Sound(SOUNDS_PATH + '/sfx/good.wav')
      sfx_good.play()
      activate_instructions = False
  elif noise >= 18:
      sfx_bad = mixer.Sound(SOUNDS_PATH + '/sfx/bad.wav')
      sfx_bad.play()
      activate_instructions = False
  else:
    activate_instructions = True

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
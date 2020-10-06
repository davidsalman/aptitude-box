from datetime import datetime
from firebase import db, store
from gpiozero import Button, LED
from os import path
from pygame import mixer
from time import sleep

# Constants

GAME_DB = 'games'
GAME_ID = 'proto-box-dial-it-in'
GAME_NAME = 'Dial It In Game'
MAX_LEVEL = 1
MAX_SCORE = MAX_LEVEL
MAX_STRIKES = 3
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/push_pull'
START_PIN = 26
START_LED = 25

# Variables

level = 1
score = 0
strikes = 0

def reset_game():
  global level, score, strikes
  level = 1
  score = 0
  strikes = 0

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
  sleep(1)
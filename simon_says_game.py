from datetime import datetime
from firebase import db, store
from gpiozero import Button, LED
from math import ceil
from os import path
from pygame import mixer
from random import randrange
from time import sleep

# Constants

GAME_DB = 'games'
GAME_ID = 'proto-box-simon-says'
GAME_NAME = 'Simon Says Game'
MAX_LEVEL = 10
MAX_SCORE = MAX_LEVEL
MAX_STRIKES = 3
NUM_IO = 20
PINS = [1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/simon_says'
START_PIN = 23

# Variables

io = []
generated_sequence = [None] * MAX_LEVEL
player_sequence = [None]  * MAX_LEVEL
tally = [None] * MAX_STRIKES
level = 1
score = 0
strikes = 0
velocity = 600

# Functions

def generate_sequence():
  global generated_sequence
  for l in range(MAX_LEVEL):
    generated_sequence[l] = randrange(NUM_IO)

def play_sequence():
  for l in range(level):
    selected_led = generated_sequence[l]
    io[selected_led].on()
    sleep(velocity/1000)
    io[selected_led].off()

def get_player_sequence():
  set_as_buttons()
  level_passed = False
  for l in range(level):
    level_passed = False
    while level_passed is False:
      for i in range(NUM_IO):
        if io[i].is_pressed:
          io[i].wait_for_release()
          player_sequence[l] = i
          if generated_sequence[l] == player_sequence[l]:
            level_passed = True
          else:
            wrong_sequence()
            return
      sleep(0.01)
  right_sequence()

def right_sequence():
  global level, velocity, score
  set_as_leds()
  reset_leds()
  sleep(0.1)
  activate_leds()
  sleep(0.5)
  reset_leds()
  sleep(0.1)
  sfx_correct = mixer.Sound(SOUNDS_PATH + '/sfx/right_sequence.wav')
  sfx_correct.play()
  if velocity > 100:
    velocity -= 50
  level += 1
  score += 1

def wrong_sequence():
  global level, score, strikes, tally, velocity
  set_as_leds()
  for t in range(3):
    reset_leds()
    sleep(0.1)
    activate_leds()
    sleep(0.1)
  reset_leds()
  sleep(0.1)
  sfx_incorrect = mixer.Sound(SOUNDS_PATH + '/sfx/wrong_sequence.wav')
  sfx_incorrect.play()
  dialog_incorrect = mixer.Sound(SOUNDS_PATH + '/dialog/incorrect.wav')
  dialog_incorrect.play()
  level = 1
  velocity = 600
  tally[strikes] = score
  strikes += 1
  score = 0

def reset_game():
  global generated_sequence, player_sequence, tally, level, score, strikes, velocity
  generated_sequence = [None] * MAX_LEVEL
  player_sequence = [None]  * MAX_LEVEL
  tally = [None] * MAX_STRIKES
  level = 1
  score = 0
  strikes = 0
  velocity = 600
  set_as_leds()
  reset_leds()

def activate_leds():
  for led in io:
    led.on()

def reset_leds():
  for led in io:
    led.off()

def set_as_buttons():
  global io
  io.clear()
  for i in range(NUM_IO):
    io.append(Button(PINS[i]))

def set_as_leds():
  global io
  io.clear()
  for o in range(NUM_IO):
    io.append(LED(PINS[o]))

def reset_io():
  for x in io:
    x.close()

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
  start_button = Button(START_PIN)
  start_button.wait_for_press()
  dialog_instructions = mixer.Sound(SOUNDS_PATH + '/dialog/instructions.wav')
  dialog_instructions.play()
  game_ref.update({
    'status': 'Playing',
    'started_at': datetime.utcnow().timestamp()
  })
  sleep(30)

def loop():
  if level == 1:
    generate_sequence()
  play_sequence()
  get_player_sequence()
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  game_ref.update({
    'score': score,
    'strikes': strikes
  })

def complete():
  global score
  activate_leds()
  if strikes < MAX_STRIKES:
    score -= strikes  
    dialog_success = mixer.Sound(SOUNDS_PATH + '/dialog/on_success.wav')
    dialog_success.play()
  else:
    for x in tally:
      score += x
    score = ceil(score / strikes)
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
    'strikes': strikes
  })
  sleep(5)

def clean_up():
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  game_ref.update({
    'alive': False,
    'status': 'Inactive',
    'started_at': 0,
    'completed_at': 0
  })
  reset_io()
  mixer.quit()

if __name__ == '__main__':
  try:
    print('Initializing ...')
    init()
    print('Simon Says Game is now active!') 
    while True:
      print('Press the start button to play ...')
      start()
      while level <= MAX_LEVEL and strikes < MAX_STRIKES:
        print('Score: {}, Strikes: {}'.format(score, strikes))
        loop()
      print('Simon Says Game completed!')
      complete()
  except KeyboardInterrupt:
    print('Keyboard interrupt detected! Closing ...')
  finally:
    clean_up()

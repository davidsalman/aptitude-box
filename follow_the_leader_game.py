from datetime import datetime
from firebase import db, store
from gpiozero import Button, LED
from os import path
from pygame import mixer
from time import sleep

# Constants

GAME_DB = 'games'
GAME_ID = 'proto-box-follow-the-leader'
GAME_NAME = 'Follow The Leader Game'
MAX_LEVEL = 40
MAX_STRIKES = 3
NUM_IO = 20
PINS = [4, 17, 27, 22, 10, 9, 11, 0, 5, 6, 13, 19, 26, 21, 20, 16, 12, 1, 7, 8]
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/follow_the_leader'
START_PIN = 23

# Variables

io = []
mode = 'left'
left_sequence = [ 1, 6, 11, 16, 2, 7, 12, 17, 3, 8, 13, 18, 4, 9, 14, 19, 5, 10, 15, 20 ]
right_sequence = [ 5, 10, 15, 20, 4, 9, 14, 19, 3, 8, 13, 18, 2, 7, 12, 17, 1, 6, 11, 16 ]
level = 1
score = 0
strikes = 0

# Functions

def check_left_sequence():
  global io, level, score
  set_as_buttons()
  sequence = left_sequence[level-1]
  pin = io[sequence].pin
  state = io[sequence].value
  target = None
  if state == 0:
    target = 1
  else:
    target = 0
  while state != target:
    io[sequence] = LED(pin)
    io[sequence].blink(0.5, 0.5, 1, False)
    io[sequence] = Button(pin)
    state = io[sequence].value
    sleep(0.01)
  level += 1
  score += 1

def check_right_sequence():
  global io, level, score
  set_as_buttons()
  sequence = right_sequence[level-1]
  pin = io[sequence].pin
  state = io[sequence].value
  target = None
  if state == 0:
    target = 1
  else:
    target = 0
  while state != target:
    io[sequence] = LED(pin)
    io[sequence].blink(0.5, 0.5, 1, False)
    io[sequence] = Button(pin)
    state = io[sequence].value
    sleep(0.01)
  level += 1
  score += 1

def reset():
  global level, score, strikes
  level = 1
  score = 0
  strikes = 0

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

# Main 

def init():
  mixer.init()
  set_as_leds()
  reset_leds()
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  if game_ref.get() == None:
    game_ref.set({
      'name': GAME_NAME,
      'alive': True,
      'status': 'Initializing',
      'score': score,
      'max_score': MAX_LEVEL,
      'strikes': strikes,
      'max_strikes': MAX_STRIKES,
      'start_at': 0,
      'completed_at': 0
    })
  else:
    game_ref.update({
      'alive': True,
      'status': 'Initializing',
      'score': score,
      'strikes': strikes,
      'started_at': 0,
      'completed_at': 0
    })
    sleep(2)

def start():
  reset()
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  game_ref.update({
    'status': 'Ready',
    'score': score,
    'strikes': strikes,
    'started_at': 0,
    'completed_at': 0
  })
  start_button = Button(1)
  start_button.wait_for_press()
  # dialog_instructions = mixer.Sound(SOUNDS_PATH + '/instructions.wav')
  # dialog_instructions.play()
  game_ref.update({
    'status': 'Playing',
    'started_at': datetime.utcnow().timestamp()
  })
  sleep(30)

def loop():
  global mode
  if mode == 'left':
    check_left_sequence()
  if mode == 'right':
    check_right_sequence()
  if level == 21:
    mode = 'right'
  if level == 41:
    mode = 'left'     
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  game_ref.update({
    'score': score,
    'strikes': strikes
  })

def complete():
  set_as_leds()
  activate_leds()
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
  sleep(10)

def clean_up():
  global io
  game_ref = db.reference().child(GAME_ID)
  game_ref.update({
    'alive': False,
    'status': 'Inactive',
    'started_at': 0,
    'completed_at': 0
  })
  for x in io:
    x.close()
  mixer.quit()

if __name__ == '__main__':
  try:
    print('Initializing ...')
    init()
    print('Follow The Leader Game is now active!')
    while True:
      print('Press the start button to play ...')
      start()
      while level <= MAX_LEVEL and strikes < MAX_STRIKES:
        print('Score: {}, Strikes: {}'.format(score, strikes))
        loop()
      print('Follow The Leader Game completed!')
      complete()
  except KeyboardInterrupt:
    print('Keyboard interrupt detected! Closing ...')
  finally:
    clean_up()
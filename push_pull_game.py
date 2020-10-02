
from datetime import datetime
from firebase import db, store
from gpiozero import Button, LED
from os import path
from pygame import mixer
from random import randrange
from time import sleep

# Constants

GAME_DB = 'games'
GAME_ID = 'proto-box-push-pull-game'
GAME_NAME = 'Push Pull Game'
MAX_LEVEL = 5
MAX_STATES = 5
MAX_SCORE = MAX_LEVEL * MAX_STATES
MAX_STRIKES = 3
NUM_IO = 15
PINS = [[4, 5, 6], [7, 8, 9], [10, 11, 12], [13, 14, 15], [16, 17, 18]]
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/push_pull'
START_PIN = 23

# Variables

io = []
states = [None] * MAX_STATES
targets = [None] * MAX_STATES
mistake = [None] * MAX_STATES
level = 1
score = 0
strikes = 0

def generate_targets(target_index):
  if states[target_index] == 0 or states[target_index] == 2:
    targets[target_index] = 1
  elif states[target_index] == 1:
    rand_selection = randrange(2)
    if rand_selection == 0:
      targets[target_index] = 0
    else:
      targets[target_index] = 2

def read_switch(switch_state, switch_index):
  set_as_buttons()
  state = None
  if switch_state[0].value == 1 and switch_state[1].value == 1:
    state = 2
  elif switch_state[0].value == 0 and switch_state[1].value == 1:
    state = 1
  elif switch_state[0].value == 0 and switch_state[1].value == 0:
    state = 0 
  states[switch_index] = state

def show_current_state(switch_state, state):
  if state == 0:
    switch_state[0].blink(0.5, 0.5, 1, True)
  elif state == 1:
    switch_state[1].blink(0.5, 0.5, 1, True)
  elif state == 2:
    switch_state[2].blink(0.5, 0.5, 1, True)
  sleep(1)

def show_target_state(switch_state, target):
  if target == 0:
    switch_state[0].blink(0.25, 0.25, 2, True)
  elif target == 1:
    switch_state[1].blink(0.25, 0.25, 2, True)
  elif target == 2:
    switch_state[2].blink(0.25, 0.25, 2, True)
  sleep(1)

def activate_switch_leds(led_switches):
  for led in led_switches:
    led.on()

def right_state():
  global score
  score += 1

def wrong_state():
  global strikes
  strikes += 1  

def activate_leds():
  for x in io:
    for y in io[x]:
      y.on()

def reset_leds():
  for i in io:
    for o in io[i]:
      o.off()

def set_as_leds():
  global io
  io.clear()
  for o in range(MAX_STATES):
    io.append([])
    for j in range(3):
      io[o].append(Button[PINS[o][j]])

def set_as_buttons():
  global io
  io.clear()
  for i in range(MAX_STATES):
    io.append([])
    for j in range(2):
      io[i].append(Button[PINS[i][j]])
    
def reset_io():
  for i in io:
    for o in io[i]:
      o.close()

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
  start_button = Button(START_PIN)
  start_button.wait_for_press()
  dialog_instructions = mixer.Sound(SOUNDS_PATH + '/instructions.wav')
  dialog_instructions.play()
  game_ref.update({
    'status': 'Playing',
    'started_at': datetime.utcnow().timestamp()
  })
  sleep(30)

def loop():
  for s in range(MAX_STATES):
    read_switch(io[s], s)
  for t in range(MAX_STATES):
    generate_targets(t)
  while states[0] != targets[0] or states[1] != targets[1] or states[2] != targets[2] or states[3] != targets[3] or states[4] != targets[4]:
    for s in range(MAX_STATES):
      read_switch(io[s], s)
      set_as_leds()
      reset_leds()
      if states[s] == targets[s]:
        activate_switch_leds(io[s])
        right_state()
      else:
        show_current_state(io[s], states[s])
        show_target_state(io[s], targets[s])
  level += 1
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  game_ref.update({
    'score': score,
    'strikes': strikes
  })

def complete():
  global score
  activate_leds()
  score -= strikes
  if strikes < MAX_STRIKES:
    dialog_success = mixer.Sound(SOUNDS_PATH + '/on_success.wav')
    dialog_success.play()
  else:
    dialog_failure = mixer.Sound(SOUNDS_PATH + '/on_failure.wav')
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
  sleep(10)


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
    print('Push Pull Game is now active!') 
    while True:
      print('Press the start button to play ...')
      start()
      while level <= MAX_LEVEL and strikes < MAX_STRIKES:
        print('Score: {}, Strikes: {}'.format(score, strikes))
        loop()
      print('Push Pull Game completed!')
      complete()
  except KeyboardInterrupt:
    print('Keyboard interrupt detected! Closing ...')
  finally:
    clean_up()
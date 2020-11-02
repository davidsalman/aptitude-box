from datetime import datetime
from firebase import db, store
from firebase_admin.exceptions import FirebaseError
from gpiozero import Button, LED
from os import path
from pygame import mixer
from random import randrange
from time import sleep

# Constants

GAME_DB = 'games'
GAME_ID = 'proto-box-push-pull'
GAME_NAME = 'Push Pull Game'
MAX_LEVEL = 5
MAX_STATES = 5
MAX_SCORE = MAX_LEVEL * MAX_STATES
MAX_STRIKES = 3
NUM_IO = 15
PINS = [[4, 17, 27], [22, 10, 9], [11, 0, 5], [6, 13, 19], [23, 24, 18]]
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/push_pull'
START_BUTTON = 26
START_LED = 21

# Variables

io = [[None, None, None], [None, None, None], [None, None, None], [None, None, None], [None, None, None]]
origin = [None] * MAX_STATES
states = [None] * MAX_STATES
targets = [None] * MAX_STATES
done = [False] * MAX_STATES
mistake = [False] * MAX_STATES
level = 1
score = 0
strikes = 0
start_led = LED(START_LED)
start_button = Button(START_BUTTON)

def generate_targets(target_index):
  global targets  
  if states[target_index] == 0 or states[target_index] == 2:
    targets[target_index] = 1
  elif states[target_index] == 1:
    rand_selection = randrange(2)
    if rand_selection == 0:
      targets[target_index] = 0
    else:
      targets[target_index] = 2
      
def check_switch(switch_index):
  if states[switch_index] == targets[switch_index]:
    activate_switch_leds(io[switch_index])
  else:
    show_current_state(io[switch_index], states[switch_index])
    show_target_state(io[switch_index], targets[switch_index])

def check_state_against_target(switch_index):
  check_switch(switch_index)
  if states[switch_index] != targets[switch_index]:
    done[switch_index] = False
    if states[switch_index] != origin[switch_index]: 
      if not mistake[switch_index]:
        wrong_state()
        mistake[switch_index] = True
    else:
      mistake[switch_index] = False
  else:
    if not done[switch_index]:  
      right_state(switch_index)
      done[switch_index] = True

def read_origin(switch_state, switch_index):
  global origin
  state = None
  if switch_state[0].value == 1 and switch_state[1].value == 1:
    state = 2
  elif switch_state[0].value == 0 and switch_state[1].value == 1:
    state = 1
  elif switch_state[0].value == 0 and switch_state[1].value == 0:
    state = 0 
  origin[switch_index] = state

def read_switch(switch_state, switch_index):
  global states  
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
    switch_state[1].blink(0.5, 0.5, 1, True)
  elif state == 1:
    switch_state[0].blink(0.5, 0.5, 1, True)
  elif state == 2:
    switch_state[2].blink(0.5, 0.5, 1, True)

def show_target_state(switch_state, target):
  if target == 0:
    switch_state[1].blink(0.25, 0.25, 2, True)
  elif target == 1:
    switch_state[0].blink(0.25, 0.25, 2, True)
  elif target == 2:
    switch_state[2].blink(0.25, 0.25, 2, True)

def activate_switch_leds(led_switches):
  for led in led_switches:
    led.on()

def right_state(switch_index):
  global score
  activate_switch_leds(io[switch_index])
  sfx_success = mixer.Sound(SOUNDS_PATH + '/sfx/success.wav')
  sfx_success.play()
  score += 1

def wrong_state():
  global strikes
  sfx_failure = mixer.Sound(SOUNDS_PATH + '/sfx/failure.wav')
  sfx_failure.play()
  dialog_wrong = mixer.Sound(SOUNDS_PATH + '/dialog/wrong.wav')
  dialog_wrong.play()
  strikes += 1  

def reset_game():
  global io, done, mistake, states, targets, level, origin, score, strikes
  io = [[None, None, None], [None, None, None], [None, None, None], [None, None, None], [None, None, None]]
  origin = [None] * MAX_STATES
  states = [None] * MAX_STATES
  targets = [None] * MAX_STATES
  done = [False] * 5
  mistake = [False] * 5
  level = 1
  score = 0
  strikes = 0
  set_as_leds()
  reset_leds()

def activate_leds():
  for i in io:
    for o in i:
      o.on()

def reset_leds():
  for i in io:
    for o in i:
      o.off()

def set_as_leds():
  global io
  for o in range(MAX_STATES):
    for j in range(3):
      if io[o][j] is not None:
        io[o][j].close()
      io[o][j] = LED(PINS[o][j])

def set_as_buttons():
  global io
  for i in range(MAX_STATES):
    for j in range(3):
      if io[i][j] is not None:
        io[i][j].close()
      io[i][j] = Button(PINS[i][j])

def reset_io():
  for i in io:
    for o in i:
      o.close()

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
  sleep(1)

def loop():
  global done, mistake, level
  done = [False] * MAX_STATES
  mistake = [False] * MAX_STATES
  set_as_buttons()
  for s in range(MAX_STATES):
    read_switch(io[s], s)  
    read_origin(io[s], s)
    generate_targets(s)
  while states[0] != targets[0] or states[1] != targets[1] or states[2] != targets[2] or states[3] != targets[3] or states[4] != targets[4]:
    set_as_buttons()
    for s in range(MAX_STATES):
      read_switch(io[s], s)
    set_as_leds()
    for s in range(MAX_STATES):
      check_state_against_target(s)
    if start_button.is_pressed:
      break
    sleep(1)
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
        if start_button.is_pressed:
          break
      print('Push Pull Game completed!')
      complete()
  except KeyboardInterrupt:
    print('Keyboard interrupt detected! Closing ...')
  except:
    print('Error detected! Closing ...')
  finally:
    clean_up()

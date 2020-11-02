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
MAX_LEVEL = 20
MAX_SCORE = MAX_LEVEL * 3
MAX_STRIKES = 3
PINS = [4, 17, 27, 22, 10, 9, 11, 0, 5, 6, 13, 19, 26, 21, 20, 16, 12, 1, 7, 8]
SOUNDS_PATH = path.dirname(path.abspath(__file__)) + '/sounds/follow_the_leader'
START_BUTTON = 23
START_LED = 14

# Variables

io = []
mode = 'left'
left_hand_sequence = [20, 16, 12, 8, 4, 19, 15, 11, 7, 3, 18, 14, 10, 6, 2, 17, 13, 9, 5, 1]
right_hand_sequence = [17, 13, 9, 5, 1, 18, 14, 10, 6, 2, 19, 15, 11, 7, 3, 20, 16, 12, 8, 4]
level = 1
score = 0
strikes = 0
start_led = LED(START_LED)
start_button = Button(START_BUTTON)

# Functions

def check_both_hands_sequence():
  global io
  sequence_left = left_hand_sequence[level-1] - 1
  sequence_right = right_hand_sequence[level-1] - 1
  pin_left = io[sequence_left].pin.number
  pin_right = io[sequence_right].pin.number
  state_left = io[sequence_left].value
  state_right = io[sequence_right].value
  target_left = None
  target_right = None
  if state_left == 0:
    target_left = 1
  else:
    target_left = 0
  if state_right == 0:
    target_right = 1
  else:
    target_right = 0
  if level == 1 or level == 11:
    dialog_both_hands = mixer.Sound(SOUNDS_PATH + '/dialog/both_hands.wav')
    dialog_both_hands.play()
  while state_left != target_left or state_right != target_right:
    io[sequence_left].close()
    io[sequence_right].close()
    io[sequence_left] = LED(pin_left)
    io[sequence_right] = LED(pin_right)
    io[sequence_left].blink(0.5, 0.5, 1, True)
    io[sequence_right].blink(0.5, 0.5, 1, True)
    sleep(1.0)
    io[sequence_left].close()
    io[sequence_right].close()
    io[sequence_left] = Button(pin_left)
    io[sequence_right] = Button(pin_right)
    state_left = io[sequence_left].value
    state_right = io[sequence_right].value
    if start_button.is_pressed:
      break
    sleep(0.01)
  io[sequence_left].close()
  io[sequence_right].close()
  io[sequence_left] = LED(pin_left)
  io[sequence_right] = LED(pin_right)
  io[sequence_left].on()
  io[sequence_right].on()
  right_sequence()

def check_left_hand_sequence():
  global io
  sequence = left_hand_sequence[level-1] - 1
  pin = io[sequence].pin.number
  state = io[sequence].value
  target = None
  if state == 0:
    target = 1
  else:
    target = 0
  if level == 1:
    dialog_left_hand = mixer.Sound(SOUNDS_PATH + '/dialog/left_hand.wav')
    dialog_left_hand.play()
  while state != target:
    for i in range(level, MAX_LEVEL):
      if io[left_hand_sequence[i]-1].value == target:
        wrong_sequence() 
    io[sequence].close()
    io[sequence] = LED(pin)
    io[sequence].blink(0.5, 0.5, 1, False)
    io[sequence].close()
    io[sequence] = Button(pin)
    state = io[sequence].value
    if start_button.is_pressed:
      break
    sleep(0.01)
  io[sequence].close()
  io[sequence] = LED(pin)
  io[sequence].on()
  right_sequence()  

def check_right_hand_sequence():
  global io
  sequence = right_hand_sequence[level-1] - 1
  pin = io[sequence].pin.number
  state = io[sequence].value
  target = None
  if state == 0:
    target = 1
  else:
    target = 0
  if level == 1:
    dialog_right_hand = mixer.Sound(SOUNDS_PATH + '/dialog/right_hand.wav')
    dialog_right_hand.play()
  while state != target:
    for i in range(level, MAX_LEVEL):
      if io[right_hand_sequence[i]-1].value == target:
        wrong_sequence() 
    io[sequence].close()
    io[sequence] = LED(pin)
    io[sequence].blink(0.5, 0.5, 1, False)
    io[sequence].close()
    io[sequence] = Button(pin)
    state = io[sequence].value
    if start_button.is_pressed:
      break
    sleep(0.01)
  io[sequence].close()
  io[sequence] = LED(pin)
  io[sequence].on()
  right_sequence()

def right_sequence():
  global level, score
  sfx_correct = mixer.Sound(SOUNDS_PATH + '/sfx/beep.wav')
  sfx_correct.play()
  level += 1
  score += 1

def wrong_sequence():
  global strikes
  sfx_incorrect = mixer.Sound(SOUNDS_PATH + '/sfx/boop.wav')
  sfx_incorrect.play()
  dialog_wrong = mixer.Sound(SOUNDS_PATH + '/dialog/wrong.wav')
  dialog_wrong.play()
  strikes += 1

def reset_game():
  global level, mode, score, strikes, left_hand_sequence, right_hand_sequence
  level = 1
  mode = 'left'
  left_hand_sequence = [20, 16, 12, 8, 4, 19, 15, 11, 7, 3, 18, 14, 10, 6, 2, 17, 13, 9, 5, 1]
  right_hand_sequence = [17, 13, 9, 5, 1, 18, 14, 10, 6, 2, 19, 15, 11, 7, 3, 20, 16, 12, 8, 4]
  score = 0
  strikes = 0
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
  for i in range(len(PINS)):
    io.append(Button(PINS[i]))

def set_as_leds():
  global io
  io.clear()
  for o in range(len(PINS)):
    io.append(LED(PINS[o]))

def reset_io():
  for x in io:
    x.close()

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
  sleep(28)

def loop():
  global level, mode, left_hand_sequence, right_hand_sequence
  if level == 1:
    set_as_buttons()
  if level == 11 and mode == 'both':
    set_as_leds()
    reset_leds()
    set_as_buttons()
  if mode == 'both':
    check_both_hands_sequence()
  elif mode == "left":
    check_left_hand_sequence()  
  elif mode == 'right':
    check_right_hand_sequence()
  if level > MAX_LEVEL:
    level = 1
    set_as_leds()
    reset_leds()
    set_as_buttons()
    if mode == 'both':
      mode = 'done'
    elif mode == 'left':
      mode = 'right'
    elif mode == 'right':
      left_hand_sequence = [20, 16, 12, 8, 4, 19, 15, 11, 7, 3, 3, 7, 11, 15, 19, 4, 8, 12, 16, 20]
      right_hand_sequence = [17, 13, 9, 5, 1, 18, 14, 10, 6, 2, 2, 6, 10, 14, 18, 1, 5, 9, 13, 17]
      mode = 'both'
  game_ref = db.reference(GAME_DB).child(GAME_ID)
  game_ref.update({
    'score': score,
    'strikes': strikes
  })

def complete():
  global score
  set_as_leds()
  activate_leds()
  score -= strikes
  if strikes < MAX_STRIKES:
    dialog_success = mixer.Sound(SOUNDS_PATH + '/dialog/on_success.wav')
    dialog_success.play()
  else:
    if score < 0:
      score = 0
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
  sleep(6)

def clean_up():
  global io
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
    print('Follow The Leader Game is now active!')
    while True:
      print('Press the start button to play ...')
      start()
      while mode != 'done' and strikes < MAX_STRIKES:
        print('Score: {}, Strikes: {}'.format(score, strikes))
        loop()
        if start_button.is_pressed:
          break
      print('Follow The Leader Game completed!')
      complete()
  except KeyboardInterrupt:
    print('Keyboard interrupt detected! Closing ...')
  except:
    print('Error detected! Closing ...')
  finally:
    clean_up()
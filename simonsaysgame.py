from gpiozero import Button, LED
from math import ceil
from os import path
from pygame import mixer
from random import randrange
from time import sleep

# Constants

MAX_LEVEL = 10
NUM_IO = 20
SOUNDS_PATH = path.dirname(path.abspath(__file__) + '/sounds/simonsays')

# Variables

io = []
generated_sequence = []
player_sequence = [] 
tally = []
level = 1
score = 0
strikes = 0
velocity = 600

# Functions

def generate_sequence():
  for level in range(MAX_LEVEL):
    generated_sequence[level] = randrange(NUM_IO)

def play_sequence():
  for level in range(level):
    selected_led = generated_sequence[level]
    io[selected_led].on()
    sleep(velocity/1000)
    io[selected_led].off()

def get_player_sequence():
  set_as_button()
  level_passed = False
  for sequence in range(level):
    level_passed = False
    while level_passed is False:
      for i in range(NUM_IO):
        if io[i].is_pressed:
          player_sequence[sequence] = i
          if generated_sequence[sequence] == player_sequence[sequence]:
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
  if velocity > 100:
    velocity -= 50
  level += 1
  score += 1
  mixer.Sound(SOUNDS_PATH + '/right_sequence.wav')

def wrong_sequence():
  global level, score, strikes, tally, velocity
  set_as_leds()
  for t in range(3):
    reset_leds()
    sleep(0.1)
    activate_leds()
    sleep(0.2)
  reset_leds()
  sleep(0.1)
  level = 1
  velocity = 600
  tally[strikes] = score
  score = 0
  for x in range(strikes):
    score += tally[score]
  score = ceil(score / strikes)
  strikes += 1
  mixer.Sound(SOUNDS_PATH + '/wrong_sequence.wav')

def activate_leds():
  for led in io:
    led.on()

def reset_leds():
  for led in io:
    led.off()

def set_as_button():
  global io
  io.clear()
  for i in range(NUM_IO):
    io.append(Button(i+1))

def set_as_leds():
  global io
  io.clear()
  for o in range(NUM_IO):
    io.append(LED(o+1))

def clean_up():
  global io
  for x in io:
    x.close()

# Main

def init():
  mixer.init()
  set_as_leds()
  reset_leds()
  start_button = Button(NUM_IO + 1)
  start_button.wait_for_press()
  mixer.Sound(SOUNDS_PATH + '/instructions.wav')
  sleep(30)

def loop():
  if level == 1:
    generate_sequence()
  play_sequence()
  get_player_sequence()

def complete():
  activate_leds()
  if strikes < 3: 
    mixer.Sound(SOUNDS_PATH + '/on_success.wav')
  else:
    mixer.Sound(SOUNDS_PATH + '/on_failure.wav')
  sleep(10)

if __name__ == '__main__':
  try:
    print('Initializing ...')
    init()
    print('SimonSays game is now active!')
    while level <= MAX_LEVEL and strikes < 3:
      print('Score: {}, Strikes: {}'.format(score, strikes))
      loop()
    print('SimonSays game completed!')
    complete()
  except KeyboardInterrupt:
    print('Keyboard interupt detected! Closing ...')
  finally:
    mixer.quit()
    clean_up()

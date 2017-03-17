#!/usr/bin/python

#----------------------------------------------------------------------

from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
import json
import commands
import pygame
import sys
from time import time, strftime

#----------------------------------------------------------------------

# RADIO_CONFIG_FILE = '/home/pi/radio/radio.cfg'
RADIO_CONFIG_FILE = '/tmp/radio.cfg'
KEY_STATION = 'station'
KEY_VOLUME = 'volume'
KEY_DEBUG = 'debug'
KEY_USE_LCD = 'use_lcd'
FLAG_SELECT = 1
FLAG_LEFT = 2
FLAG_RIGHT = 4
FLAG_UP = 8
FLAG_DOWN = 16
FILE_READONLY = 'r'
FILE_WRITE = 'w'
CMD_MPC_LSPLAYLISTS = 'mpc lsplaylists'
CMD_MPC_STOP = 'mpc stop'
CMD_MPC_PLAY = 'mpc play'
CMD_MPC_CLEAR = 'mpc clear'
CMD_MPC_LOAD = 'mpc load'
CMD_MPC_VOLUME = 'mpc volume'
CMD_MPC_CURRENT = 'mpc current'
CMD_HOSTNAME = 'hostname -I'
CMD_SHUTDOWN = 'sudo shutdown -h now'
PYGAME_CAPTION = 'Internet Radio'
PYGAME_WIDTH = 500
PYGAME_HEIGHT = 100
FONT_MONOSPACE = 'monospace'
FONT_MONOSPACE_SIZE = 16
SHUTDOWN_COUNTDOWN = 5
STR_NEWLINE = '\n'
STR_NO_STATION = ''
STR_SPACE = ' '
STR_WELCOME = 'Welcome'
STR_WELCOME_2 = ''
STR_SHUTDOWN_IN = 'Shutdown in'
STR_SHUTTING_DOWN = 'Shutting down'
STR_SEE_YOU_LATER = 'See you later!'
STR_MPC_FIX = 'mpc fix'
FORMAT_TIME = '%H:%M:%S %d/%m'
FORMAT_SHUTDOWN_TIME = '{:.1f}'
COLS = 16
ROWS = 2

data = {
  KEY_USE_LCD: True,
  KEY_DEBUG: False
}

scroller_time = time()
last_input_time = time()
backlight = Adafruit_CharLCDPlate.ON

#----------------------------------------------------------------------

def read_data():
  global data
  try:
    with open(RADIO_CONFIG_FILE, FILE_READONLY) as infile:
      data = json.load(infile)
  except:
    pass

#----------------------------------------------------------------------

def write_data():
  with open(RADIO_CONFIG_FILE, FILE_WRITE) as outfile:
    outfile.write(json.dumps(data, indent=4))
    outfile.write(STR_NEWLINE)

#----------------------------------------------------------------------

def get_data(prop, defval=False):
  return data[prop] if prop in data else defval

#----------------------------------------------------------------------

def set_data(prop, val):
  if prop in data and data[prop] == val:
    return
  data[prop] = val
  write_data()

#----------------------------------------------------------------------

def scroller(text):
  if len(text) <= COLS:
    return (text + STR_SPACE*COLS)[0:COLS]
  scroller_text = text + STR_SPACE
  skip = int(((time() - scroller_time)) * 2.0) % len(scroller_text)
  scroller_text = (scroller_text + scroller_text)[skip:skip+COLS]
  return scroller_text

#----------------------------------------------------------------------

def get_station():
  return get_data(KEY_STATION, STR_NO_STATION)

#----------------------------------------------------------------------

def set_station(station):
  set_data(KEY_STATION, station)

#----------------------------------------------------------------------

def get_volume(defval=100):
  station = get_station()
  if station == STR_NO_STATION:
    return defval
  if not KEY_VOLUME in data:
    return defval
  if not station in data[KEY_VOLUME]:
    return defval
  return data[KEY_VOLUME][station]

#----------------------------------------------------------------------

def set_volume(val):
  station = get_station()
  if station == STR_NO_STATION:
    return
  if not KEY_VOLUME in data:
    data[KEY_VOLUME] = { }
  if station in data[KEY_VOLUME]:
    if data[KEY_VOLUME][station] == val:
      return
  data[KEY_VOLUME][station] = val
  write_data()

#----------------------------------------------------------------------

def get_debug():
  return get_data(KEY_DEBUG)

#----------------------------------------------------------------------

def get_use_lcd():
  return get_data(KEY_USE_LCD)

#----------------------------------------------------------------------

def shell_command(cmd):
  try:
    return commands.getstatusoutput(cmd)[1].rstrip().split(STR_NEWLINE)
  except:
    return [ ]

#----------------------------------------------------------------------

def mpc_clear():
  shell_command(CMD_MPC_CLEAR)

#----------------------------------------------------------------------

def mpc_stop():
  shell_command(CMD_MPC_STOP)

#----------------------------------------------------------------------

def mpc_play():
  shell_command(CMD_MPC_PLAY)

#----------------------------------------------------------------------

def mpc_load(station):
  shell_command(CMD_MPC_LOAD + STR_SPACE + station)

#----------------------------------------------------------------------

def mpc_volume(vol):
  shell_command(CMD_MPC_VOLUME + STR_SPACE + str(vol))

#----------------------------------------------------------------------

def mpc_current():
  return STR_SPACE.join(shell_command(CMD_MPC_CURRENT))

#----------------------------------------------------------------------

def mpc_lsplaylists():
  return shell_command(CMD_MPC_LSPLAYLISTS)

#----------------------------------------------------------------------

def debug_init():
  pygame.init()
  global screen, font
  screen = pygame.display.set_mode((PYGAME_WIDTH, PYGAME_HEIGHT))
  font = pygame.font.SysFont(FONT_MONOSPACE, FONT_MONOSPACE_SIZE)
  pygame.display.set_caption(PYGAME_CAPTION)

#----------------------------------------------------------------------

def debug_write_lines(lines):
  global screen, font
  if backlight == Adafruit_CharLCDPlate.ON:
    screen.fill((64, 64, 64))
  elif backlight == Adafruit_CharLCDPlate.RED:
    screen.fill((64, 0, 0))
  else:
    screen.fill((0, 0, 0))
  i = 0
  while (i < len(lines)):
    line = font.render(lines[i], 2, (255, 255, 0))
    screen.blit(line, (0, FONT_MONOSPACE_SIZE * i))
    i = i + 1
  pygame.display.flip()

#----------------------------------------------------------------------

def lcd_init():
  global lcd
  try:
    lcd = Adafruit_CharLCDPlate()
    lcd.begin(COLS, ROWS)
    lcd.clear()
  except:
    set_data(KEY_USE_LCD, False)

#----------------------------------------------------------------------

def lcd_write_lines(lines):
  lcd.home()
  i = 0
  while (i < len(lines)):
    lcd.message(lines[i])
    i = i + 1

#----------------------------------------------------------------------

def write_lines(lines):
  if get_debug():
    debug_write_lines(lines)
  if get_use_lcd():
    lcd_write_lines(lines)

#----------------------------------------------------------------------

def debug_get_input():
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      pygame.quit()
      sys.exit()
  pressed = pygame.key.get_pressed()
  if pressed[pygame.K_q] == 1:
    sys.exit()
  res = 0
  if pressed[pygame.K_SPACE] == 1:
    res |= FLAG_SELECT
  if pressed[pygame.K_RETURN] == 1:
    res |= FLAG_SELECT
  if pressed[pygame.K_LEFT] == 1:
    res |= FLAG_LEFT
  if pressed[pygame.K_RIGHT] == 1:
    res |= FLAG_RIGHT
  if pressed[pygame.K_UP] == 1:
    res |= FLAG_UP
  if pressed[pygame.K_DOWN] == 1:
    res |= FLAG_DOWN
  return res

#----------------------------------------------------------------------

def lcd_get_input():
  res = 0
  if lcd.buttonPressed(lcd.SELECT):
    res |= FLAG_SELECT
  if lcd.buttonPressed(lcd.LEFT):
    res |= FLAG_LEFT
  if lcd.buttonPressed(lcd.RIGHT):
    res |= FLAG_RIGHT
  if lcd.buttonPressed(lcd.UP):
    res |= FLAG_UP
  if lcd.buttonPressed(lcd.DOWN):
    res |= FLAG_DOWN
  return res

#----------------------------------------------------------------------

def get_input():
  res = 0
  if get_debug():
    res |= debug_get_input()
  if get_use_lcd():
    res |= lcd_get_input()
  return res

#----------------------------------------------------------------------

def get_next_station(dir = 1):
  stations = sorted(mpc_lsplaylists())
  count = len(stations)
  if count == 0:
    return STR_NO_STATION
  try:
    station = get_data(KEY_STATION, STR_NO_STATION)
    index = stations.index(station)
    return stations[(index + count + dir) % count]
  except:
    return stations[0]

#----------------------------------------------------------------------

def get_shutdown_text():
  return STR_SHUTDOWN_IN + STR_SPACE + FORMAT_SHUTDOWN_TIME.format(shutdown_time - time())

#----------------------------------------------------------------------
 
def play_station(station):
  set_station(station)
  volume = get_volume()
  mpc_stop()
  mpc_clear()
  mpc_load(station)
  mpc_play()
  mpc_volume(volume)

#----------------------------------------------------------------------
 
def play_next_station(dir = 1):
  station = get_next_station(dir)
  if station == STR_NO_STATION:
    return
  play_station(station)
  print get_station(), get_volume()

#----------------------------------------------------------------------

def adjust_volume(dir = 5):
  volume = get_volume() + dir
  if volume < 0:
    volume = 0
  if volume > 100:
    volume = 100
  set_volume(volume)
  mpc_volume(volume)
  print get_station(), get_volume()

#----------------------------------------------------------------------

def radio_fix():
  print STR_MPC_FIX
  mpc_stop()
  mpc_play()

#----------------------------------------------------------------------

def lcd_set_backlight(color):
  lcd.backlight(color)

def set_backlight(color):
  global backlight
  if backlight == color:
    return
  if get_use_lcd():
    lcd_set_backlight(color)
  backlight = color

#----------------------------------------------------------------------

def cancel_idle():
  global last_input_time
  last_input_time = time()
  set_backlight(Adafruit_CharLCDPlate.ON)

#----------------------------------------------------------------------

def start_idle():
  set_backlight(Adafruit_CharLCDPlate.OFF)

#----------------------------------------------------------------------

def shutdown_now():
  write_lines( [
    scroller(STR_SHUTTING_DOWN),
    scroller(STR_SEE_YOU_LATER)
  ] );
  set_backlight(Adafruit_CharLCDPlate.OFF)
  shell_command(CMD_SHUTDOWN)
  sys.exit()

#----------------------------------------------------------------------

read_data()
write_data()
if get_use_lcd():
  lcd_init()
if not get_use_lcd():
  set_data(KEY_DEBUG, True)
if get_debug():
  debug_init()
write_lines( [
  scroller(STR_WELCOME),
  scroller(STR_WELCOME_2)
] )
input = 0
write_lines_time = 0
shutdown_time = 0
play_next_station(0)
while True:
  lastinput = input
  input = get_input()
  if input & FLAG_LEFT:
    cancel_idle()
    if not (lastinput & FLAG_LEFT):
      play_next_station(-1)
      scroller_time = time()
      write_lines_time = 0
  elif input & FLAG_RIGHT:
    cancel_idle()
    if not (lastinput & FLAG_RIGHT):
      play_next_station(1)
      scroller_time = time()
      write_lines_time = 0
  elif input & FLAG_UP:
    cancel_idle()
    if not (lastinput & FLAG_UP):
      adjust_volume(5)
      write_lines_time = 0
  elif input & FLAG_DOWN:
    cancel_idle()
    if not (lastinput & FLAG_DOWN):
      adjust_volume(-5)
      write_lines_time = 0
  elif input & FLAG_SELECT:
    cancel_idle()
    if not (lastinput & FLAG_SELECT):
      radio_fix()
      shutdown_time = time() + SHUTDOWN_COUNTDOWN
    if time() > shutdown_time:
      shutdown_now()
    write_lines( [
      scroller(get_shutdown_text()),
      scroller(STR_SPACE.join(shell_command(CMD_HOSTNAME)))
    ] )
    write_lines_time = 0
  else:
    if lastinput & FLAG_SELECT:
      write_lines_time = 0
    if time() > last_input_time + 5.0:
      if backlight != Adafruit_CharLCDPlate.OFF:
        start_idle()
    if time() >= write_lines_time:
      write_lines_time = time() + 0.5
      write_lines( [
        scroller(get_station() + STR_SPACE + str(get_volume())),
        scroller(strftime(FORMAT_TIME) + STR_SPACE + mpc_current())
      ] )


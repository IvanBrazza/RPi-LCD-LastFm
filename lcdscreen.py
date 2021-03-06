#!/usr/bin/env python
 
######################################################################## 
# 
# LCD4: Learning how to control an LCD module from Pi 
# 
# Author: Bruce E. Hall <bhall66@gmail.com> 
# Date : 12 Mar 2013 
# 
# See w8bh.net for more information. 
# 
######################################################################## 

import time                   #for timing delays
import RPi.GPIO as GPIO       #to access RPi GPIO
import pylast                 #to access the Last.fm API
import os.path                #to check preferences
import json                   #to read/write preferences
import multiprocessing as mp  #to create processes for scrolling text
import unicodedata            #to convert unicode strings to ASCII

#OUTPUTS: map GPIO to LCD lines
LCD_RS          = 7           #GPIO7 = Pi pin 26
LCD_E           = 8           #GPIO8 = Pi pin 24
LCD_D4          = 17          #GPIO17 = Pi pin 11
LCD_D5          = 18          #GPIO18 = Pi pin 12
LCD_D6          = 27          #GPIO21 = Pi pin 13
LCD_D7          = 22          #GPIO22 = Pi pin 15
OUTPUTS         = [LCD_RS,LCD_E,LCD_D4,LCD_D5,LCD_D6,LCD_D7]

#INPUTS: map GPIO to Switches
SW1             = 4           #GPIO4 = Pi pin 7
SW2             = 23          #GPIO16 = Pi pin 16
SW3             = 10          #GPIO10 = Pi pin 19
SW4             = 9           #GPIO9 = Pi pin 21
INPUTS          = [SW1,SW2,SW3,SW4]

#HD44780 Controller Commands
CLEARDISPLAY    = 0x01
RETURNHOME      = 0x02
RIGHTTOLEFT     = 0x04
LEFTTORIGHT     = 0x06
DISPLAYOFF      = 0x08
CURSOROFF       = 0x0C
CURSORON        = 0x0E
CURSORBLINK     = 0x0F
CURSORLEFT      = 0x10
CURSORRIGHT     = 0x14
LOADSYMBOL      = 0x40
SETCURSOR       = 0x80

#Line Addresses.
LINE = [0x00,0x40,0x14,0x54]  #for 20x4 display

musicNote = [
[ 0x07, 0x04, 0x04, 0x04, 0x04, 0x0C, 0x1C, 0x08 ],
[ 0x1E, 0x02, 0x02, 0x02, 0x06, 0x0E, 0x04, 0x00 ]
]

digits = [
[ 0x07, 0x07, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00 ], #0x00 - 3x3 square
[ 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C ], #0x01 - left vertical bar
[ 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07 ], #0x02 - right vertical bar
[ 0x1F, 0x1F, 0x1F, 0x00, 0x00, 0x00, 0x00, 0x00 ], #0x03 - horizontal bar
[ 0x1F, 0x1F, 0x1F, 0x07, 0x07, 0x07, 0x07, 0x07 ], #0x04 - right hook
[ 0x1F, 0x1F, 0x1F, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C ], #0x05 - left hook
[ 0x00, 0x00, 0x00, 0x18, 0x18, 0x18, 0x00, 0x00 ]  #0x06 - colon
]

bigDigit = [
[ 0x05, 0x04, 0x01, 0x02, 0x03, 0x03 ], #0
[ 0x00, 0x01, 0x20, 0x01, 0x00, 0x03 ], #1
[ 0x03, 0x04, 0x05, 0x03, 0x03, 0x03 ], #2
[ 0x03, 0x04, 0x03, 0x04, 0x03, 0x03 ], #3
[ 0x01, 0x02, 0x03, 0x04, 0x20, 0x00 ], #4
[ 0x05, 0x03, 0x03, 0x04, 0x03, 0x03 ], #5
[ 0x05, 0x03, 0x05, 0x04, 0x03, 0x03 ], #6
[ 0x03, 0x04, 0x20, 0x02, 0x20, 0x00 ], #7
[ 0x05, 0x04, 0x05, 0x04, 0x03, 0x03 ], #8
[ 0x05, 0x04, 0x03, 0x04, 0x20, 0x00 ], #9
[ 0x06, 0x06, 0x20, 0x20, 0x20, 0x20 ]  #colon
]

######################################################################## 
# 
# Low-level routines for configuring the LCD module. 
# These routines contain GPIO read/write calls. 
# 
 
def InitIO(): 
  #Sets GPIO pins to input & output, as required by LCD board 
  GPIO.setmode(GPIO.BCM) 
  GPIO.setwarnings(False) 
  for lcdLine in OUTPUTS: 
    GPIO.setup(lcdLine, GPIO.OUT) 
  for switch in INPUTS: 
    GPIO.setup(switch, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
 
def CheckSwitches(): 
  #Check status of all four switches on the LCD board
  #Returns four boolean values as a tuple.
  val1 = not GPIO.input(SW1) 
  val2 = not GPIO.input(SW2) 
  val3 = not GPIO.input(SW3) 
  val4 = not GPIO.input(SW4) 
  return (val4,val1,val2,val3) 
 
def PulseEnableLine(): 
  #Pulse the LCD Enable line; used for clocking in data 
  GPIO.output(LCD_E, GPIO.HIGH) #pulse E high 
  GPIO.output(LCD_E, GPIO.LOW)  #return E low 
 
def SendNibble(data): 
  #sends upper 4 bits of data byte to LCD data pins D4-D7 
  GPIO.output(LCD_D4, bool(data & 0x10)) 
  GPIO.output(LCD_D5, bool(data & 0x20)) 
  GPIO.output(LCD_D6, bool(data & 0x40)) 
  GPIO.output(LCD_D7, bool(data & 0x80)) 
 
def SendByte(data,charMode=False): 
  #send one byte to LCD controller 
  GPIO.output(LCD_RS,charMode)  #set mode: command vs. char 
  SendNibble(data)              #send upper bits first 
  PulseEnableLine()             #pulse the enable line 
  data = (data & 0x0F)<< 4      #shift 4 bits to left 
  SendNibble(data)              #send lower bits now 
  PulseEnableLine()             #pulse the enable line 
 
 
######################################################################## 
# 
# Higher-level routines for diplaying data on the LCD. 
# 
 
def ClearDisplay(): 
  #This command requires 1.5mS processing time, so delay is needed 
  SendByte(CLEARDISPLAY) 
  time.sleep(0.0015) #delay for 1.5mS 
 
def CursorOn(): 
  SendByte(CURSORON) 
 
def CursorOff(): 
  SendByte(CURSOROFF) 
 
def CursorBlink(): 
  SendByte(CURSORBLINK) 
 
def CursorLeft(): 
  SendByte(CURSORLEFT) 
 
def CursorRight(): 
  SendByte(CURSORRIGHT) 
 
def InitLCD(): 
  #initialize the LCD controller & clear display 
  SendByte(0x33)        #initialize 
  SendByte(0x32)        #initialize/4-bit 
  SendByte(0x28)        #4-bit, 2 lines, 5x8 font 
  SendByte(LEFTTORIGHT) #rightward moving cursor 
  CursorOff() 
  ClearDisplay() 

def SendChar(ch): 
  SendByte(ord(ch),True) 

def ShowMessage(string):
  #Send string of characters to display at current cursor position 
  for character in string: 
    SendChar(character)

def ScrollMessage(string, line):
  #scroll text on specified line at ~3 characters/second
  #should be spawned as a separate process (see multiprocessing)
  end = 20
  for start in range(0, len(string) + 1):
    GotoLine(line)
    message = string[start:end].ljust(20)
    for character in message:
      SendChar(character)
    time.sleep(0.3)
    end += 1
  pad     = " " * 20
  newstr  = pad + string
  while True:
    end = 20
    for start in range(0, len(newstr) + 1):
      GotoLine(line)
      message = newstr[start:end].ljust(20)
      for character in message:
        SendChar(character)
      if start == 20:
        time.sleep(2)
      else:
        time.sleep(0.3)
      end += 1

def GotoLine(row): 
  #Moves cursor to the given row 
  #Expects row values 0-1 for 16x2 display; 0-3 for 20x4 display 
  addr = LINE[row] 
  SendByte(SETCURSOR+addr) 
 
def GotoXY(row,col): 
  #Moves cursor to the given row & column 
  #Expects col values 0-19 and row values 0-3 for a 20x4 display 
  addr = LINE[row] + col 
  SendByte(SETCURSOR + addr) 
 
 
######################################################################## 
# 
# BIG CLOCK & Custom character generation routines 
# 
 
def LoadCustomSymbol(addr,data): 
  #saves custom character data at given char-gen address 
  #data is a list of 8 bytes that specify the 5x8 character 
  #each byte contains 5 column bits (b5,b4,..b0) 
  #each byte corresponds to a horizontal row of the character 
  #possible address values are 0-7 
  cmd = LOADSYMBOL + (addr<<3) 
  SendByte(cmd) 
  for byte in data: 
    SendByte(byte,True) 
 
def LoadSymbolBlock(data): 
  #loads a list of symbols into the chargen RAM, starting at addr 0x00 
  for i in range(len(data)): 
    LoadCustomSymbol(i,data[i]) 
 
def ShowBigDigit(symbol,startCol): 
  #displays a 4-row-high digit at specified column 
  for row in range(3):
    GotoXY(row,startCol)
    for col in range(2):
      index = row*2 + col
      SendByte(symbol[index],True)
 
def ShowColon():
  #displays a 2-char high colon ':' at specified column
  for row in range(3):
    GotoXY(row, 6)
    for col in range(1):
      index = row*1 + col
      SendByte(bigDigit[10][index],True)

def HideColon():
  GotoXY(0, 6)
  ShowMessage(" ")
  GotoXY(1, 6)
  ShowMessage(" ")
 
def BigClock(): 
  #displays large-digit time in hh:mm:ss on 20x4 LCD 
  #continuous display (this routine does not end!) 
  LoadSymbolBlock(digits)
  posn = [0,3,7,10]
  ClearDisplay() 
  while (True): 
    switchValues = CheckSwitches()
    if switchValues[0] == 1:
      #re-init display if the first button is pressed
      InitIO()
      InitLCD()
      LoadSymbolBlock(digits)
    try:
      #check if scrobbling
      result = user.get_now_playing()
      if result:
        NowScrobbling(result)
        LoadSymbolBlock(digits)
    except:
      time.sleep(0)
    tStr = time.strftime("%I%M")
    for i in range(len(tStr)): 
      value = int(tStr[i]) 
      symbols = bigDigit[value] 
      ShowBigDigit(symbols,posn[i]) 
    ShowColon()
    GotoXY(0,13)
    ShowMessage(time.strftime("%p"))
    GotoLine(3)
    ShowMessage(time.strftime("%a %b %d %Y"))
    time.sleep(1)
    HideColon()
    time.sleep(1)

#######################################################################
#
# Custom Functions
#

def CheckConfig():
  #check if config file exists. If it doesn't, create it
  if os.path.isfile("lastconfig.json"):
    return
  else:
    CreateConfig()

def CreateConfig():
  #display message on LCD and console that we're creating a config
  GotoXY(0,0)
  ShowMessage("Creating config...")
  print "A configuration was not found. Let's create one."

  #get config details
  KEY       = raw_input("Enter your Last.fm API key: ")
  SECRET    = raw_input("Enter your Last.fm API secret: ")
  username  = raw_input("Enter your Last.fm username: ")
  password  = pylast.md5(raw_input("Enter your Last.fm password: "))
  towrite   = {'API_KEY': KEY, 'API_SECRET': SECRET, 'username': username, 'password': password}

  #write config to file
  with open('lastconfig.json', 'w') as outfile:
    json.dump(towrite, outfile, indent=4)

def InitLast():
  global user

  #read config file
  with open('lastconfig.json') as infile:
    config    = json.load(infile)

  #init pylast
  API_KEY     = config['API_KEY']
  API_SECRET  = config['API_SECRET']
  username    = config['username']
  password    = config['password']
  network     = pylast.LastFMNetwork(api_key = API_KEY, api_secret = API_SECRET, username = username, password_hash = password)
  user        = network.get_user("dudeman1996")

def NowScrobbling(result):
  #get track details and display them
  artist  = unicodedata.normalize('NFKD', result.artist.get_name()).encode('ascii','ignore')
  try:
    album = unicodedata.normalize('NFKD', result.get_album().get_name()).encode('ascii','ignore')
  except:
    album = " "
  title   = unicodedata.normalize('NFKD', result.get_title()).encode('ascii','ignore')
  DisplayNowScrobbling(artist, album, title)

  while (True):
    switchValues = CheckSwitches()
    if switchValues[0] == 1:
      #re-init display if first button is pressed
      InitIO()
      InitLCD()
      DisplayNowScrobbling(artist, album, title)
    try:
      #check if track has changed
      result    = user.get_now_playing()
      newartist = str(result.artist.get_name())
      try:
        newalbum  = str(result.get_album().get_name())
      except:
        newalbum = " "
      newtitle  = str(result.get_title())
      if newtitle != title:
        title   = newtitle
        artist  = newartist
        album   = newalbum
        for Process in Processes:
          Process.terminate() #kill any scrolling processes
        DisplayNowScrobbling(artist, album, title)
      time.sleep(2)
    except:
      #nothing is playing, kill scrolling processes and return to clock
      for Process in Processes:
        Process.terminate()
      ClearDisplay()
      return

def DisplayNowScrobbling(artist, album, title):
  global Processes
  Processes = []

  ClearDisplay()

  #display "Now Scrobbling:" and show music note
  GotoLine(0)
  ShowMessage("Now Scrobbling:")
  LoadSymbolBlock(musicNote)
  GotoXY(0,18)
  for count in range(len(musicNote)):
    SendByte(count,True)

  #scroll artist name if > 20 characters, otherwise display it
  if len(artist) > 20:
    #spawn process to scroll artist
    ArtistProcess = mp.Process(target=ScrollMessage, args=[artist, 1])
    ArtistProcess.start()
    Processes.append(ArtistProcess)
    time.sleep(0.2) #needed for the display to process
  else:
    GotoLine(1)
    ShowMessage(artist)

  #scroll album name if > 20 characters, otherwise display it
  if len(album) > 20:
    #spawn process to scroll album
    AlbumProcess = mp.Process(target=ScrollMessage, args=[album, 2])
    AlbumProcess.start()
    Processes.append(AlbumProcess)
    time.sleep(0.2) #needed for the display to process
  else:
    GotoLine(2)
    ShowMessage(album)

  #scroll title name if > 20 characters, otherwise display it
  if len(title) > 20:
    #spawn process to scroll title
    TitleProcess = mp.Process(target=ScrollMessage, args=[title, 3])
    TitleProcess.start()
    Processes.append(TitleProcess)
    time.sleep(0.2) #needed for the display to process
  else:
    GotoLine(3)
    ShowMessage(title)

######################################################################## 
# 
# Main Program 
# 

print "Pi LCD4 program starting."
InitIO() #Initialization 
InitLCD() 
CheckConfig()
InitLast()
BigClock() #Something actually useful 
 
# END #############################################################

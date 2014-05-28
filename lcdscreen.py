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

import time #for timing delays
import RPi.GPIO as GPIO
import random
import pylast

xbmc = 0

#OUTPUTS: map GPIO to LCD lines
LCD_RS          = 7 #GPIO7 = Pi pin 26
LCD_E           = 8 #GPIO8 = Pi pin 24
LCD_D4          = 17 #GPIO17 = Pi pin 11
LCD_D5          = 18 #GPIO18 = Pi pin 12
LCD_D6          = 27 #GPIO21 = Pi pin 13
LCD_D7          = 22 #GPIO22 = Pi pin 15
OUTPUTS         = [LCD_RS,LCD_E,LCD_D4,LCD_D5,LCD_D6,LCD_D7]

#INPUTS: map GPIO to Switches
SW1             = 4 #GPIO4 = Pi pin 7
SW2             = 23 #GPIO16 = Pi pin 16
SW3             = 10 #GPIO10 = Pi pin 19
SW4             = 9 #GPIO9 = Pi pin 21
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
LINE = [0x00,0x40,0x14,0x54] #for 20x4 display

musicNote = [
[ 0x7,  0x7,  0x4, 0x4, 0x4, 0x1C, 0x1C, 0x1C ],
[ 0x1e, 0x1e, 0x2, 0x2, 0xE, 0xE,  0xE,  0x0  ]
]

weather = [
[ 0xC, 0x12, 0x12, 0xC, 0x0, 0x0, 0x0, 0x0 ], #degree
[ 0x0, 0x0,  0x0,  0xE, 0x0, 0x0, 0x0, 0x0 ]  #hyphen
]

patterns = [
[ 0x15, 0x0A, 0x15, 0x0A, 0x15, 0x0A, 0x15, 0x0A ], #50%
[ 0x0A, 0x15, 0x0A, 0x15, 0x0A, 0x15, 0x0A, 0x15 ], #alt 50%
[ 0x15, 0x15, 0x15, 0x15, 0x15, 0x15, 0x15, 0x15 ], #3 vbars
[ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ],
[ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ],
[ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ],
[ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ],
]

verticalBars = [
[ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F ], #1 bar
[ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F ], #2 bars
[ 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F ], #3 bars
[ 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F ], #4 bars
[ 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F ], #5 bars
[ 0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F ], #6 bars
[ 0x00, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F ], #7 bars
[ 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F ], #8 bars
]

horizontalBars = [
[ 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10 ], #1 bar
[ 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18 ], #2 bars
[ 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C, 0x1C ], #3 bars
[ 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E ], #4 bars
[ 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F ], #5 bars
[ 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F ], #4 bars
[ 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07, 0x07 ], #3 bars
[ 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03, 0x03 ], #2 bars
]

digits = [
[ 0x01, 0x03, 0x03, 0x07, 0x07, 0x0F, 0x0F, 0x1F ], #lower-rt triangle
[ 0x10, 0x18, 0x18, 0x1C, 0x1C, 0x1E, 0x1E, 0x1F ], #lower-lf triangle
[ 0x1F, 0x0F, 0x0F, 0x07, 0x07, 0x03, 0x03, 0x01 ], #upper-rt triangle
[ 0x1F, 0x1E, 0x1E, 0x1C, 0x1C, 0x18, 0x18, 0x10 ], #upper-lf triangle
[ 0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F ], #lower horiz bar
[ 0x1F, 0x1F, 0x1F, 0x1F, 0x00, 0x00, 0x00, 0x00 ], #upper horiz bar
[ 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F ]  #solid block
]

bigDigit = [
[ 0x00, 0x06, 0x01, 0x06, 0x20, 0x06, 0x06, 0x20, 0x06, 0x02, 0x06, 0x03], #0
[ 0x20, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06, 0x20], #1
[ 0x00, 0x06, 0x01, 0x20, 0x00, 0x03, 0x00, 0x03, 0x20, 0x06, 0x06, 0x06], #2
[ 0x00, 0x06, 0x01, 0x20, 0x20, 0x06, 0x20, 0x05, 0x06, 0x02, 0x06, 0x03], #3
[ 0x06, 0x20, 0x06, 0x06, 0x06, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06], #4
[ 0x06, 0x06, 0x06, 0x06, 0x04, 0x04, 0x20, 0x20, 0x06, 0x06, 0x06, 0x03], #5
[ 0x00, 0x06, 0x01, 0x06, 0x20, 0x20, 0x06, 0x05, 0x01, 0x02, 0x06, 0x03], #6
[ 0x06, 0x06, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06], #7
[ 0x00, 0x06, 0x01, 0x06, 0x04, 0x06, 0x06, 0x05, 0x06, 0x02, 0x06, 0x03], #8
[ 0x00, 0x06, 0x01, 0x02, 0x04, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06]  #9
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
  GPIO.output(LCD_E, GPIO.LOW) #return E low 
 
def SendNibble(data): 
  #sends upper 4 bits of data byte to LCD data pins D4-D7 
  GPIO.output(LCD_D4, bool(data & 0x10)) 
  GPIO.output(LCD_D5, bool(data & 0x20)) 
  GPIO.output(LCD_D6, bool(data & 0x40)) 
  GPIO.output(LCD_D7, bool(data & 0x80)) 
 
def SendByte(data,charMode=False): 
  #send one byte to LCD controller 
  GPIO.output(LCD_RS,charMode) #set mode: command vs. char 
  SendNibble(data) #send upper bits first 
  PulseEnableLine() #pulse the enable line 
  data = (data & 0x0F)<< 4 #shift 4 bits to left 
  SendNibble(data) #send lower bits now 
  PulseEnableLine() #pulse the enable line 
 
 
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
  SendByte(0x33) #initialize 
  SendByte(0x32) #initialize/4-bit 
  SendByte(0x28) #4-bit, 2 lines, 5x8 font 
  SendByte(LEFTTORIGHT) #rightward moving cursor 
  CursorOff() 
  ClearDisplay() 

def SendChar(ch): 
  SendByte(ord(ch),True) 

def ShowMessage(string):
  #Send string of characters to display at current cursor position 
  for character in string: 
    SendChar(character)

def ShowMessageWrap(string, LineNumber): 
  #Send string of characters to display at current cursor position 
  WordWrap = False
  while WordWrap == False:
    if LineNumber == 4:
      return
    if len(string) > 20:
      if string[0:1] == " ":
        message = string[1:21]
        string  = string[21:]
      else:
        message = string[:20]
        string  = string[20:]
      GotoLine(LineNumber)
      LineNumber += 1
      for character in message: 
        SendChar(character) 
    else:
      if string[0:1] == " ":
        message = string[1:]
      else:
        message = string
      GotoLine(LineNumber)
      LineNumber += 1
      for character in message:
        SendChar(character)
      WordWrap = True
 
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
  for row in range(4): 
    GotoXY(row,startCol) 
    for col in range(3): 
      index = row*3 + col 
      SendByte(symbol[index],True) 
 
def ShowColon(col): 
  #displays a 2-char high colon ':' at specified column 
  dot = chr(0xA1) 
  GotoXY(1,col) 
  SendChar(dot) 
  GotoXY(2,col) 
  SendChar(dot) 
 
def BigClock(): 
  #displays large-digit time in hh:mm:ss on 20x4 LCD 
  #continuous display (this routine does not end!) 
  LoadSymbolBlock(digits)
  posn = [0,3,7,10]
  ClearDisplay() 
  while (True): 
    try:
      result = user.get_now_playing()
      if result:
        NowPlaying(result)
        time.sleep(1)
        LoadSymbolBlock(digits)
    except:
      time.sleep(0)
    tStr = time.strftime("%I%M")
    for i in range(len(tStr)): 
      ShowColon(6) 
      value = int(tStr[i]) 
      symbols = bigDigit[value] 
      ShowBigDigit(symbols,posn[i]) 
    GotoXY(0,13)
    ShowMessage(time.strftime("%p"))
    GotoXY(1,17)
    ShowMessage(time.strftime("%a"))
    GotoXY(2,14)
    ShowMessage(time.strftime("%b %d"))
    GotoXY(3,16)
    ShowMessage(time.strftime("%Y"))
    time.sleep(1) 
    GotoXY(1,6)
    ShowMessage(" ")
    GotoXY(2,6)
    ShowMessage(" ")
    time.sleep(1)

#######################################################################
#
# Custom Functions
#

def InitLast():
  global user
  API_KEY     = "32aa388ab9f750aa2732c18540c0f3b0"
  API_SECRET  = "8693c56d42e2a92b7b4c149200d75f55"
  username    = "dudeman1996"
  password    = pylast.md5("inspiron1520")
  network     = pylast.LastFMNetwork(api_key = API_KEY, api_secret = API_SECRET, username = username, password_hash = password)
  user        = network.get_user("dudeman1996")

def NowPlaying(result):
  artist = str(result.artist.get_name())
  title  = str(result.get_title())
  DisplayNowPlaying(artist, title)
  while (True):
    try:
      result = user.get_now_playing()
      newartist = str(result.artist.get_name())
      newtitle  = str(result.get_title())
      if newtitle != title:
        artist = newartist
        title = newtitle
        DisplayNowPlaying(artist, title)
      time.sleep(2)
    except:
      ClearDisplay()
      return

def DisplayNowPlaying(artist, title):
  ClearDisplay()
  GotoLine(0)
  ShowMessage("Now Playing:")
  LoadSymbolBlock(musicNote)
  GotoXY(0,16)
  for count in range(len(musicNote)):
    SendByte(count,True)
  GotoLine(1)
  ShowMessage(artist[:20])
  ShowMessageWrap(title, 2)

######################################################################## 
# 
# Main Program 
# 

print "Pi LCD4 program starting."
InitIO() #Initialization 
InitLCD() 
InitLast()
BigClock() #Something actually useful 
 
# END #############################################################

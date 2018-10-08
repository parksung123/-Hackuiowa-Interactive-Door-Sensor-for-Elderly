import RPi.GPIO as GPIO
import socket, time

### socket.send status code ###
SOCKET_DETEC = "111"
SOCKET_NOT_DETEC = "110"
SOCKET_OPEN = "121"
SOCKET_CLOSED = "120"
SOCKET_CHANGE = "131"
SOCKET_NOT_CHANGE = "130"
SOCKET_LCD_REQ = "211"
### end ###

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
 
RED = 13
GREEN = 19
BLUE = 26
 
GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(BLUE, GPIO.OUT)

# next create a socket object 
s = socket.socket()          
print "Socket successfully created"

PORT = 17098                

s.bind(('', PORT))         
print "socket binded to %s" %(PORT) 

s.listen(5)      
print "socket is listening"            

c, addr = s.accept()      
print 'Got connection from', addr 

c.send('Thank you for connecting,0,0,0$') 

data = ''
char = ''
LCD_str = ''
LCD_col = '0,0,0'
LCD_SHOW_MEG = True

while True: 
  char = c.recv(1)
  if char != '\n':
    data += char
  else:
    data = ''

  if data == SOCKET_DETEC:
    print "SOCKET_DETEC"
  elif data == SOCKET_NOT_DETEC:
    print "SOCKET_NOT_DETEC"
  elif data == SOCKET_OPEN:
    GPIO.output(GREEN, GPIO.HIGH)
    GPIO.output(RED, GPIO.LOW)
    LCD_str = "DOOR IS OPEN!!" 
  elif data == SOCKET_CLOSED:
    GPIO.output(RED, GPIO.HIGH)
    GPIO.output(GREEN, GPIO.LOW)
    LCD_str = "DOOR IS CLOSED!!" 
  elif data == SOCKET_CHANGE:
    GPIO.output(BLUE, GPIO.LOW)
    LCD_SHOW_MEG = True
  elif data == SOCKET_NOT_CHANGE:
    GPIO.output(BLUE, GPIO.HIGH)
    LCD_SHOW_MEG = False
  elif data == SOCKET_LCD_REQ:

    if LCD_SHOW_MEG:
      file_msg = open("message.txt", "r") 
      file_col = open("color.txt", "r") 
      LCD_str = file_msg.read() 
      LCD_col = file_col.read() 
      file_msg.close()
      file_col.close()

    c.send(LCD_str) 
    c.send(",") 
    c.send(LCD_col) 
    c.send("$") 

c.close() 

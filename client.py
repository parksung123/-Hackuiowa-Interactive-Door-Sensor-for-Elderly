import RPi.GPIO as GPIO
import time
import socket
import grove_rgb_lcd as LCD
import smtplib 
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import requests 
import geocoder
api_address =  'http://api.openweathermap.org/data/2.5/weather?appid=105ccbc068343b1fa41d3b69d9b97b17&lat='
g = geocoder.ip('me')

my_lat = g.latlng[0]
my_lon = g.latlng[0]
url = api_address +str(my_lat) + '&lon=' +str(my_lon)

EMAIL_FROM = "hackthonakl@gmail.com"
EMAIL_TO = "ericlilhy@gmail.com"
EMAIL_FROM_ID = "hackthonakl"
EMAIL_FROM_PW = "hackhack"
EMAIL_FROM_NAME = "Your House Monitor"
EMAIL_TO_NAME = "Person who may care"
EMAIL_SUBJECT = "Important Update of The House"
EMAIL_MSG = "Be careful that the door of the house is moved"

CHANGE_TIME_THRES = 20  #sec
STATUS_MIN_THRES = 5    # Door is closed when the dis is greater than MIN and less than MAX
STATUS_MAX_THRES = 20
MOVING_DETEC = 15       # Detect a change when the change in distance is greater than this
AVE_COUNT = 5
DIS_MAX_VAL = 400

### status value ###
DOOR_CLOSED_STATUS = 1
DOOR_OPEN_STATUS = 2
### end ###

### socket.send status code ###
SOCKET_DETEC = "111\n"
SOCKET_NOT_DETEC = "110\n"
SOCKET_OPEN = "121\n"
SOCKET_CLOSED = "120\n"
SOCKET_CHANGE = "131\n"
SOCKET_NOT_CHANGE = "130\n"
SOCKET_LCD_REQ = "211\n"
### end ###

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

TRIG = 20
ECHO = 16
RED = 13
GREEN = 19
BLUE = 26

GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(BLUE, GPIO.OUT)

### socket init ###
s = socket.socket()          

PORT = 17098
IPADDR = '192.168.1.101'

s.connect((IPADDR, PORT)) 
s.settimeout(3)
### end ###

### mail init ###
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(EMAIL_FROM_ID, EMAIL_FROM_PW)
msg = MIMEMultipart()
msg['From'] = EMAIL_FROM_NAME
msg['To'] = EMAIL_TO_NAME
msg['Subject'] = EMAIL_SUBJECT
message = EMAIL_MSG
msg.attach(MIMEText(message))
### end ###

print "Distance Measurement In Progress"

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)

GPIO.output(TRIG, False)
print "Waiting For Sensor To Settle"
time.sleep(1)	

def getDistance():
  GPIO.output(TRIG, True)
  time.sleep(0.00001)
  GPIO.output(TRIG, False)

  invalid = False

  t_start = time.time()

  while GPIO.input(ECHO) == 0:
    pulse_start = time.time()
    if (time.time() - t_start) > 1:
      invalid = True
      return 0

  t_start = time.time()

  while GPIO.input(ECHO)==1:
    pulse_end = time.time() 
    if (time.time() - t_start) > 1:
      invalid = True
      return 0

  if not(('pulse_end' in locals()) and ('pulse_start' in locals())):
    return 0

  pulse_duration = pulse_end - pulse_start

  distance = pulse_duration * 17150
  distance = round(distance, 2)

  if distance > DIS_MAX_VAL:
    return DIS_MAX_VAL

  return distance

prevDistance = getDistance()
status = 0

char = ''
LCD_Data = ''
LCD_Data_Prev = ''
LCD_Prev_Time = time.time()
Prev_Time = time.time()

universalTiming = time.time()
while True: 

### LCD Display ###

  if (time.time() - LCD_Prev_Time) > 0.5:
    json_data = requests.get(url).json()
    formatted = json_data['weather'][0]['main'] 
    s.send(SOCKET_LCD_REQ)

    char = s.recv(1)
    while char != '$':
      LCD_Data += char
      char = s.recv(1)

    if LCD_Data != LCD_Data_Prev:
      server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
      LCD_Data_List = LCD_Data.split(",")
      LCD.setText(LCD_Data_List[0])
      LCD_Data_Prev = LCD_Data
      LCD.setRGB(int(LCD_Data_List[1]),int(LCD_Data_List[2]),int(LCD_Data_List[3]))
      Prev_Time = time.time()

    if (time.time() - Prev_Time) > CHANGE_TIME_THRES/2:
      LCD.setText("Weather\n" + formatted)
      #Prev_Time = time.time()

    LCD_Data = ''
    LCD_Prev_Time = time.time()


### --- LCD Display --- end ###

### Distance Measurement ###

  totalDis = 0

  for i in range(AVE_COUNT): 
    distance = getDistance()
    time.sleep(0.04)
    if distance == 0:
      i-=1

    totalDis += distance

  avgDis = totalDis / AVE_COUNT

  if avgDis <= STATUS_MAX_THRES and avgDis >= STATUS_MIN_THRES: # Door is closed when avgDis is within the range of MIN and MAX 
    if status != DOOR_CLOSED_STATUS:
      status_changed = True
      time_changed = time.time()
    status = DOOR_CLOSED_STATUS
  else:                                                         # Door is opend otherwise
    if status != DOOR_OPEN_STATUS:
      status_changed = True
      time_changed = time.time()
    status = DOOR_OPEN_STATUS

  if abs(prevDistance - avgDis) >= MOVING_DETEC: 
    print "Door moved."
    s.send(SOCKET_DETEC)
    print "Prev. Dis: ", prevDistance
    s.send("Prev. Dis: {}\n".format(prevDistance))
    print "Curr. Dis: ", avgDis
    s.send("Curr. Dis: {}\n".format(avgDis))
  else:
    print "Door is not moving"
    s.send(SOCKET_NOT_DETEC)
    print "Prev. Dis: ", prevDistance
    s.send("Prev. Dis: {}\n".format(prevDistance))
    print "Curr. Dis: ", avgDis
    s.send("Curr. Dis: {}\n".format(avgDis))

  prevDistance = avgDis

  if status == DOOR_CLOSED_STATUS:
    GPIO.output(RED, GPIO.HIGH)
    print "Door is closed."
    s.send(SOCKET_CLOSED)
    GPIO.output(GREEN, GPIO.LOW)
  elif status == DOOR_OPEN_STATUS:
    GPIO.output(GREEN, GPIO.HIGH)
    print "Door is opened."
    s.send(SOCKET_OPEN)
    GPIO.output(RED, GPIO.LOW)

  if status_changed and ((time.time() - time_changed) < CHANGE_TIME_THRES):
    GPIO.output(BLUE, GPIO.LOW)
    print "Status changed within {} seconds.".format(CHANGE_TIME_THRES)
    #server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    s.send(SOCKET_CHANGE)
  elif status_changed and ((time.time() - time_changed) >= CHANGE_TIME_THRES):
    GPIO.output(BLUE, GPIO.HIGH)
    status_changed = False
    s.send(SOCKET_NOT_CHANGE)

### --- Distance Measurement --- end ###

GPIO.cleanup();

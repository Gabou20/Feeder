from imapclient import IMAPClient, SEEN
import time
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
import os
import sys
import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD
import httplib2
import json
import html2text


DEBUG = False
MOTORON = True

# Raspberry Pi pin configuration:
lcd_rs        = 13
lcd_en        = 12
lcd_d4        = 26
lcd_d5        = 5
lcd_d6        = 21
lcd_d7        = 6
lcd_backlight = 12

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Here is our logfile
LOGFILE = "/tmp/petfeeder.log"

# Variables for checking email
GMAILHOSTNAME = 'imap.gmail.com' # Insert your mailserver here - Gmail uses 'imap.gmail.com'
MAILBOX = 'Inbox' # Insert the name of your mailbox. Gmail uses 'Inbox'
GMAILUSER = "gabriellemartinfortier20" # Insert your email username
GMAILPASSWD = "871gabrielle" # Insert your email password
NEWMAIL_OFFSET = 0
lastEmailCheck = time.time()
MAILCHECKDELAY = 30  # Don't check email too often since Gmail will complain

# GPIO pins
MOTORCONTROLPIN = 4
FEEDBUTTONPIN = 19
RESETBUTTONPIN = 16
QUANTITYBUTTONPIN = 20
GREENLED = 27
REDLED = 24

# Variables for feeding information
readyToFeed = False # not used now but for future use
feedInterval = 28800 # This translates to 8 hours in seconds
FEEDFILE="/home/pi/petfeeder/lastfeed"
cupsToFeed = 1
motorTime = cupsToFeed * 4 # It takes 27 seconds of motor turning (~1.75 rotations) to get 1 cup of feed
QUANTITYFILE = "/home/pi/petfeeder/lastquantity"
 
# Function to check email
#def checkmail():
#    global lastEmailCheck
#    global lastFeed
#    global feedInterval
    
    #if (time.time() > (lastEmailCheck + MAILCHECKDELAY)):  # Make sure that that atleast MAILCHECKDELAY time has passed
     #   lastEmailCheck = time.time()
     #  server = IMAPClient(GMAILHOSTNAME, use_uid=True, ssl=True)  # Create the server class from IMAPClient with HOSTNAME mail server
     #   server.login(GMAILUSER, GMAILPASSWD)
     #   server.select_folder(MAILBOX)
        
        # See if there are any messages with subject "When" that are unread
        #whenMessages = server.search([u'UNSEEN', u'SUBJECT', u'When'])

        # Respond to the when messages
        #if whenMessages:
         #   for msg in whenMessages:
         #       msginfo = server.fetch([msg], ['BODY[HEADER.FIELDS (FROM)]'])
         #       fromAddress = str(msginfo[msg].get('BODY[HEADER.FIELDS (FROM)]')).split('<')[1].split('>')[0]
         #       msgBody = "The last feeding was done on " + time.strftime("%b %d at %I:%M %P", time.localtime(lastFeed))

                #if (time.time() - lastFeed) > feedInterval:
                #    msgBody = msgBody + "\nReady to feed now!"
                #else:
                #    msgBody = msgBody + "\nThe next feeding can begin on " + time.strftime("%b %d at %I:%M %P", time.localtime(lastFeed + feedInterval))

                #if NUMBERTRIVIA:
                #    msgBody = msgBody + getNumberTrivia()

                #if CHUCKNORRIS:
                #    msgBody = msgBody + getChuckNorrisQuote()
                                                
                #sendemail(fromAddress, "Thanks for your feeding query", msgBody)
                #server.add_flags(whenMessages, [SEEN])


        # See if there are any messages with subject "Feed" that are unread
        #feedMessages = server.search([u'UNSEEN', u'SUBJECT', u'Feed'])
        
        # Respond to the feed messages and then exit
        #if feedMessages:
        #    for msg in feedMessages:
        #        msginfo = server.fetch([msg], ['BODY[HEADER.FIELDS (FROM)]'])
        #        fromAddress = str(msginfo[msg].get('BODY[HEADER.FIELDS (FROM)]')).split('<')[1].split('>')[0]

        #        msgBody = "The last feeding was done at " + time.strftime("%b %d at %I:%M %P", time.localtime(lastFeed))
        #        if (time.time() - lastFeed) > feedInterval:
        #            msgBody = msgBody + "\nReady to be fed, will be feeding Lucky shortly"
        #        else:
        #            msgBody = msgBody + "\nThe next feeding can begin at " + time.strftime("%b %d at %I:%M %P", time.localtime(lastFeed + feedInterval))
        #                       
        #        sendemail(fromAddress, "Thanks for your feeding request", msgBody)

        #        server.add_flags(feedMessages, [SEEN])
        #    return True

    #return False

#def sendemail(to, subject, text, attach=None):
#    msg = MIMEMultipart()
#    msg['From'] = GMAILUSER
#    msg['To'] = to
#    msg['Subject'] = subject
#    msg.attach(MIMEText(text))
#    if attach:
#        part = MIMEBase('application', 'octet-stream')
#        part.set_payload(open(attach, 'rb').read())
#        Encoders.encode_base64(part)
#        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attach))
#        msg.attach(part)
#    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
#    mailServer.ehlo()
#    mailServer.starttls()
#    mailServer.ehlo()
#    mailServer.login(GMAILUSER, GMAILPASSWD)
#    mailServer.sendmail(GMAILUSER, to, msg.as_string())
#    mailServer.close()

def buttonpressed(PIN):
    # Check if the button is pressed
    global GPIO
    
    # Cheap (sleep) way of controlling bounces / rapid presses
    time.sleep(0.05)
    button_state = GPIO.input(PIN)
    if button_state == True:
        return True
    else:
        return False

#def remotefeedrequest():
    # At this time we are only checking for email
    # Other mechanisms for input (e.g. web interface or iOS App) is a TO-DO
#    return checkmail()


def printlcd(row, col, LCDmesg):
    # Set the row and column for the LCD and print the message
    global logFile
    global lcd
    
    lcd.set_cursor(row, col)
    lcd.message(LCDmesg)

def feednow():
    # Run the motor for motorTime, messages in the LCD during the feeeding
    global GPIO
    global MOTORCONTROLPIN
    global motorTime
    global lastFeed
    global QUANTITY
    global GREENLED

    QUANTITY = QUANTITY - 11
    savequantity()
    lcd.clear()
    printlcd(0,0,"Feeding now.....")
    GPIO.output(GREENLED,GPIO.LOW)
    if MOTORON:
        GPIO.output(MOTORCONTROLPIN, True)
        time.sleep(motorTime)
        GPIO.output(MOTORCONTROLPIN, False)
        printlcd(0,1, "Done!")
#       sendemail(GMAILUSER, "Fed at " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(lastFeed)), "Feeding done!")
        time.sleep(2)
    return time.time()

def saveLastFeed():
    global FEEDFILE
    global lastFeed
    with open(FEEDFILE, 'w') as feedFile:
        feedFile.write(str(lastFeed))
    feedFile.close()

def quantityprint(quantity):
    write = '% '
    quantity = str(quantity)
    if len(quantity) == 1:
        write = '%  '
    elif len(quantity) == 2:
        write = '%  '
    return write

def resetquantity():
    global QUANTITY
    
    QUANTITY = 100
    savequantity()
    lcd.clear()
    printlcd(0,0, "Reservoir filled")
    GPIO.output(REDLED,GPIO.LOW)
    time.sleep(2)

def savequantity():
    global QUANTITYFILE
    global QUANTITY
    
    with open(QUANTITYFILE, 'w') as quantityfile:
        quantityfile.write(str(QUANTITY))
    feedFile.close()

# This is the main program, essentially runs in a continuous loop looking for button press or remote request
try:

    #### Begin initializations #########################
    ####################################################
    
    # Initialize the logfile
    logFile = open(LOGFILE, 'a')

    # Initialize the LCD
    lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, 
							lcd_columns, lcd_rows, lcd_backlight)
    lcd.clear()

    # Initialize the GPIO system
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    # Initialize the pin for the motor control
    GPIO.setup(MOTORCONTROLPIN, GPIO.OUT)
    GPIO.output(MOTORCONTROLPIN, False)

    # Initialize the pin for the feed and reset buttons
    GPIO.setup(FEEDBUTTONPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RESETBUTTONPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(QUANTITYBUTTONPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Initialize the pin for the LEDs
    GPIO.setup(GREENLED, GPIO.OUT)
    GPIO.setup(REDLED, GPIO.OUT)
    
    # Initialize lastFeed
    if os.path.isfile(FEEDFILE):
        with open(FEEDFILE, 'r') as feedFile:
            lastFeed = float(feedFile.read())
        feedFile.close()
    else:
        lastFeed = time.time()
        saveLastFeed()

    #Initialize quantity remaining
    if os.path.isfile(QUANTITYFILE):
        with open(QUANTITYFILE, 'r') as quantityfile:
            QUANTITY = int(quantityfile.read())
        quantityfile.close()
    else:
        QUANTITY = 100

    #### End of initializations ########################
    ####################################################

    #### The main loop ####
    
    while True:
        #### If reset button pressed, then reset the counter
        if buttonpressed(RESETBUTTONPIN):
            lcd.clear()
            printlcd(0,0, "Resetting...   ")
            lastFeed = time.time() - feedInterval + 5
            saveLastFeed()
            time.sleep(2)

        if buttonpressed(QUANTITYBUTTONPIN):
            resetquantity()
            
        ### Check if the food container is still fuller than 10%
        if QUANTITY < 10:
            GPIO.output(REDLED,GPIO.HIGH)
        
        #### Check if we are ready to feed
        if (time.time() - lastFeed) > feedInterval:
            printlcd(0,0, str(QUANTITY) + quantityprint(QUANTITY) + time.strftime("%m/%d %I:%M", time.localtime(time.time())))
            printlcd(0,1, "Ready to feed   ")
            GPIO.output(GREENLED,GPIO.HIGH)

            #### See if the button is pressed
            if buttonpressed(FEEDBUTTONPIN):
                lastFeed = feednow()
                saveLastFeed()
            
            #### Check if remote feed request is available
            #elif remotefeedrequest():
            #    lastFeed = feednow()
            #    saveLastFeed()


                
        #### Since it is not time to feed yet, keep the countdown going
        else:
            timeToFeed = (lastFeed + feedInterval) - time.time()
            printlcd(0,0, str(QUANTITY) + quantityprint(QUANTITY) + time.strftime("%m/%d %I:%M", time.localtime(time.time())))
            printlcd(0,1, 'Next:' + time.strftime("%Hh %Mm %Ss", time.gmtime(timeToFeed)))
            if buttonpressed(FEEDBUTTONPIN):
                lcd.clear()
                printlcd(0,0, "Not now, try at ")
                printlcd(0,1, time.strftime("%b/%d %H:%M", time.localtime(lastFeed + feedInterval)))
                time.sleep(2)
        time.sleep(.6)

#### Cleaning up at the end
except KeyboardInterrupt:
    logFile.close()
    lcd.clear()
    GPIO.cleanup()

except SystemExit:
    logFile.close()
    lcd.clear()
    GPIO.cleanup()

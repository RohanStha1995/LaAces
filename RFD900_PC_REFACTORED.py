#RFD900 PC REFACTORED Ground Station Software
#...Modified and Refactored by Michael Casteel
#...For McNeese State University
#...Louisiana Aerospace Catalyst Experiences for Students (LaACES) Program
#...Last updated in Spring 2019

#Based off original code by Dylan Trafford
#...For the Montana Space Grant Consortium (MSGC) Borealis Program
#...Originally written in Spring 2015

# ----- IMPORTS ----- #

import ImageTk
from Tkinter import * #Tkinter GUI module
import tkMessageBox

import time
import datetime
import base64
import hashlib 
import os

import struct #for unpacking data

import traceback #traceback functionality for error handling

import serial #for communication with RFD900 over USB
import subprocess
import sys
import PIL.Image # = for image processing

from multiprocessing.connection import Client

# ----- INITIALIZE SERVO PROCESS COMMUNICATION ----- #

clientGPS = Client(('localhost',5000))

# ----- SESSION TIME AND DIRECTORY ----- #

sessionTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')

sessionDir = "SESSIONS/Session_{}/".format(sessionTime)
if not os.path.exists(sessionDir):
    os.makedirs(sessionDir)

# ----- LOGGING DECLARATIONS ----- #

event_logFileName = "{}Event_Log_File_{}.txt".format(sessionDir,sessionTime)
runtime_logFileName = "{}Runtime_Log_File_{}.txt".format(sessionDir,sessionTime)

with open(event_logFileName, "w+") as event_logFile:
    event_logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    event_logFile.write(" (aka {} UTC Epoch) -- Ground Station Software Starts\r\n".format(time.time()))	

#unbuffered class is used to output console writing to the runtime logging file 
class Unbuffered:
    def __init__(self,stream):
        self.stream = stream
    def write(self,data):
        self.stream.write(data)
        self.stream.flush()
        runtime_logFile.write(data)
        runtime_logFile.flush()
    def flush(self):
        self.stream.flush()
    def close(self):
        self.stream.close()

runtime_logFile = open(runtime_logFileName,'w+')
sys.stdout = Unbuffered(sys.stdout) #create unbuffered output to runtime log file

# ----- MODEM CONNECTION INITIALIZATION ----- #

try:
    #Serial Variables
    port = "COM6"              #This is a computer dependent setting. Open Device Manager to determine which port the RFD900 Modem is plugged into
    baud = 38400				#baud rate in bits/s, need to be adjusted to match the modem's baud rate (note: independent of *air* data rate!)
    timeout = 3                 #Sets the ser.read() timeout period, or when to continue in the code when no data is received after the timeout period (in seconds)

    #Initializations
    ser = serial.Serial(port = port, baudrate = baud, timeout = timeout)
    wordlength = 3000          #Variable to determine spacing of checksum. Ex. wordlength = 1000 will send one thousand bits before calculating and verifying checksum
    imagedatasize = 10000
    extension = ".png"
    timeupdateflag = 0          #determines whether to update timevar on the camera settings
except:
    with open(event_logFileName, "a") as logFile:
        logFile.write("\r\n--- ")
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- CRITICAL ERROR: INTIALIZATION ---\r\n\r\n".format(time.time()))
        e = sys.exc_info()
        logFile.write("{}\r\n".format(e[0]))
        logFile.write("{}\r\n".format(e[1]))
        logFile.write("{}".format(traceback.format_exc(e[2])))
        print("There was a critical error! Stopping Program, please see \"{}\" for details.".format(event_logFileName))
        sys.exit()
		
# ------ CAMERA INITIAL VALUES ----- #

width = 650
height = 450
sharpness = 0               #Default  =0; range = (-100 to 100)
brightness = 50             #Default = 50; range = (0 to 100)
contrast = 0                #Default = 0; range = (-100 to 100)
saturation = 0              #Default = 0; range = (-100 to 100)
iso = 400                   #Unknown Default; range = (100 to 800)

payloadGPS = ""

pingGPS = -1.0
GPSLength = 35


# ------ FUNCTION DECLARATIONS ----- #

def updateslider():
    global width
    global height
    global sharpness
    global brightness
    global contrast
    global saturation
    global iso
    global timeupdateflag
    try:
        widthslide.set(width)
        heightslide.set(height)
        sharpnessslide.set(sharpness)
        brightnessslide.set(brightness)
        contrastslide.set(contrast)
        saturationslide.set(saturation)
        isoslide.set(iso)
    except:
        print "error setting slides to new values"
        print "here are current values"
        print width
        print height
        print sharpness
        print brightness
        print contrast
        print saturation
        print iso
        sys.stdout.flush()
    try:
        if (timeupdateflag == 1):
            timeVar.set("Last Updated: "+str(datetime.datetime.now().strftime("%Y/%m/%d @ %H:%M:%S")))
            timeupdateflag = 0
        else:
            timeVar.set("No Recent Update")
        widthVar.set("Current Width = "+str(width))
        heightVar.set("Current Height = " + str(height))
        sharpnessVar.set("Current Sharpness = " + str(sharpness))
        brightnessVar.set("Current Brightness = " + str(brightness))
        contrastVar.set("Current Contrast = " + str(contrast))
        saturationVar.set("Current Saturation = " + str(saturation))
        isoVar.set("Current ISO = " + str(iso))
    except:
        print "error setting slides to new values"
        print "here are current values"
        print width
        print height
        print sharpness
        print brightness
        print contrast
        print saturation
        print iso
    return

def reset_cam():
    global width
    global height
    global sharpness
    global brightness
    global contrast
    global saturation
    global iso
    width = 650
    height = 450
    sharpness = 0               #Default  =0; range = (-100 to 100)
    brightness = 50             #Default = 50; range = (0 to 100)
    contrast = 0                #Default = 0; range = (-100 to 100)
    saturation = 0              #Default = 0; range = (-100 to 100)
    iso = 400                   #Unknown Default; range = (100 to 800)
    print "Default width:",width
    print "Default height:",height
    print "Default sharpness:",sharpness
    print "Default brightness:",brightness
    print "Default contrast:",contrast
    print "Default saturation:",saturation
    print "Default ISO:",iso
    sys.stdout.flush()
    try:
        widthslide.set(width)
        heightslide.set(height)
        sharpnessslide.set(sharpness)
        brightnessslide.set(brightness)
        contrastslide.set(contrast)
        saturationslide.set(saturation)
        isoslide.set(iso)
    except:
        print "error setting slides to new values"
        print "here are current values"
        print width
        print height
        print sharpness
        print brightness
        print contrast
        print saturation
        print iso
        sys.stdout.flush()
    return

def b64_to_image(data,savepath):                                    #Back converts a base64 String of ASCII characters into an image, the save path dictates image format
    fl = open(savepath, "wb")
    fl.write(data.decode('base64'))
    fl.close()

def gen_checksum(data):
    return hashlib.md5(data).hexdigest()                            #Generates a 32 character hash up to 10000 char length String(for checksum). If string is too long I've notice length irregularities in checksum

def sync():                                                         #This is module to ensure both sender and receiver at that the same point in their data streams to prevent a desync
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Attempted to Sync\r\n".format(time.time()))
    print "Attempting to Sync - This should take approx. 2 sec"
    sync = ""
    addsync0 = ""
    addsync1 = ""
    addsync2 = ""
    addsync3 = ""
    while(sync != "sync"):                                          #Program is held until no data is being sent (timeout) or until the pattern 's' 'y' 'n' 'c' is found
        addsync0 = ser.read()
        addsync0 = str(addsync0)
        if(addsync0 == ''):
            break
        sync = addsync3 + addsync2 + addsync1 + addsync0
        addsync3 = addsync2
        addsync2 = addsync1
        addsync1 = addsync0
    sync = ""
    ser.write('S')                                                  #Notifies sender that the receiving end is now synced 
    print "System Match"
    ser.flushInput()
    ser.flushOutput()
    return

def receive_image(savepath, wordlength):
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Start Photo Receiving\r\n".format(time.time()))
    onceDone = False
    resetOnce = False

    print "confirmed photo request"                                 #Notifies User we have entered the receiveimage() module
    #sys.stdout.flush()
    
    #Module Specific Variables
    trycnt = 0                                                      #Initializes the checksum timeout (timeout value is not set here)
    finalstring = ""                                                #Initializes the data string so that the += function can be used
    done = False                                                    #Initializes the end condition
    
    #Retreive Data Loop (Will end when on timeout)
    while(done == False):
        if(onceDone == True):
            if(resetOnce == False):
                resetOnce = True
            else:
                onceDone = False

        print "Current Recieve Position: ", str(len(finalstring))
        checktheirs = ""
        checktheirs = ser.read(32)                                  #Asks first for checksum. Checksum is asked for first so that if data is less than wordlength, it won't error out the checksum data
        #print (checktheirs)
        payloadGPS = ser.read(GPSLength)
        
        clientGPS.send(payloadGPS)
        
        #print (payloadGPS)
        word = ser.read(wordlength)                                 #Retreives characters, wholes total string length is predetermined by variable wordlength
        checkours = gen_checksum(payloadGPS + word)                              #Retreives a checksum based on the received data string
        #print (checkours)
        
        #CHECKSUM
        if (checkours != checktheirs):
            if(trycnt < 5):                                         #This line sets the maximum number of checksum resends. Ex. trycnt = 5 will attempt to rereceive data 5 times before erroring out                                              #I've found that the main cause of checksum errors is a bit drop or add desync, this adds a 2 second delay and resyncs both systems 
                ser.write('N')
                trycnt += 1
                print "try number:", str(trycnt)
                print "\tresend last"                                 #This line is mostly used for troubleshooting, allows user to view that both devices are at the same position when a checksum error occurs
                print "\tpos @" , str(len(finalstring))
                #sys.stdout.flush()
                sync()                                              #This corrects for bit deficits or excesses ######  THIS IS A MUST FOR DATA TRANSMISSION WITH THE RFD900s!!!! #####
                with open(event_logFileName, "a") as logFile:
                   logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                   logFile.write(" (aka {} UTC Epoch) -- Packet Failure, Retry Number {}\r\n".format(time.time(), trycnt))
            else:
                print "ran out of send attempts"
                ser.write('N')                                      #Kind of a worst case, checksum trycnt is reached and so we save the image and end the receive, a partial image will render if enough data
                finalstring += word                                 
                done = True
                with open(event_logFileName, "a") as logFile:
                    logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    logFile.write(" (aka {} UTC Epoch) -- ERROR: Ran out of retry attempts, truncating photo\r\n".format(time.time()))
                break
        else:
            trycnt = 0
            ser.write('Y')
            print ("GPS Location:" + payloadGPS)
            finalstring += word
        if(word == ""):
            if(onceDone == False):
                print "their word was empty, trying again"
                #ser.read(ser.inWaiting())
                ser.write('Y')
                #sys.stdout.flush()
                sync()
                resetOnce = False
                onceDone = True
                with open(event_logFileName, "a") as logFile:
                    logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    logFile.write(" (aka {} UTC Epoch) -- Payload word was empty, retrying\r\n".format(time.time()))
            else:
                print "word was empty"
                done = True
                with open(event_logFileName, "a") as logFile:
                    logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    logFile.write(" (aka {} UTC Epoch) -- Word was empty, ending photo receiving\r\n".format(time.time()))
                break
        if(checktheirs == ""):
            if(onceDone == False):
                print "their check was empty, trying again"
                #ser.read(ser.inWaiting())
                ser.write('Y')
                #sys.stdout.flush()
                sync()
                resetOnce = False
                onceDone = True
                with open(event_logFileName, "a") as logFile:
                    logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    logFile.write(" (aka {} UTC Epoch) -- Payload check-word was empty, retrying\r\n".format(time.time()))
            else:
                print "their check was empty twice, stopping"
                done = True
                with open(event_logFileName, "a") as logFile:
                    logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    logFile.write(" (aka {} UTC Epoch) -- Payload check-word empty twice, ending photo receiving\r\n".format(time.time()))
                break
    try:                                                            #This will attempt to save the image as the given filename, if it for some reason errors out, the image will go to the except line
        b64_to_image(finalstring,savepath)
        imageDisplay.set(savepath)
    except:
        e = sys.exc_info()
        print e[0]
        print e[1]
        print "Error with filename, saved as newimage" + extension
        sys.stdout.flush()
        b64_to_image(finalstring,"newimage" + extension)            #Save image as newimage.jpg due to a naming error
        with open(event_logFileName, "a") as logFile:
            logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logFile.write(" (aka {} UTC Epoch) -- ERROR: File save name error, saving as \"newimage.jpg\"\r\n".format(time.time()))
    
    print "Image Saved"
    sys.stdout.flush()
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- End Photo Receiving\r\n".format(time.time()))


def most_Recent():     #Get Most Recent Photo
    ser.flushInput()
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Requested most recent photo\r\n".format(time.time()))
    global im
    global photo
    global tmplabel
    global reim
    ser.write('1')
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        sys.stdout.flush()
        ser.write('1')
    #sync()
    sendfilename = ""
    temp = 0
    while(temp <= 14):
        sendfilename += str(ser.read())
        temp += 1
    #sendfilename = "image" + sendfilename +extension
    imagepath = imagename.get()
    if (imagepath == ""):
        try:
            if(sendfilename[0] == "i"):
                imagepath = sendfilename
            else:
                imagepath = "image_%s%s" % (str(datetime.datetime.now().strftime("%Y%m%d_T%H%M%S")),extension)
        except:
            imagepath = "image_%s%s" % (str(datetime.datetime.now().strftime("%Y%m%d_T%H%M%S")),extension)
    else:
        imagepath = imagepath+extension
            
    try:
        print "Image will be saved as:", imagepath
        tkMessageBox.showinfo("In Progress..",message = "Image request recieved.\nImage will be saved as "+imagepath)
        timecheck = time.time()
        sys.stdout.flush()
        receive_image(str(sessionDir + imagepath), wordlength)
        im = PIL.Image.open(str(sessionDir + imagepath))
        reim = im.resize((650,450),PIL.Image.ANTIALIAS)
        photo = ImageTk.PhotoImage(reim)
        tmplabel.configure(image = photo)
        tmplabel.pack(fill=BOTH,expand = 1)
        print "Receive Time =", (time.time() - timecheck)
    except:
        with open(event_logFileName, "a") as logFile:
            logFile.write("\r\n--- ")
            logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logFile.write(" (aka {} UTC Epoch) -- CRITICAL ERROR: MOST RECENT PHOTO ---\r\n\r\n".format(time.time()))
            e = sys.exc_info()
            logFile.write("{}\r\n".format(e[0]))
            logFile.write("{}\r\n".format(e[1]))
            logFile.write("{}".format(traceback.format_exc(e[2])))
            print("There was a critical error! Please see \"{}\" for details.".format(event_logFileName))
    sys.stdout.flush()
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Finished receiving most recent photo\r\n".format(time.time()))
    return

def cmd2():     #reguest imagedata.txt
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Requesting imagedata.txt\r\n".format(time.time()))
    try:
        listbox.delete(0,END)
    except:
        print "Failed to delete Listbox, window may have been destroyed"
        with open(event_logFileName, "a") as logFile:
            logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logFile.write(" (aka {} UTC Epoch) -- ERROR: Failed to delete listbox, window may have been destroyed\n".format(time.time()))
        sys.stdout.flush()
    ser.write('2')
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        sys.stdout.flush()
        ser.write('2')
    #sync()
    try:
        datafilepath = datafilename.get()
        if (datafilepath == ""):
            datafilepath = "imagedata"
        file = open(datafilepath+".txt","w")
    except:
        print "Error with opening file"
        with open(event_logFileName, "a") as logFile:
            logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logFile.write(" (aka {} UTC Epoch) -- ERROR: Error with opening imagedata file\r\n".format(time.time()))
        sys.stdout.flush()
        return
    timecheck = time.time()
    temp = ser.readline()
    while(temp != ""):
        file.write(temp)
        try:
            listbox.insert(0,temp)
        except:
            print "error adding items"
            with open(event_logFileName, "a") as logFile:
                logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                logFile.write(" (aka {} UTC Epoch) -- ERROR: Error adding items to listbox\r\n".format(time.time()))
            break
        temp = ser.readline()
    file.close()
    print "File Recieved, Attempting Listbox Update"
    sys.stdin.flush()
    subGui.lift()
    subGui.mainloop()
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Finished receiving image list\r\n".format(time.time()))
    return

def cmd3():     #reguest specific image
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Requested specific photo\r\n".format(time.time()))
    global im
    global photo
    global tmplabel
    global reim
    item = map(int,listbox.curselection())
    try:
        data = listbox.get(ACTIVE)
    except:
        print "Nothing Selected"
        with open(event_logFileName, "a") as logFile:
            logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logFile.write(" (aka {} UTC Epoch) -- ERROR:  no photo was selected\r\n".format(time.time()))
        sys.stdout.flush()
        return
    data = data[0:15]
    print data[10]
    if (data[10] != 'b'):
        tkMessageBox.askquestion("W A R N I N G",message = "You have selected the high resolution image.\nAre you sure you want to continue?\nThis download could take 15+ min.",icon = "warning")
        if 'yes':
            ser.write('3')
            while (ser.read() != 'A'):
                print "Waiting for Acknowledge"
                sys.stdout.flush()
                ser.write('3')
            sync()
            try:
                imagepath = data
                ser.write(data)
                timecheck = time.time()
                tkMessageBox.showinfo("In Progress...",message = "Image request recieved.\nImage will be saved as "+imagepath)
                print "Image will be saved as:", imagepath
                sys.stdout.flush()
                receive_image(str(sessionDir + imagepath), wordlength)
                im = PIL.Image.open(sessionDir + imagepath)
                reim = im.resize((650,450),PIL.Image.ANTIALIAS)
                photo = ImageTk.PhotoImage(reim)
                tmplabel.configure(image = photo)
                tmplabel.pack(fill=BOTH,expand = 1)
                print "Receive Time =", (time.time() - timecheck)
            except:
                with open(event_logFileName, "a") as logFile:
                    logFile.write("\r\n--- ")
                    logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                    logFile.write(" (aka {} UTC Epoch) -- CRITICAL ERROR: SPECIFIC PHOTO REQUEST ---\r\n\r\n".format(time.time()))
                    e = sys.exc_info()
                    logFile.write("{}\r\n".format(e[0]))
                    logFile.write("{}\r\n".format(e[1]))
                    logFile.write("{}".format(traceback.format_exc(e[2])))
                    print("There was a critical error! Please see \"{}\" for details.".format(event_logFileName))
            with open(event_logFileName, "a") as logFile:
                logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                logFile.write(" (aka {} UTC Epoch) -- Finished receiving specific photo\r\n".format(time.time())) 
            return
        else:
            return
            
    else:
        ser.write('3')
        while (ser.read() != 'A'):
            print "Waiting for Acknowledge"
            sys.stdout.flush()
            ser.write('3')
        sync()
        try:
            imagepath = data
            ser.write(data)
            timecheck = time.time()
            tkMessageBox.showinfo("In Progress...",message = "Image request recieved.\nImage will be saved as "+imagepath)
            print "Image will be saved as:", imagepath
            sys.stdout.flush()
            receive_image(str(sessionDir + imagepath), wordlength)
            im = PIL.Image.open(sessionDir + imagepath)
            reim = im.resize((650,450),PIL.Image.ANTIALIAS)
            photo = ImageTk.PhotoImage(reim)
            tmplabel.configure(image = photo)
            tmplabel.pack(fill=BOTH,expand = 1)
            print "Receive Time =", (time.time() - timecheck)
        except:
            with open(event_logFileName, "a") as logFile:
                logFile.write("\r\n--- ")
                logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                logFile.write(" (aka {} UTC Epoch) -- CRITICAL ERROR: MOST RECENT PHOTO ---\r\n\r\n".format(time.time()))
                e = sys.exc_info()
                logFile.write("{}\r\n".format(e[0]))
                logFile.write("{}\r\n".format(e[1]))
                logFile.write("{}".format(traceback.format_exc(e[2])))
                print("There was a critical error! Please see \"{}\" for details.".format(event_logFileName))
        with open(event_logFileName, "a") as logFile:
            logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logFile.write(" (aka {} UTC Epoch) -- Finished receiving specific photo\r\n".format(time.time())) 
        return

def cmd4(): #Retrieve current settings
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Requested current settings\r\n".format(time.time())) 
    global width
    global height
    global sharpness
    global brightness
    global contrast
    global saturation
    global iso
    global timeupdateflag
    print "Retrieving Camera Settings"
    try:
        killtime = time.time()+10
        ser.write('4')
        while ((ser.read() != 'A') & (time.time()<killtime)):
            print "Waiting for Acknowledge"
            ser.write('4')
        #sync()
        timecheck = time.time()
        #tkMessageBox.showinfo("In Progress..",message = "Downloading Settings")
        try:
            file = open("camerasettings.txt","w")
            print "File Successfully Created"
        except:
            print "Error with opening file"
            sys.stdout.flush()
            return
        timecheck = time.time()
        sys.stdin.flush()
        temp = ser.read()
        while((temp != "\r") & (temp != "") ):
            file.write(temp)
            temp = ser.read()
        file.close()
        print "Receive Time =", (time.time() - timecheck)
        sys.stdout.flush()
        file = open("camerasettings.txt","r")
        twidth = file.readline()             #Default = (650,450); range up to
        width = int(twidth)
        print "width = ",width
        theight = file.readline()             #Default = (650,450); range up to
        height = int(theight)
        print "height = ",height
        tsharpness = file.readline()              #Default  =0; range = (-100 to 100)
        sharpness = int(tsharpness)
        print "sharpness = ",sharpness
        tbrightness = file.readline()             #Default = 50; range = (0 to 100)
        brightness = int(brightness)
        print "brightness = ", brightness
        tcontrast = file.readline()               #Default = 0; range = (-100 to 100)
        contrast = int(tcontrast)
        print "contrast = ",contrast
        tsaturation = file.readline()             #Default = 0; range = (-100 to 100)
        saturation = int(tsaturation)
        print "saturation = ",saturation
        tiso = file.readline()                      #Unknown Default; range = (100 to 800)
        iso = int(tiso)
        print "iso = ",iso
        file.close()
        timeupdateflag = 1
        updateslider()
        with open(event_logFileName, "a") as logFile:
            logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logFile.write(" (aka {} UTC Epoch) -- Finished receiving current settings\r\n".format(time.time())) 
    except:
        with open(event_logFileName, "a") as logFile:
            logFile.write("\r\n--- ")
            logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            logFile.write(" (aka {} UTC Epoch) -- CRITICAL ERROR: RECEIVING CURRENT SETTINGS ---\r\n\r\n".format(time.time()))
            e = sys.exc_info()
            logFile.write("{}\r\n".format(e[0]))
            logFile.write("{}\r\n".format(e[1]))
            logFile.write("{}".format(traceback.format_exc(e[2])))
            print("There was a critical error! Please see \"{}\" for details.".format(event_logFileName))
        print "Camera Setting Retrieval Error"
    return

def cmd5():     #upload new settings
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Uploading new settings\r\n".format(time.time())) 
    global width
    global height
    global sharpness
    global brightness
    global contrast
    global saturation
    global iso
    width = widthslide.get()
    height = heightslide.get()
    sharpness = sharpnessslide.get()
    brightness = brightnessslide.get()
    contrast = contrastslide.get()
    saturation = saturationslide.get()
    iso = isoslide.get()
    file = open("camerasettings.txt","w")
    file.write(str(width)+"\n")
    file.write(str(height)+"\n")
    file.write(str(sharpness)+"\n")
    file.write(str(brightness)+"\n")
    file.write(str(contrast)+"\n")
    file.write(str(saturation)+"\n")
    file.write(str(iso)+"\n")
    file.close()
    
    ser.write('5')
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        #sys.stdin.flush()
        ser.write('5')
    #sync()
    timecheck = time.time()
    #tkMessageBox.showinfo("In Progress..",message = "Downloading Settings")
    try:
        file = open("camerasettings.txt","r")
    except:
        print "Error with opening file"
        sys.stdout.flush()
        return
    timecheck = time.time()
    temp = file.readline()
    while(temp != ""):
        ser.write(temp)
        temp = file.readline()
    file.close()
    error = time.time()
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        sys.stdout.flush()
        if(error+10<time.time()):
            with open(event_logFileName, "a") as logFile:
                logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                logFile.write(" (aka {} UTC Epoch) -- ERROR: Timed-out when sending new settings, no acknowledge received\r\n".format(time.time())) 
            print "Acknowledge not received"
            return
    print "Send Time =", (time.time() - timecheck)
    sys.stdout.flush()
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- New camera settings uploaded\r\n".format(time.time())) 
    return

def time_sync():
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Attempting a time sync\r\n".format(time.time())) 
    #ser.flushInput()
    ser.write('T')
    termtime = time.time() + 20
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        ser.write('T')
        if (termtime < time.time()):
            with open(event_logFileName, "a") as logFile:
                logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                logFile.write(" (aka {} UTC Epoch) -- ERROR: no acknowledge recieved, connection error\r\n".format(time.time())) 
            print "No Acknowledge Recieved, Connection Error"
            sys.stdout.flush()
            return
    localtime = str(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
    rasptime = str(ser.readline())
    print "##################################\nRaspb Time = %s\nLocal Time = %s\n##################################" % (rasptime,localtime)
    sys.stdin.flush()
    connectiontest(10)
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Finished time sync\r\n".format(time.time())) 
    return

def connectiontest(numping):
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Attempted ping, {} packets\r\n".format(time.time(), numping)) 
    ser.write('6')
    termtime = time.time() + 20
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        ser.write('6')
        if (termtime < time.time()):
            with open(event_logFileName, "a") as logFile:
                logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                logFile.write(" (aka {} UTC Epoch) -- ERROR: no acknowledge received, connection error\r\n".format(time.time())) 
            print "No Acknowledge Recieved, Connection Error"
            sys.stdout.flush()
            return
    avg = 0
    ser.write('P')
    temp = ""
    for x in range (1,numping):
        sendtime = time.time()
        receivetime = 0
        termtime = sendtime + 10
        while ((temp != 'P')&(time.time()<termtime)):
            ser.write('P')
            temp = ser.read()
            receivetime = time.time()
        if (receivetime == 0):
            print "Connection Error, No return ping within 10 seconds"
            with open(event_logFileName, "a") as logFile:
                logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                logFile.write(" (aka {} UTC Epoch) -- ERROR: connection error, no return ping within 10 seconds\r\n".format(time.time())) 
            ser.write('D')
            sys.stdout.flush()
            return
        else:
            temp = ""
            avg += receivetime - sendtime
            #print (avg/x)
    ser.write('D')
    avg = avg/numping
    print "Ping Response Time = " + str(avg)[0:4] + " seconds"
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Finished ping test\r\n".format(time.time())) 
    sys.stdout.flush()
    return

def requestGPS():
    ser.flushInput()
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Requesting GPS Data\r\n".format(time.time()))
    ser.write('G')
    termtime = time.time() + 5
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        sys.stdout.flush()
        if (termtime < time.time()):
            with open(event_logFileName, "a") as logFile:
                logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
                logFile.write(" (aka {} UTC Epoch) -- ERROR: no acknowledge received, connection error\r\n".format(time.time())) 
            print "No Acknowledge Recieved, Connection Error"
            sys.stdout.flush()
            return
    payloadGPS = ser.read(GPSLength)
    #TODO - process the input gps data
    with open(event_logFileName, "a") as logFile:
        logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        logFile.write(" (aka {} UTC Epoch) -- Payload location: {}\r\n".format(time.time(), payloadGPS))
    #print test
    
    clientGPS.send(payloadGPS)
    sys.stdout.flush()
    return
    
#optional command to retreive runtime data from payload
'''
def cmd7(): #get payload runtime data
    ser.write('7')
    while (ser.read() != 'A'):
        print "Waiting for Acknowledge"
        sys.stdout.flush()
        ser.write('7')
    #sync()
    timecheck = time.time()
    try:
        file = open("piruntimedata.txt","w")
    except:
        print"Error with opening file"
        sys.stdout.flush()
        return
    timecheck = time.time()
    sys.stdin.flush()
    termtime = time.time()+60
    temp = ser.readline()
    while(temp !="\r"):
        file.write(temp)
        temp = ser.readline()
        if (termtime < time.time()):
            print "Error recieving piruntimedata.txt"
            file.close()
            return
    file.close()
    print "piruntimedata.txt saved to local folder"
    print "Receive Time =", (time.time() - timecheck)
    sys.stdout.flush()
    return
'''
'''
def changeGPSPing():
    global pingGPS
    timing = float(optionList.get())
    pingGPS = timing
    print("ping is now",pingGPS)
    return
'''
# ------ GUI DECLARATION ----- #

#declare main GUI component
mainGui = Tk()
#mainGui.iconbitmap(default="bc.ico")

imageName = StringVar()
dataFileName = StringVar()
imageDisplay = StringVar()
pingCount = StringVar()

widthVar = StringVar()
heightVar = StringVar()
sharpnessVar = StringVar()
brightnessVar = StringVar()
contrastVar = StringVar()
saturationVar = StringVar()
isoVar = StringVar()
timeVar = StringVar()

optionList = StringVar(mainGui)

mainGui.geometry("1300x570+30+30")
mainGui.title("McNeese State University LaACES Program")

mainlabel = Label(text = "RFD900 MSU Interface v0.1", fg = 'grey', font = "Verdana 10 bold")
mainlabel.pack()

imagetitle = Label(textvariable = imageDisplay, font = "Verdana 12 bold")
imagetitle.place(x=300,y=20)


frame = Frame(master = mainGui,width =665,height=465,borderwidth = 5,bg="black",colormap="new")
frame.place(x=295,y=45)
im = PIL.Image.open("MSULa.jpg")
reim = im.resize((650,450),PIL.Image.ANTIALIAS)
photo = ImageTk.PhotoImage(reim)
tmplabel = Label(master = frame,image = photo)
tmplabel.pack(fill=BOTH,expand = 1)

#-------------------------------------------
    #Cmd1 Gui - Request Most Recent Image
most_Recent_Button = Button(mainGui, text = "Most Recent Photo", command = most_Recent)
#most_Recent_Button = Button(mainGui, text = "Most Recent Photo", command = requestGPS)
most_Recent_Button.place(x=150,y=65)

most_Recent_Label = Label(text = "Image Save Name : Default = image_XXXX_b" + extension, font = "Verdana 6 italic")
most_Recent_Label.place(x=10,y=50)

imagename = Entry(mainGui, textvariable=imageName)
imagename.place(x=10,y=70)
#-------------------------------------------
    #Cmd2 Gui - Request text file on image data
cmd2button = Button(mainGui, text = "Request 'imagedata.txt'", command = cmd2)
cmd2button.place(x=150, y=115)

datafilename = Entry(mainGui, textvariable=dataFileName)
datafilename.place(x=10,y=120)

cmd2label = Label(text = "Data File Save Name: Default = imagedata.txt", font = "Verdana 6 italic")
cmd2label.place(x=10,y=100)
#-------------------------------------------
    #Cmd3 Gui - Request specific image
subGui = Tk()
subGui.iconbitmap(default="bc.ico")
listbox = Listbox(subGui,selectmode=BROWSE, font = "Vernada 10")
subGuibutton = Button(subGui, text = "Request Selected Image", command = cmd3)
direction = Label(master=subGui,text = "Click on the image you would like to request", font = "Vernada 12 bold")
subGui.geometry("620x400+20+20")
subGui.title("Image Data and Selection")
direction.pack()
scrollbar = Scrollbar(subGui)
scrollbar.pack(side=RIGHT, fill = Y)
listbox.pack(side=TOP, fill = BOTH, expand = 1)
subGuibutton.pack()
listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)
def subGuiconfirm():
    if tkMessageBox.askokcancel("W A R N I N G",message = "You cannot reopen this window.\n Are you sure you want to close it?",icon = "warning"):
        subGui.destroy()
subGui.protocol('WM_DELETE_WINDOW',subGuiconfirm)


#-------------------------------------------
    #Cmd4 and Cmd 5 Gui - Camera Settings
camedge = Frame(mainGui,height = 330,width = 250,background = "black",borderwidth=3)
camedge.place(x=1000,y=50)
camframe = Frame(camedge, height = 50, width = 40)
camframe.pack(fill=BOTH,expand = 1)
#camframe.place(x=1000,y=50)

cambot = Frame(camframe,borderwidth = 1)
cambot.pack(side=BOTTOM,fill=X,expand =1)
camleft = Frame(camframe)
camleft.pack(side=LEFT,fill=BOTH,expand=2)
camright = Frame(camframe)
camright.pack(side=RIGHT,fill=BOTH,expand=2)

widthslide = Scale(camleft,from_=1, to=2592,orient=HORIZONTAL)
widthslide.set(width)
widthslide.pack()

widlabel = Label(master = camright,textvariable = widthVar, font = "Verdana 8")
widlabel.pack(pady=19)

heightslide = Scale(camleft,from_=1, to=1944, orient=HORIZONTAL)
heightslide.set(height)
heightslide.pack()
heilabel = Label(master = camright,textvariable = heightVar, font = "Verdana 8")
heilabel.pack(pady=5)

sharpnessslide = Scale(camleft,from_=-100, to=100,orient=HORIZONTAL)
sharpnessslide.set(sharpness)
sharpnessslide.pack()
shalabel = Label(master = camright,textvariable = sharpnessVar, font = "Verdana 8")
shalabel.pack(pady=18)

brightnessslide = Scale(camleft,from_=0, to=100,orient=HORIZONTAL)
brightnessslide.set(brightness)
brightnessslide.pack()
brilabel = Label(master = camright,textvariable = brightnessVar, font = "Verdana 8")
brilabel.pack(pady=5)

contrastslide = Scale(camleft,from_=-100, to=100,orient=HORIZONTAL)
contrastslide.set(contrast)
contrastslide.pack()
conlabel = Label(master = camright,textvariable = contrastVar, font = "Verdana 8")
conlabel.pack(pady=18)

saturationslide = Scale(camleft,from_=-100, to=100,orient=HORIZONTAL)
saturationslide.set(saturation)
saturationslide.pack()
satlabel = Label(master = camright,textvariable = saturationVar, font = "Verdana 8")
satlabel.pack(pady=5)

isoslide = Scale(camleft,from_=100, to=800,orient=HORIZONTAL)
isoslide.set(iso)
isoslide.pack()
isolabel = Label(master = camright,textvariable = isoVar, font = "Verdana 8")
isolabel.pack(pady=18)

cmd4button = Button(cambot, text = "Get Current Settings", command = cmd4,borderwidth = 2,background = "white",font = "Verdana 10")
cmd4button.grid(row = 1,column = 1)

cmd5button = Button(cambot, text = "Send New Settings", command = cmd5,borderwidth = 2,background = "white",font = "Verdana 10")
cmd5button.grid(row = 1,column = 0)

defaultbutton = Button(cambot,text = "Default Settings",command = reset_cam,borderwidth = 2,background = "white",font = "Verdana 10",width = 20)
defaultbutton.grid(row = 0,columnspan = 2,pady=5)

timelabel = Label(master = mainGui,textvariable=timeVar,font="Verdana 8")
timelabel.place(x=1020,y=27)

updateslider()
#-------------------------------------------
    #Cmd 6 - Gui setup for connection testing

conbutton = Button(mainGui,text = "Connection Test",command = time_sync,borderwidth = 2,font = "Verdana 10",width = 25)
conbutton.place(x=25,y=490)

#-------------------------------------------
    #Location Polling timer
    
timingLabel = Label(mainGui, text = "Change GPS Ping Timing (seconds)")
timingLabel.place(x=90,y=530)

OPTIONS = ["-1","0.5","3","10"]
optionList.set(OPTIONS[0])
timingList = OptionMenu(mainGui,optionList,*OPTIONS)
timingList.place(x=25,y=530)

#-------------------------------------------
    #HERE WE GO!!!

rframe = Frame(mainGui,height = 40, width = 35)
runlistbox = Listbox(rframe,selectmode=BROWSE, font = "Vernada 8",width=35,height=20)
runscrollbar = Scrollbar(rframe)
runlistbox.config(yscrollcommand=runscrollbar.set)
runscrollbar.config(command=runlistbox.yview)
runscrollbar.pack(side=RIGHT,fill=Y)
runlistbox.pack(side=LEFT,fill=Y)
rframe.place(x=10,y=165)

def callback():
    global runlistbox
    global mainGui
    try:
        runlistbox.delete(0,END)
    except:
        print "Failed to delete Listbox"
    print str(datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
    sys.stdout.flush()
    for line in reversed(list(open(runtime_logFileName))):
        runlistbox.insert(END,line.rstrip())
    mainGui.after(5000,callback)
    return

def mGuicloseall():    
    with open(event_logFileName, "a") as event_logFile:
        event_logFile.write(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        event_logFile.write(" (aka {} UTC Epoch) -- Program Closed\r\n".format(time.time())) 
    subGui.destroy()
    mainGui.destroy()
    ser.close()
    print "Program Terminated"
    sys.stdout.close()
    return
	
# ----- RUNTIME / GUI LOOP ACTIVATION ----- #

mainGui.protocol('WM_DELETE_WINDOW',mGuicloseall)
mainGui.after(1000,time_sync())
callback()

deltTime = time.time()

while True:
    try:
        pingGPS = float(optionList.get())
        if((pingGPS > 0.0) and (time.time() - deltTime > pingGPS)):
            print(pingGPS)
            print("GPS Automatically Requested")
            requestGPS()
            deltTime = time.time()   
        mainGui.update_idletasks()
        mainGui.update()
    except TclError as error:
        exit()

#mainGui.mainloop()

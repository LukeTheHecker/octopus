"""
Simple Python RDA client for the RDA tcpip interface of the BrainVision Recorder
It reads all the information from the recorded EEG,
prints EEG and marker information to the console and calculates and
prints the average power every second


Brain Products GmbH
Gilching/Freiburg, Germany
www.brainproducts.com

"""

# needs socket and struct library
from socket import *
from struct import *
# from test import package_size
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from plot import DataMonitor, HistMonitor
import time
from matplotlib.widgets import Button
# Marker class for storing marker information
class Marker:
    def __init__(self):
        self.position = 0
        self.points = 0
        self.channel = -1
        self.type = ""
        self.description = ""

# Helper function for receiving whole message
def RecvData(socket, requestedSize):
    returnStream = ''
    while len(returnStream) < requestedSize:
        databytes = socket.recv(requestedSize - len(returnStream))
        if databytes == '':
            raise RuntimeError, "connection broken"
        returnStream += databytes
 
    return returnStream   

    
# Helper function for splitting a raw array of
# zero terminated strings (C) into an array of python strings
def SplitString(raw):
    stringlist = []
    s = ""
    for i in range(len(raw)):
        if raw[i] != '\x00':
            s = s + raw[i]
        else:
            stringlist.append(s)
            s = ""

    return stringlist
    

# Helper function for extracting eeg properties from a raw data array
# read from tcpip socket
def GetProperties(rawdata):

    # Extract numerical data
    (channelCount, samplingInterval) = unpack('<Ld', rawdata[:12])

    # Extract resolutions
    resolutions = []
    for c in range(channelCount):
        index = 12 + c * 8
        restuple = unpack('<d', rawdata[index:index+8])
        resolutions.append(restuple[0])

    # Extract channel names
    channelNames = SplitString(rawdata[12 + 8 * channelCount:])

    return (channelCount, samplingInterval, resolutions, channelNames)

# Helper function for extracting eeg and marker data from a raw data array
# read from tcpip socket       
def GetData(rawdata, channelCount):

    # Extract numerical data
    (block, points, markerCount) = unpack('<LLL', rawdata[:12])

    # Extract eeg data as array of floats
    data = []
    for i in range(points * channelCount):
        index = 12 + 4 * i
        value = unpack('<f', rawdata[index:index+4])
        data.append(value[0])

    # Extract markers
    markers = []
    index = 12 + 4 * points * channelCount
    for m in range(markerCount):
        markersize = unpack('<L', rawdata[index:index+4])

        ma = Marker()
        (ma.position, ma.points, ma.channel) = unpack('<LLl', rawdata[index+4:index+16])
        typedesc = SplitString(rawdata[index+16:index+markersize[0]])
        ma.type = typedesc[0]
        ma.description = typedesc[1]

        markers.append(ma)
        index = index + markersize[0]

    return (block, points, markerCount, data, markers)


##############################################################################################
#
# Main RDA routine
#
##############################################################################################

# Create a tcpip socket
con = socket(AF_INET, SOCK_STREAM)
# Connect to recorder host via 32Bit RDA-port
# adapt to your host, if recorder is not running on local machine
# change port to 51234 to connect to 16Bit RDA-port
con.connect(("192.168.2.122", 51244))

# Flag for main loop
finish = False

# data buffer for calculation, empty in beginning
data1s = []

# block counter to check overflows of tcpip buffer
lastBlock = -1

# Initialize own modules
sr = 250
dur_package = 0.02  # This is fixed
package_size = int(round(sr*dur_package))
plot_package_interval = 10 * package_size

fig = plt.figure(num=42, figsize=(13, 6))


axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
# TODO: Go on here next time!
# Button stuff
clicked = False
def myfun(sweg, clicked=clicked):
    print clicked
    clicked = not clicked

bnext = Button(axnext, 'Next')
bnext.on_clicked(myfun)
bprev = Button(axprev, 'Previous')
bprev.on_clicked(myfun)
# Tkinter stuff


data_monitor = DataMonitor(sr, plot_package_interval, fig=fig)
hist_monitor = HistMonitor(sr, fig=fig)
# Time lag monitoring
cnt = 0
lag_s = 99999
startTime = time.time()
theoreticalLooptime = float(package_size)/sr

# Response
targetMarker = 'R 14'

#### Main Loop ####
while not finish:

    # if clicked:
    #     print "yep"
    # else:
    #     print "nope"

    # Get message header as raw array of chars
    rawhdr = RecvData(con, 24)

    # Split array into usefull information id1 to id4 are constants
    (id1, id2, id3, id4, msgsize, msgtype) = unpack('<llllLL', rawhdr)

    # Get data part of message, which is of variable size
    rawdata = RecvData(con, msgsize - 24)

    # Perform action dependend on the message type
    if msgtype == 1:
        # Start message, extract eeg properties and display them
        (channelCount, samplingInterval, resolutions, channelNames) = GetProperties(rawdata)
        # reset block counter
        lastBlock = -1

        print "Start"
        print "Number of channels: " + str(channelCount)
        print "Sampling interval: " + str(samplingInterval)
        print "Resolutions: " + str(resolutions)
        print "Channel Names: " + str(channelNames)

        ch_name = 'RP'
        ch_idx = channelNames.index(ch_name)

    elif msgtype == 4:
        # Data message, extract data and markers
        (block, points, markerCount, data, markers) = GetData(rawdata, channelCount)
        hist_monitor.update_data(data)
        # Check for overflow
        if lastBlock != -1 and block > lastBlock + 1:
            print "*** Overflow with " + str(block - lastBlock) + " datablocks ***" 
        lastBlock = block

        # Print markers, if there are some in actual block
        if markerCount > 0:
            for m in range(markerCount):
                print "Marker " + markers[m].description + " of type " + markers[m].type
            markerDescriptions = [marker.description for marker in markers]
            # Check if correct marker is incoming:
            if targetMarker in markerDescriptions:
                print "{} in {}".format(targetMarker, markerDescriptions)
                hist_monitor.button_press()
                hist_monitor.plot_hist()
            

        # Put data at the end of actual buffer       
        data1s.extend(data)
                
        st = time.time()
        if np.mod(cnt+1, plot_package_interval / package_size) == 0:
            data_reshaped = np.asarray(data1s)
            data_reshaped = data_reshaped.reshape(channelCount, len(data1s)/channelCount)
            data_package = data_reshaped[ch_idx, -plot_package_interval:]
            data_monitor.update(data_package, lagtime=lag_s)    

        # If more than 1s of data is collected, calculate average power, print it and reset data buffer
        if len(data1s) == channelCount * 1000000 / samplingInterval:
            # data_reshaped = np.asarray(data1s)
            # data_reshaped = data_reshaped.reshape(channelCount, len(data1s)/channelCount)
            # data_package = data_reshaped[ch_idx, :]
            # data_monitor.update(data_package)

            index = int(len(data1s) - channelCount * 1000000 / samplingInterval)
            data1s = data1s[index:]

            avg = 0
            # Do not forget to respect the resolution !!!
            for i in range(len(data1s)):
                avg = avg + data1s[i]*data1s[i]*resolutions[i % channelCount]*resolutions[i % channelCount]

            avg = avg / len(data1s)
            # print "Average power: " + str(avg)

            data1s = []

        # Lag Calculation        
        endTime = time.time()
        measuredLoopTime = endTime - startTime
        calculatedEndTime = (theoreticalLooptime*(1 + cnt))
        lag_s = calculatedEndTime - measuredLoopTime
        cnt += 1

    elif msgtype == 3:
        # Stop message, terminate program
        print "Stop"
        finish = True

    
# Close tcpip connection
con.close()

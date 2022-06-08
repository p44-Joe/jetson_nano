#sudo systemctl restart nvargus-daemon
# On the Jetson Nano, OpenCV comes preinstalled
# Data files are in /usr/sharc/OpenCV

import os
import sys
import cv2
import json
import time
import requests
import argparse
import pickledb
import threading
import datetime
import numpy as np
from openalpr import Alpr

parser = argparse.ArgumentParser(description='Arguments for inside or outside camera.')
parser.add_argument('-IN', '--InGarage', action='store_true', help='Argument to play as camera from inside the parking garage')
parser.add_argument('-OUT', '--OutGarage', action='store_true', help='Argument to play as camera from outside the parking garage')
parser.add_argument('-SF', '--StillFrame', action='store_true', help='Arguemnt to show still frame once license plate is detected')
args = parser.parse_args()

if not args.InGarage and not args.OutGarage:
    print("No args entered, exiting program")
    exit()

# def gstreamer_pipeline credit is from https://github.com/JetsonHacksNano/CSI-Camera/blob/master/simple_camera.py
# gstreamer_pipeline returns a GStreamer pipeline for capturing from the CSI camera
# Defaults to 1280x720 @ 30fps 
# Flip the image by setting the flip_method (most common values: 0 and 2)
# display_width and display_height determine the size of the window on the screen

# def gstreamer_pipeline (capture_width=1920, capture_height=1080, display_width=720, display_height=480, framerate=30, flip_method=0) :   
#     return ('nvarguscamerasrc sensor_id=0 ! ' 
#     'video/x-raw(memory:NVMM), '
#     'width=(int)%d, height=(int)%d, '
#     'format=(string)NV12, framerate=(fraction)%d/1 ! '
#     'nvvidconv flip-method=%d ! '
#     'video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! '
#     'videoconvert ! '
#     'video/x-raw, format=(string)BGR ! appsink'  % (capture_width,capture_height,framerate,flip_method,display_width,display_height))

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d !"
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

'''Coming Soon
def apiPut(url_parameters, url_body):
    r = requests.post("https://##########.execute-api.us-east-1.amazonaws.com/dev/print-event", params=url_parameters, data=url_body)
    print(r.status_code, r.reason)


def regNewCar(plateNum, time):
    url_parameters = {
        "command":"InsertDocument",
        "ledgerName":"openalpr",
        "tableName":"garage",
        "plate":plateNum,
        "confidence":"100.00",
        "timestamp":time,
        "action":"registered"
        }
    url_body = {}
    apiPut(url_parameters, url_body)
'''

    
# checking for pickledb files; if not, creating files and loading them.
def load_dbs(infile, regfile):
    exists_in = os.path.isfile('./' + infile)
    exists_reg = os.path.isfile('./' + regfile)
    if not exists_in:
        print('Creating {0}'.format(infile))
        indb = pickledb.load(infile, False)
    else:
        indb = pickledb.load(infile, False)
    if not exists_reg:
        print('Creating {0}'.format(regfile))
        regdb = pickledb.load(regfile, False)
        regdb.set('ANYNAME', str(time.time()))
        #apiPut('ANYNAME', datetime.datetime.utcnow().replace(microsecond=0).isoformat()+'Z')
        
    else:
        regdb = pickledb.load(regfile, False)
    return indb, regdb

#creating new still image of found license plate
def rectangle(cords, img):
    if args.StillFrame:
        x = int(min(cords['coordinates'], key=lambda ev: ev['x'])['x'])
        y = int(min(cords['coordinates'], key=lambda ev: ev['y'])['y'])
        w = int(max(cords['coordinates'], key=lambda ev: ev['x'])['x'])
        h = int(max(cords['coordinates'], key=lambda ev: ev['y'])['y'])
        cv2.rectangle(img,(x,y),(w,h),(255,0,0),2)
        cv2.imshow('Plate Detected', img)

#processing image frame in new thread - TODO look at different methods
def newThread(alpr, num, indb, regdb):
    results = alpr.recognize_ndarray(num)
    if results['results'] != []:
        max_c = max(results['results'], key=lambda ev: ev['confidence'])
        if int(max_c['confidence']) > 80: # adjust confidence here
            # if the license plate is in the in-garage database, open the gate and update db's
            if indb.get(max_c['plate']) and args.InGarage:
                indb.rem(max_c['plate'])
                regdb.set(str(max_c['plate']), str(time.time()))
                url_parameters = {
                    "command":"InsertDocument",
                    "ledgerName":"openalpr",
                    "tableName":"garage",
                    "plate":max_c['plate'],
                    "confidence":max_c['confidence'],
                    "timestamp":"2017-04-21",
                    "action":"exitgarage"
                    }
                url_body = {}
                #apiPut(url_parameters, url_body)
                rectangle(max_c, num)
                print('Opening gate, {0} has left the parking garage'.format(max_c['plate']))
                #print(json.dumps(max_c, indent=4))
            # if the license plate is not in the in-garage database but seen from in the garage
            elif regdb.get(max_c['plate']) and args.InGarage and not indb.get(max_c['plate']):
                if time.time() - float(regdb.get(max_c['plate'])) > 10:
                    print('{0} is a registered vehicle that has already left the garage. Do not open gate.'.format(max_c['plate']))
                    rectangle(max_c, num)
            # if the license plate is registered and seen from the out side camera, and not in the garage database, open gate
            elif regdb.get(max_c['plate']) and args.OutGarage and not indb.get(max_c['plate']):
                print('{0} is a registered vehicle, opening gate'.format(max_c['plate']))
                indb.set(str(max_c['plate']), str(time.time()))
                rectangle(max_c, num)
            # if the license plate is registered and seen from the out side camera but in the in-garage database
            elif regdb.get(max_c['plate']) and args.OutGarage and indb.get(max_c['plate']):
                if time.time() - float(indb.get(max_c['plate'])) > 10:
                    print('{0} is a registered vehicle that is already in the garage, do not open gate'.format(max_c['plate']))
                    rectangle(max_c, num)

def lp_detect() :
    in_db, reg_db = load_dbs('cars_in.db', 'cars_reg.db')
    alpr = Alpr("us", "/usr/share/openalpr/config/openalpr.defaults.conf", "/usr/share/openalpr/runtime_data")
    if not alpr.is_loaded():
        print("Error loading OpenALPR")
        sys.exit(1)
    alpr.set_top_n(2)
    cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    if cap.isOpened():
        frame = 0
        cv2.namedWindow('License Plate Detect', cv2.WINDOW_AUTOSIZE)
        while cv2.getWindowProperty('License Plate Detect',0) >= 0:
            ret, img = cap.read()
            if ret:
                frame+=1
                try:
                    if str(frame)[-1] == "0":
                        t = threading.Thread(target=newThread, args=(alpr, img, in_db, reg_db))
                        t.start()
                except Exception as e:
                    print('App error: {0}'.format(e))

                cv2.imshow('License Plate Detect',img)
                keyCode = cv2.waitKey(30) & 0xff
                # Stop the program on press of ESC key or window is closed
                if keyCode == 27 or cv2.getWindowProperty("License Plate Detect", 0) == -1:
                    print('Escape key was pressed')
                    in_db.getall()
                    in_db.dump()
                    reg_db.dump()
                    time.sleep(1)
                    break

        print('Closing cap')
        cap.release()
        print('Closing windows')
        cv2.destroyAllWindows()
        time.sleep(1)
        print('Closing alpr')
        alpr.unload()
    else:
        print("Unable to open camera")

if __name__ == '__main__':
    lp_detect()

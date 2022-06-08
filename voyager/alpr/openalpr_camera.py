# test_camera.py
#
# Open an RTSP stream and feed image frames to 'openalpr'
# for real-time license plate recognition.

import sys
import argparse
import subprocess
import numpy as np
import cv2
from openalpr import Alpr


RTSP_SOURCE  = 'rtsp://face:Face12345@10.15.19.201:554/live.sdp'
WINDOW_NAME  = 'openalpr'
FRAME_SKIP   = 15

# def open_cam_rtsp(uri, width=1280, height=720, latency=2000):
#     gst_str = ('rtspsrc location={} latency={} ! '
#                'rtph264depay ! h264parse ! omxh264dec ! nvvidconv ! '
#                'video/x-raw, width=(int){}, height=(int){}, format=(string)BGRx ! '
#                'videoconvert ! appsink').format(uri, latency, width, height)
#     return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

def open_cam_usb(dev=1, width=800, height=600):
    # We want to set width and height here, otherwise we could just do:
    #     return cv2.VideoCapture(dev)
    gst_str = ('v4l2src device=/dev/video{} ! '
               'video/x-raw, width=(int){}, height=(int){} ! '
               'videoconvert ! appsink').format(dev, width, height)
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

def open_cam_onboard(width=1280, height=720):
    gst_elements = str(subprocess.check_output('gst-inspect-1.0'))
    if 'nvcamerasrc' in gst_elements:
        # On versions of L4T prior to 28.1, add 'flip-method=2' into gst_str
        gst_str = ('nvcamerasrc ! '
                   'video/x-raw(memory:NVMM), '
                   'width=(int)1280, height=(int)720, '
                   'format=(string)I420, framerate=(fraction)10/1 ! '
                   'nvvidconv ! '
                   'video/x-raw, width=(int){}, height=(int){}, '
                   'format=(string)BGRx ! '
                   'videoconvert ! appsink').format(width, height)
    elif 'nvarguscamerasrc' in gst_elements:
        gst_str = ('nvarguscamerasrc ! '
                   'video/x-raw(memory:NVMM), '
                   'width=(int)1280, height=(int)720, '
                   'format=(string)NV12, framerate=(fraction)10/1 ! '
                   'nvvidconv flip-method=2 ! '
                   'video/x-raw, width=(int){}, height=(int){}, '
                   'format=(string)BGRx ! '
                   'videoconvert ! appsink').format(width, height)
    else:
        raise RuntimeError('onboard camera source not found!')
    return cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

def main():
    alpr = Alpr('us', 'tx2.conf', '/usr/share/openalpr/runtime_data')
    if not alpr.is_loaded():
        print('Error loading OpenALPR')
        sys.exit(1)
    alpr.set_top_n(3)
    #alpr.set_default_region('new')

    cap = open_cam_usb()
    # cap = open_cam_onboard()
    if not cap.isOpened():
        alpr.unload()
        sys.exit('Failed to open video file!')
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
    cv2.setWindowTitle(WINDOW_NAME, 'OpenALPR video test')

    _frame_number = 0
    while True:
        ret_val, frame = cap.read()
        if not ret_val:
            print('VidepCapture.read() failed. Exiting...')
            break

        _frame_number += 1
        if _frame_number % FRAME_SKIP != 0:
            continue
        cv2.imshow(WINDOW_NAME, frame)

        results = alpr.recognize_ndarray(frame)
        for i, plate in enumerate(results['results']):
            best_candidate = plate['candidates'][0]
            print('Plate #{}: {:7s} ({:.2f}%)'.format(i, best_candidate['plate'].upper(), best_candidate['confidence']))

        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()
    cap.release()
    alpr.unload()


if __name__ == "__main__":
    main()

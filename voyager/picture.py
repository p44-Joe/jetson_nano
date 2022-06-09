import cv2
import time
import numpy as np
from datetime import datetime

my_date = datetime.utcnow()
filename = "/home/joe/Pictures/"+ my_date.isoformat() +".jpg"
mtx = np.matrix('1.302277119864884753e+03,0.000000000000000000e+00,9.502486590818548393e+02;0.000000000000000000e+00,1.303466191765572148e+03,6.312575445467336976e+02;0.000000000000000000e+00,0.000000000000000000e+00,1.000000000000000000e+00')
dist = np.matrix('-4.024334822479178064e-01,2.120660026985363711e-01,-1.173992294609796892e-02,-6.449904424562102716e-03,-9.215752881837419030e-02')
width = 1920
height = 1080
focus = 255  # min: 0, max: 255, increment:5
frames = 30

def main():
	capture = capture_write()

def capture_write(filename=filename, port=0, ramp_frames=frames, x=width, y=height):
	camera = cv2.VideoCapture(port)

	# Set Resolution
	camera.set(cv2.CAP_PROP_FRAME_WIDTH, x)
	camera.set(cv2.CAP_PROP_FRAME_HEIGHT, y)
	#camera.set(cv2.CAP_PROP_FOCUS, focus)
	#camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)

	# Adjust camera lighting
	for i in range(ramp_frames):
		temp = camera.read()
	retval, im = camera.read()
	dst = cv2.undistort(im, mtx, dist, None, mtx)
	cv2.imwrite(filename,dst)
	del(camera)
	return True

if __name__ == '__main__':
    main()


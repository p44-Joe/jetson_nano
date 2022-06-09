import cv2
import numpy as np
from datetime import datetime

my_date = datetime.utcnow()
filename = my_date.isoformat() +".jpg"

mtx = np.matrix('1.302277119864884753e+03,0.000000000000000000e+00,9.502486590818548393e+02;0.000000000000000000e+00,1.303466191765572148e+03,6.312575445467336976e+02;0.000000000000000000e+00,0.000000000000000000e+00,1.000000000000000000e+00')

dist = np.matrix('-4.024334822479178064e-01,2.120660026985363711e-01,-1.173992294609796892e-02,-6.449904424562102716e-03,-9.215752881837419030e-02')

# initialize the camera
cam = cv2.VideoCapture(0)   # 0 -> index of camera
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
s, img = cam.read()
if s:    # frame captured without any errors
#    namedWindow("cam-test",CV_WINDOW_AUTOSIZE)
#    imshow("cam-test",img)
#    waitKey(0)
#    destroyWindow("cam-test")
	dst = cv2.undistort(img, mtx, dist, None, mtx)
	cv2.imwrite(filename,img) #save image

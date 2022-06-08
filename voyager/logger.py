#!/usr/bin/env python3
from datetime import datetime
import time

cont = True
first = True

while (cont):
	now = datetime.utcnow()
	current_time = now.strftime("%Y-%m-%dT%H:%M:%S")
	#print("Current Time =", current_time)

	file1 = open("/home/joe/Code/logfile.txt", "a")  # append mode
	if first: 
		file1.write("Reboot\n")
		first = False
	file1.write(current_time)
	file1.write('\n')
	file1.close()
	time.sleep(300)

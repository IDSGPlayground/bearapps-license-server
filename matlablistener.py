#! /usr/bin/env python

import shutil
import matlabout
import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.bind("tcp://127.0.0.1:23272")
socket.setsockopt(zmq.SUBSCRIBE, "matlab")

while True:
    if socket.recv_unicode():
        print "Got MATLAB update notification!"
        matlabout.outputfile("../bearapps/bear_apps/db.sqlite")
        shutil.copy2("/usr/local/matlab/src/matlab.opt", "/usr/local/matlab/etc")
 

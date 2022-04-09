import time
import sys
import os
import datetime
import subprocess

# from shit and sticks

while True:
    try:
        exec(open("proto.py").read())
        time.sleep(1)
    except:
        err = sys.exc_info()[1]
        f1 = open("{}/err.txt".format(os.getcwd()), "a")
        f1.write("\n")
        f1.write(str(datetime.datetime.now()))
        f1.write("\n")
        f1.write("\n")
        f1.write(str(err))
        f1.write("\n")
        pass

import threading
import time
import subprocess
import os

groups = ["https://t.me/hiring_relocatin_hr_it", "https://t.me/withpublic_jobs"]


def run_get_info_from_groups(*my_args):
   print(''.join(my_args))
   # fix env issues
   # exec(open(os.getcwd() + "/parser.py").read())
   print('threared')


def open_tread(one_group):
   t = threading.Thread(target=run_get_info_from_groups, name=one_group.split('/')[-1], args=one_group)
   t.daemon = True
   t.start()


def thread_runer():
   for group in groups:
      open_tread(group)
      time.sleep(2)

if __name__ == '__main__':
   thread_runer()
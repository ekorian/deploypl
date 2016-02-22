"""
daemon.py

   Handle arguments, configuration file 

@author: K.Edeline
"""

import sys, os, time, atexit
from signal import SIGTERM
import logging
import logging.handlers

class Daemon(object):
   """
   Subclass Daemon class and override the run() method.
   """
   def __init__(self, pidfile='/var/run/mydaemon.pid', stdin='/dev/null', 
                     stdout='/var/log/deploypl.log', 
                     stderr='/var/log/deploypl.log', **kwargs): # TODO: replace with /dev/null
      super().__init__(**kwargs)
      self.stdin   = stdin
      self.stdout  = stdout
      self.stderr  = stderr
      self.pidfile = pidfile
     
 
   def daemonize(self):
      """
      Daemonize, do double-fork magic.
      """
      try:
         pid = os.fork()
         if pid > 0:
            # Exit first parent.
            sys.exit(0)
      except OSError as e:
         message = "Fork #1 failed: {}\n".format(e)
         sys.stderr.write(message)
         sys.exit(1)

      # Decouple from parent environment.
      os.chdir("/")
      os.setsid()
      os.umask(0)

      # Do the double fork, do the, do the double fork
      try:
         pid = os.fork()
         if pid > 0:
            # Exit from second parent.
            sys.exit(0)
      except OSError as e:
         message = "Fork #2 failed: {}\n".format(e)
         sys.stderr.write(message)
         sys.exit(1)

      # Write pidfile.
      pid = str(os.getpid())
      open(self.pidfile,'w+').write("{}\n".format(pid))

      # Register a function to clean up.
      atexit.register(self.delpid)

      # Redirects stdio
      self.redirect_fds()   
 
   def delpid(self):
      os.remove(self.pidfile)
 
   def start(self):
      """
      Start daemon.
      """
      # Check pidfile to see if the daemon already runs.
      try:
         pf = open(self.pidfile,'r')
         pid = int(pf.read().strip())
         pf.close()
      except IOError:
         pid = None
 
      if pid:
         message = "pid file {} already exist. Daemon already running?\n".format(self.pidfile)
         sys.stderr.write(message)
         sys.exit(1)
 
      # Start daemon.
      self.daemonize()
      self.run()
 
   def redirect_fds(self):
      """
      Redirect standard file descriptors.
      """
      sys.stdout.flush()
      sys.stderr.flush()
      si = open(self.stdin, 'r')
      so = open(self.stdout, 'a+')
      se = open(self.stderr, 'a+')
      os.dup2(si.fileno(), sys.stdin.fileno())
      os.dup2(so.fileno(), sys.stdout.fileno())
      os.dup2(se.fileno(), sys.stderr.fileno())

   def status(self):
      """
      Get status of daemon.
      """
      try:
         pf = open(self.pidfile,'r')
         pid = int(pf.read().strip())
         pf.close()
      except IOError:
         message = "There is no PID file. Daemon already running?\n"
         sys.stderr.write(message)
         sys.exit(1)
 
      try:
         procfile = open("/proc/{}/status".format(pid), 'r')
         procfile.close()
         message = "There is a process with pid {}\n".format(pid)
         sys.stdout.write(message)
      except IOError:
         message = "There is no process with pid {}\n".format(self.pidfile)
         sys.stdout.write(message)

      # TODO timestamp at startup and display uptime
 
   def stop(self):
      """
      Stop the daemon.
      """
      # Get the pid from pidfile.
      try:
         pf = open(self.pidfile,'r')
         pid = int(pf.read().strip())
         pf.close()
      except IOError as e:
         message = str(e) + "\nDaemon is not running\n"
         sys.stderr.write(message)
         sys.exit(1)

      # Try killing daemon process.
      try:
         os.kill(pid, SIGTERM)
         time.sleep(1)
      except OSError as e:
         print(str(e))
         sys.exit(1)
 
      try:
         if os.path.exists(self.pidfile):
            os.remove(self.pidfile)
      except IOError as e:
            message = str(e) + "\nCannot remove pid file {}".format(self.pidfile)
            sys.stderr.write(message)
            sys.exit(1)
 
   def restart(self):
      """
      Restart daemon.
      """
      self.stop()
      time.sleep(1)
      self.start()
 
   def run(self):
      """
      You should override this method when you subclass Daemon.
      It will be called after the process has been daemonized by start() or restart().

      Example:

      class MyDaemon(Daemon):
         def run(self):
             while True:
                 time.sleep(1)
      """
      pass



"""
daemon.py

    file Handle arguments, configuration

@author: K.Edeline
"""

import sys
import os
import time
import atexit
from signal import SIGTERM
import logging
import logging.handlers

class Launcher(object):
   """
   Launcher
   """
   def __init__(self):
      pass

class Daemon(object):
   """
   Spawn a double-forked daemon
   Subclass Daemon class and override the run() method.
   """
   def __init__(self, pidfile='/var/run/mydaemon.pid', stdin='/dev/null', 
                     stdout='/var/log/deploypl.log', 
                     stderr='/var/log/deploypl.log',
                     name='daemon', **kwargs): # TODO: replace with /dev/null
      super().__init__(**kwargs)
      self.stdin   = stdin
      self.stdout  = stdout
      self.stderr  = stderr
      self.pidfile = pidfile
      self.name    = name

      self.cwd     = os.getcwd()
 
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
      pid = self._open_pid()
      if pid:
         message = "pid file {} already exist, {} already running?\n".format(
                                                     self.pidfile, self.name)
         sys.stderr.write(message)
         return 1
 
      # Start daemon.
      self.daemonize()
      self.run()
      return 0
 
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

   def _open_pid(self, exit_on_error=False):
      """
      open the pid file and return the pid
      @return:
         pid the pid number
      """
      try:
         pf = open(self.pidfile,'r')
         pid = int(pf.read().strip())
         pf.close()
      except IOError as e:
         if exit_on_error:
            message = str(e) + "\n{} is not running\n".format(self.name)
            sys.stderr.write(message)
            sys.exit(1)      
         else:
            pid = None  

      return pid

   def status(self):
      """
      Get status of daemon.
      """
      pid = self._open_pid(exit_on_error=True)

      try:
         procfile = open("/proc/{}/status".format(pid), 'r')
         procfile.close()
         message = "{} running with pid {}\n".format(self.name, pid)
         sys.stdout.write(message)
         return 0
      except IOError:
         message = "no process with pid {}\n".format(self.pidfile)
         sys.stdout.write(message)

      return 1 

   def stop(self):
      """
      Stop the daemon.
      """
      pid = self._open_pid(exit_on_error=True)

      # Try killing daemon process.
      try:
         os.kill(pid, SIGTERM)
         time.sleep(1)
      except OSError as e:
         sys.stdout.write(str(e))
         return 1
 
      try:
         if os.path.exists(self.pidfile):
            os.remove(self.pidfile)
      except IOError as e:
         message = str(e) + "\nCannot remove pid file {}".format(self.pidfile)
         sys.stderr.write(message)
         return 1
      return 0
 
   def restart(self):
      """
      Restart daemon.
      """
      if self.stop() > 0:
         return 1
      time.sleep(1)
      if self.start() > 0:
         return 1
 
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



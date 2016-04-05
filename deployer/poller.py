"""
poller.py

   PL nodes

@author: K.Edeline
"""

import threading
import time

import pssh

from deployer.node import PLNodePool

class Poller(PLNodePool):
   """
   Poller

   """

   def __init__(self, daemon, rawfile=None, initial_delay=0, interval=3600):
      super(Poller, self).__init__(daemon, rawfile=rawfile)

      self.initial_delay = 0
      self.interval = interval
   
      self._uptime = time.time()

      # Ping service
      self.timer = threading.Timer(self.initial_delay, self.poll)
      # XXX one schedule.enter per state

   def uptime(self):
      return time.time() - self._uptime

   def run(self):
      self.timer.start()

   def poll(self):
      """
      Poll nodepool
      """      
      self.daemon.debug("polling ...")

      ## ping
      threads = [threading.Thread(target=node.ping()) for node in self.pool]
      for thread in threads:
          thread.start()
      for thread in threads:
          thread.join()
      ## ssh
   
      ## reseted, ro node ?


      ## if reseted or first time
      self.profile()

      # schedule next poll
      self.timer = threading.Timer(self.interval, self.poll)
      self.timer.start()

      self.daemon.debug("polling completed")

   def profile(self):
      """
      get kernel, distrib, ip, vsys, 
      check for broken packet manager (& fix)
      """
      pass

class PollerException(Exception):
   """
   PollerException(Exception)
   """

   def __init__(self, value):
      self.value = value

   def __str__(self):
      return repr(self.value)


"""
deloypl.py

   This file contains the PL deployer core.

@author: K.Edeline
"""
import sys
import os
import time

import http
from http import client

import deployer.node
from deployer.ios import IOManager
from deployer.daemon import Daemon
from deployer.poller import Poller

# XXX exceptino file ?

class PLDeployer(IOManager, Daemon):
   """
   PLDeployer
   
   """

   def __init__(self):
      super(PLDeployer, self).__init__(child=self, 
                              pidfile='/var/run/deploypl.pid',
                              stdout='/home/ko/Desktop/gits/own/deploypl/deploypl.log', 
                              stderr='/home/ko/Desktop/gits/own/deploypl/deploypl.log',
                              name='deploypl')
      self.load_inputs()
      
      self.pool = None # XXX fix name
      
   def _load_config(self):
      """
      Load configuration
      """
      self.plconfig = self.config["planet-lab.eu"]
      
      # PL settings
      self._nodedir = "/".join([self.cwd, self.config["core"]["nodes_dir"]])
      self._rawfile = "/".join([self._nodedir, self.config["core"]["raw_nodes"]])

   def load(self):
      """
      load at run time (not instantiation time)
      """
      self._load_config()
      self.load_outputs()

      self.pool = Poller(self, self._rawfile)

   def run(self):
      """      
      while True:
         self.error("loop")
         time.sleep(1)
      
      """
      # Load env
      self.load()
      self.debug(self.pool.status())
      self.debug("loading completed, starting to probe ...")
     
      self.pool.run()
      while True:
         self.error("loop")
         time.sleep(5)

      self.info("Deploying on slice "+self.config["planet-lab.eu"]["slice"])
      """"""

   def status_str(self, spaced=False):
      """
      Returns a string that describes current node pool state
      """
      status = self.pool.status()
      status_str = ""

      # Simply unroll dicts and print their content
      for key, count in status.items():
         status_str += key+":\n"
         for k, v in count:
            status_str += "  "+str(k)+": "+str(v)+"\n"
         if spaced:
            status_str += "\n"

      return status_str

   def status(self):
      """
      Print node pool status to stdout.
      """
      if Daemon.status(self) != 0:
         return 1
      
      # Load decoy logger
      self.load_outputs(decoy=True)

      # Load node pool & print status
      try:
         self.pool = Poller(self, None)      
         sys.stdout.write(self.status_str())
      except deployer.node.PLNodePoolException:
         sys.stdout.write("empty\n")

      return 0


      



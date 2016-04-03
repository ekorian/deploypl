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

from deployer.ios import IOManager
from deployer.daemon import Daemon
from deployer.node import PLNodePool

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
      
      self.pool = None
      
   def _load_config(self):
      """
      Load configuration
      """
      self.plconfig = self.config["planet-lab.eu"]
      
      # PL settings
      self._node_dir = "/".join([self.cwd, self.config["core"]["nodes_dir"]])
      self._raw_file = "/".join([self._node_dir, self.config["core"]["raw_nodes"]])

   def load(self):
      """
      load at run time (not instantiation time)
      """
      self._load_config()
      self.load_outputs()

      self.pool = PLNodePool(self, self._raw_file)
      

   def run(self):
      """      
      while True:
         self.error("loop")
         time.sleep(1)
      
      """
      # Load env
      self.load()
      self.info("Deploying on slice "+self.config["planet-lab.eu"]["slice"])
      self.info(self.pool.authorities())

      
      self.error("finshed")
      
      #self.debug("Found {} PLC and {} PLE nodes from raw nodes file".format())
      while True:
         self.error("loop")
         time.sleep(5)
      """"""

   def status_str(self):
      """
      Returns a string that describes current node pool state
      """
      status_str = str(self.pool.states())+"\n"
      status_str += str(self.pool.authorities())+"\n"
      return status_str

   def status(self):
      """
      Print node pool status to stdout.
      """
      if Daemon.status(self) != 0:
         return 1
      
      # Load decoy logger functions
      self.load_outputs(decoy=True)

      # Load node pool & print status
      self.pool = PLNodePool(self, None)      
      sys.stdout.write(self.status_str())
      return 0


      



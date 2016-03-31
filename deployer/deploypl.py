"""
deloypl.py

   This file contains the PL deployer core.

@author: K.Edeline
"""
import sys
import os
import time

import rpyc
import http
from http import client

from deployer.ios import IOManager
from deployer.daemon import Daemon
from deployer.node import PLNodePool
from deployer.status import start_status_service


class PLDeployer(IOManager, Daemon):
   """
   PLDeployer

   
   """
   def __init__(self):
      """

      """
      super(PLDeployer, self).__init__(child=self, 
                              pidfile='/var/run/deploypl.pid',
                              stdout='/home/ko/Desktop/gits/own/deploypl/deploypl.log', 
                              stderr='/home/ko/Desktop/gits/own/deploypl/deploypl.log',
                              name='deploypl')

      self.load_ios()
      self._load_config()

      self.pool = None

   def _load_config(self):
      """
      Load configuration
      """
      self.plconfig = self.config["planet-lab.eu"]
      
      # PL settings
      self._node_dir = "/".join([self.cwd, self.config["core"]["nodes_dir"]])
      self._raw_file = "/".join([self.__node_dir, self.config["core"]["raw_nodes"]])

      # daemon settings
      self.daemon_addr =     self.config["core"]["daemon_addr"]
      self.daemon_port = int(self.config["core"]["daemon_port"])

   def load(self):
      """
      load at run time (not instantiation time)
      """
      self.pool = PLNodePool(self._raw_file)

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

      start_status_service(self, self.daemon_addr, self.daemon_port)
      self.error("finshed")
      
      #self.debug("Found {} PLC and {} PLE nodes from raw nodes file".format())
      while True:
         self.error("loop")
         time.sleep(1)
      """"""

   def status_str(self):
      status_str = str(self.pool.states())+"\n"
      status_str +=
      return status_str

   def status(self):
      """
      Get status of daemon.
      """
      if Daemon.status(self) > 0:
         return 1
      
      status_service = rpyc.connect(self.daemon_addr, self.daemon_port)
      sys.stdout.write(status_service.root.status())
      



"""
deloypl.py

   This file contains the PL deployer core.

@author: K.Edeline
"""

import sys, os, time
import http

from http import client

from deployer.ios import IOManager
from deployer.daemon import Daemon

class PLDeployer(IOManager, Daemon):
   """
   PLDeployer

   
   """
   def __init__(self):
      """

      """
      super(PLDeployer, self).__init__(child=self, pidfile='/var/run/deploypl.pid')
      self.load_ios()

      #print(self.config["planet-lab.eu"])
      #print(self.config["planet-lab.eu"]["user"])
      self.plconfig = self.config["planet-lab.eu"]
      #print(self.config["core"])


   def run(self):
      """
      
      """
      self.info("Deploying on slice "+self.config["planet-lab.eu"]["slice"])


      http.client.HTTPConnection('planet-lab.eu')
      """
      while True:
         self.error("lopp")
         time.sleep(1)
      """
      self.error("finshed")

if __name__ == '__main__':
   pld = PLDeployer()
   pld.run()

"""
deloypl.py

   PL Deployer

@author: K.Edeline
"""
import sys
import time

from deployer.ios import IOManager
from deployer.daemon import Daemon
from deployer.poller import PLPoller
from deployer.node import PLNodeState, PLNodePool, PLNodePoolException

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

   def load(self):
      """
      load at run time (not instantiation time)
      
      """
      self.load_outputs()
      ## warning, ns lookups here
      self.pool = PLPoller(self, rawfile=self._rawfile, user=self.user, 
                               period=self.period, threadlimit=self.threadlimit,
                               sshlimit=self.sshlimit, plslice=self.slice,
                               initialdelay=self.initialdelay)
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

      # main loop
      time.sleep(self.initialdelay)
      while True:
         self.pool.poll()
         time.sleep(self.period)

      self.info("Deploying on slice "+self.config["planet-lab.eu"]["slice"])
      """"""

   def status_str(self, spaced=False):
      """
      Returns a string that describes current node pool state
      """
      if self.args.vverbose:
         ## Print profile of all nodes
         status = self.pool.status(string=True)

      elif self.args.verbose:
         ## Print profile of usable nodes
         status = self.pool.status(min_state=PLNodeState.usable, string=True)

      else:
         ## Print list of usable nodes
         attribute = "name" if self.args.names else "addr"
         nodes = self.pool._get(attribute, min_state=PLNodeState.usable)
         if len(nodes) > 0:
            status = "\n".join(nodes)+"\n"
         else:
            status = "No usable node found.\n"

      return status

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
         self.pool = PLNodePool(self)      
         sys.stdout.write(self.status_str())
      except PLNodePoolException:
         sys.stdout.write("No usable node found.\n")

      return 0


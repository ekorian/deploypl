"""
poller.py

   Poll nodes with ping, ssh and more

@author: K.Edeline
"""

import threading
import time
import sys

from pssh import ParallelSSHClient
from pssh.exceptions import AuthenticationException
from pssh.exceptions import ConnectionErrorException
from pssh.exceptions import UnknownHostException 
from pssh.exceptions import SSHException

from deployer.node import PLNodePool, PLNodeState
from deployer.ping import ping_process, ping_parse

# this lib is noisy
import logging
logging.getLogger("pssh").setLevel(logging.CRITICAL)

class Poller(PLNodePool):
   """
   Poller

   """

   def __init__(self, daemon, plslice=None, user=None, rawfile=None, 
                      initialdelay=0, period=3600,
                      threadlimit=10, sshlimit=10):
      super(Poller, self).__init__(daemon, rawfile=rawfile)

      self.initialdelay = 0
      self.period  = period
      self.threadlimit = threadlimit
      self.sshlimit = sshlimit
      self.user     = user
      self.slice    = plslice
      self._uptime  = time.time()

   def uptime(self):
      return time.time() - self._uptime

   def run(self):
      self.timer.start()

   def _ping(self):
      """
      ping in subprocess.Popen

      """
      self.daemon.debug("pinging ...")
      
      chunk_size = self.threadlimit
      addrs      = self._get("addr")
      states     = []

      for i in range(0, len(self.pool), chunk_size):
         chunk     = addrs[i:i+chunk_size]
         processes = []

         # Run a bunch of pings
         for addr in chunk:
            processes.append(ping_process(addr))

         # waits for them to complete and update nodes
         for process in processes:
            process.wait()
            ping_output = process.communicate()[0].decode('utf-8')
            result      = ping_parse(ping_output)
            answer      = 'received'
            
            # save result
            if result[answer] > 0:
               states.append(PLNodeState.reachable)
            else: 
               states.append(PLNodeState.unreachable)

      self._set("state", states)
      self.daemon.debug("ping completed")

   def _ssh_cmd(self, hosts, cmd, num_retries=3, timeout=10, sudo=False):
      """
      run bash command via ssh and return output dict
      """
      client = ParallelSSHClient(hosts, user=self.slice, pool_size=self.sshlimit, 
                                    num_retries=num_retries, timeout=timeout)
      try:
         output = client.run_command(cmd, stop_on_errors=False, sudo=sudo)
      except (AuthenticationException, ConnectionErrorException) as e: ## no ssh
         self.daemon.debug(e)
      except: ## bad connection prevents using ssh
         self.daemon.debug("SSH Error")
      del client

      return output

   def _ssh(self, num_retries=3, timeout=10):
      """
      ssh probe

      """

      ## Step 1. Establish ssh session
      hosts  = self._get("addr", min_state=PLNodeState.reachable)

      self.daemon.debug("ssh probing {} nodes via PL slice {} ...".format(
                        len(hosts), self.slice))
     
      output = self._ssh_cmd(hosts, "pwd")
      # if an ssh session was established, update node state
      for host, hostdata in output.items():
         if hostdata['exit_code'] != None: 
            self._set_node(host, "state", PLNodeState.accessible)
   
      self.daemon.debug("ssh probing completed")

   def _profile(self, num_retries=3, timeout=10):
      """
      get kernel, distrib, ip, vsys, 
      check for broken packet manager (& fix)
      """

      ## Step 2. Fingerprinting
      hosts = self._get("addr", min_state=PLNodeState.accessible)
      self.daemon.debug("start profiling {} ssh-accessible nodes".format(len(hosts)))
      output = self._ssh_cmd(hosts, "echo 'magic'; uname -sr; cat /etc/*-release | "
                                    "head -n 1; ls /vsys/;", sudo=True)

      self.daemon.error("output: {}".format(len(output)))
      for host, hostdata in output.items():
         profile = {}

         if hostdata['exit_code'] == 0:  

            # Some info about the node     
            stdout = hostdata['stdout']
            try:
               if "magic" in next(stdout):
                  profile["kernel"] = next(stdout)
                  profile["os"]     = next(stdout)
                  profile["vsys"]   = ("fd_tuntap.control" in next(stdout))
                  # exhausts generator
               for _ in stdout: pass
            except:
               #self.daemon.debug(profile)
               pass

            # Update node
            for k, d in profile.items():
               self._set_node(host, k, d)
            self._set_node(host, "state", PLNodeState.usable)

         else:
            self._set_node(host, "state", PLNodeState.reachable)

      ## Step 3. Find common bugs

      self.daemon.debug("node profiling completed")

   def poll(self):
      """
      Poll nodepool
      """
      start = time.time()      
      
      self._ping()
      self._ssh()   
      self._profile()

      ## XXX if reseted or first time

      # schedule next poll
      # XXX
      self.daemon.debug("polling completed")

      self.update()

      return time.time() - start


class PollerException(Exception):
   """
   PollerException(Exception)
   """

   def __init__(self, value):
      self.value = value

   def __str__(self):
      return repr(self.value)


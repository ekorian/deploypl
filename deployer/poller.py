"""
poller.py

   Poll nodes with ping, ssh and more

@author: K.Edeline
"""
import time

from deployer.node import PLNodePool, PLNodeState
from deployer.ping import ping_process, ping_parse
from deployer.ssh import run_command, download, upload

class PLPoller(PLNodePool):
   """
   PLPoller

   """

   def __init__(self, daemon, plslice=None, user=None, rawfile=None, 
                      initialdelay=0, period=3600,
                      threadlimit=10, sshlimit=10):
      super(PLPoller, self).__init__(daemon, rawfile=rawfile)

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

   def _run_command(self, hosts, cmd, timeout=10, sudo=False):
      return run_command(hosts, self.slice, cmd, timeout=timeout,
                                threads=self.sshlimit,
                                keyloc=self.daemon.sshkeyloc, sudo=sudo)

   def _ssh(self, timeout=10):
      """
      test if an ssh session can be established

      """

      ## Step 1. Establish ssh session
      hosts  = self._get("addr", min_state=PLNodeState.reachable)
      if len(hosts) == 0:
         self.daemon.debug("no reachable node found, stopping ...")
         return
      self.daemon.debug("ssh probing {} nodes via PL slice {} ...".format(
                        len(hosts), self.slice))
      output = self._run_command(hosts, "mkdir -p {}".format(self.user))

      # if an ssh session was established, update node state
      for hostdata in output:
         host = hostdata['host']
         if hostdata['status'] == 0:
            self._set_node(host, "state", PLNodeState.accessible)

      self.daemon.debug("ssh probing completed")

   def _profile(self, num_retries=3, timeout=10):
      """
      get kernel, distrib, ip, vsys, 
      check for broken packet manager (& fix)
      """

      ## Step 2. Fingerprinting
      hosts = self._get("addr", min_state=PLNodeState.accessible)
      if len(hosts) == 0:
         self.daemon.debug("no accessible node found, stopping ...")
         return

      self.daemon.debug("start profiling {} ssh-accessible nodes".format(len(hosts)))
      output = self._run_command(hosts, "echo 'magic'; uname -sr; "
                                        "cat /etc/*-release"
                                        " | head -n 1; sudo -S ls /vsys/;",
                                        timeout=30)
      for hostdata in output:
         host = hostdata['host']
         profile = {}

         if hostdata['status'] in [0,1,2,3,4,5]:

            # Some info about the node     
            stdout = hostdata['stdout'].splitlines()
            try:
               if "magic" in stdout[0]:
                  profile["kernel"] = stdout[1]
                  profile["os"]     = stdout[2]
                  profile["vsys"]   = ("fd_tuntap.control" in stdout[3])
            except: pass

            # Update node
            for k, d in profile.items():
               self._set_node(host, k, d)
            self._set_node(host, "state", PLNodeState.usable)

         else:
            self._set_node(host, "state", PLNodeState.accessible)

      ## Step 3. Finding common bugs (repo, ro system, )
      hosts = self._get("addr", min_state=PLNodeState.usable)
      if len(hosts) == 0:
         self.daemon.debug("no usable node found, stopping ...")

      self.daemon.debug("chasing bugs on {} nodes".format(len(hosts)))
      output = self._run_command(hosts, "yum install -y --nogpgcheck python",
                                    sudo=True, timeout=120)
      for hostdata in output:
         host = hostdata['host']

         if hostdata['status'] == 0:
            stdout = hostdata['stdout']
            #if "metalink" in stdout:
            #   self.daemon.debug("yum error") #XXX fix repo ?
            #   self.daemon.debug(str(hostdata))
         else:
            self.daemon.debug(str(hostdata))
            self._set_node(host, "state", PLNodeState.accessible)

      self.daemon.debug("node profiling completed")

   def poll(self):
      """
      Poll nodepool, retreive node pool status&profile and
      update database.
      """
      start = time.time()      
      
      self._ping()
      self.update()

      self._ssh()   
      self.update()

      self._profile()
      self.update()

      ## XXX if reseted or first time
      self.daemon.debug("polling completed")

      return time.time() - start

   def install_packages(self, pkgs):
      """
      install_packages
        
      @param pkgs list of yum packages         
      """
      pass

   def sync_data(self, dirloc):
      """
      sync_data

      @dirloc location of directory to be rsynced to all nodes
      """
      pass


class PLPollerException(Exception):
   """
   PLPollerException(Exception)
   """

   def __init__(self, value):
      self.value = value

   def __str__(self):
      return repr(self.value)


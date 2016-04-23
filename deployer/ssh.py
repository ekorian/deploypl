"""
ssh.py

   psshlib wrappers
      Each session is opened with subprocess.Popen
      useful functions: run_command, download, upload

@author: K.Edeline
"""

import os
import time

from psshlib import psshutil
from psshlib.manager import Manager, FatalError
from psshlib.task import Task

class SSHCmdTask(Task):

   def report(self, n):
      """
         Store a status report after the Task completes.

      """
      error  = ', '.join(self.failures)  
      tstamp = time.asctime().split()[3] # Current time
      host   = self.pretty_host
      self.result = {"tstamp": tstamp, "index": n, "host": host, 
                     "stdout": self.outputbuffer.decode('utf8'), 
                     "stderr" : self.errorbuffer.decode('utf8'),
                     "status" : self.exitstatus, "errors": error,
                     }

class SSHArgs:
   def __init__(self,d):
      ## don't use self.__dict__ here
      self._dict = d

   def __getattr__(self,key):
      try:
         return self._dict[key]
      except KeyError as err:
         raise AttributeError(key)
      
def upload(hosts, loginname, localdirs, remotedir, timeout=10, 
           threads=50, port=None, recursive=False, keyloc=None):

   opts = SSHArgs({'verbose': None, 'askpass': None, 'options': None, 
                   'errdir': None, 'timeout': timeout, 'recursive': recursive, 
                   'user': loginname, 'par': threads, 'extra': None, 
                   'outdir': None, 'host_strings': None})
   manager = Manager(opts)
   
   for host in hosts:
      cmd = ['scp', '-qC', '-o', 'StrictHostKeyChecking=no']
      if opts.options:
         for opt in opts.options:
             cmd += ['-o', opt]
      if keyloc:
         cmd.extend(['-i', keyloc])
      if port:
         cmd += ['-P', port]
      if opts.recursive:
         cmd.append('-r')
      if opts.extra:
         cmd.extend(opts.extra)
      cmd.extend(localdirs)
      cmd.append('%s@%s:%s' % (loginname, host, remotedir))

      t = SSHCmdTask(host, port, loginname, cmd, opts)
      manager.add_task(t)   

   # run tasks
   try:
      manager.run()
   except FatalError:
      return []
   
   # return result
   return [t.result for t in manager.done]

def download(hosts, loginname, remotedir, localdir, keyloc=None, localfile=".", timeout=10, threads=100, port=None, recursive=False):
   opts = SSHArgs({'verbose': None, 'askpass': None, 'options': None, 
                   'errdir': None, 'timeout': timeout, 'recursive': recursive, 
                   'user': loginname, 'par': threads, 'extra': None, 
                   'outdir': None, 'host_strings': None, 'localdir': None})
   # create directory
   for host in hosts:
      dirname = "%s/%s" % (localdir, host)
      if not os.path.exists(dirname):
         os.mkdir(dirname)

   manager = Manager(opts)
   for host in hosts:
      cmd = ['scp', '-qC', '-o', 'StrictHostKeyChecking=no']
      if opts.options:
         for opt in opts.options:
             cmd += ['-o', opt]
      if keyloc:
         cmd.extend(['-i', keyloc])
      if port:
         cmd += ['-P', port]
      if opts.recursive:
         cmd.append('-r')
      if opts.extra:
         cmd.extend(opts.extra)
      cmd.append('%s@%s:%s' % (loginname, host, remotedir))

      localpath = "%s/%s/%s" % (localdir, host, localfile)
      cmd.append(localpath)

      t = SSHCmdTask(host, port, loginname, cmd, opts)
      manager.add_task(t)

   # run tasks
   try:
      manager.run()
   except FatalError:
      return [] 

   return [t.result for t in manager.done]

def run_command(hosts, loginname, cmdline, keyloc=None, timeout=10, 
                                  threads=100, port=None, sudo=False):
   opts=SSHArgs({'send_input': None, 'par': threads, 'verbose': None, 
                 'inline_stdout': None, 'extra': None, 'askpass': None, 
                 'errdir': None, 'print_out': None, 'options': None, 
                 'user': loginname, 'timeout': timeout, 'inline': True, 
                 'host_strings': None, 'outdir': None})

   manager = Manager(opts)
   for host in hosts:
      cmd = ['ssh', host, '-o', 'NumberOfPasswordPrompts=1',
             '-o', 'StrictHostKeyChecking=no',
             '-o', 'SendEnv=PSSH_NODENUM PSSH_HOST']
      if keyloc:
         cmd.extend(['-i', keyloc])
      if opts.options:
         for opt in opts.options:
            cmd += ['-o', opt]
      if loginname:
         cmd += ['-l', loginname]
      if port:
         cmd += ['-p', port]
      if opts.extra:
         cmd.extend(opts.extra)
      if cmdline:
         _command = ""
         if sudo:
            _command = 'sudo -S '
         cmd.append(_command+cmdline)

      t = SSHCmdTask(host, port, loginname, cmd, opts, None)
      manager.add_task(t)

   # run tasks
   try:
      manager.run()
   except FatalError:
      return []
   
   return [t.result for t in manager.done]


"""
status.py

@author: K.Edeline
"""

import threading
import rpyc
from rpyc.utils.server import ThreadedServer
   

class PLDStatusService(rpyc.Service):
   """
   a rpyc status service
   """
   daemon = None

   def exposed_status(self):
      return self.daemon.status_str()

class PLDStatusServiceLauncher(threading.Thread):
   """
   Threaded PLDStatusService server
      @param addr the server address
      @param port the server port
      @param daemon must implement a status_str method
   """
   def __init__(self, daemon, addr, port):
      threading.Thread.__init__(self)

      self.daemon = daemon
      self.addr = addr
      self.port = port
      
   def run(self):
      """
      run a PLDStatusService server
      """
      PLDStatusService.daemon = self.daemon
      t = ThreadedServer(PLDStatusService, hostname=self.addr, port=self.port)
      t.start()     

def start_status_service(daemon, addr, port):
   """
   Start a threaded PLDStatusService server
   """
   pldssl = PLDStatusServiceLauncher(daemon, addr, port)
   pldssl.start()



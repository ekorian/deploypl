"""
ios.py

   Handle arguments, configuration file 

@author: K.Edeline
"""

import sys
import argparse
import configparser
import logging
import shutil

class IOManager(object):
   """

   extend me

   """
   #DEFAULT_CONFIG_LOC="/tmp/deploypl.ini"
   PKG_FILE = "packages.txt"

   def __init__(self, child=None, **kwargs):

      super().__init__(**kwargs)

      if child == None:
         raise IOSException("Child class not found")
      self.child    = child
      
      self.args   = None
      self.config = None
      self.logger = None

   def load_inputs(self):
      self.arguments()
      if "start" in self.args.cmd:
         self.configuration()

   def load_outputs(self, decoy=False):
      self.log(decoy=decoy)

   ########################################################
   # ARGPARSE
   ########################################################

   def arguments(self):
      """
      Parse arguments

         Used mostly to provide the location of the config file.
      """

      parser = argparse.ArgumentParser(description='PlanetLab C&C server')
      parser.add_argument('cmd', type=str,
                           choices=["start", "stop", "restart", "status"])

      parser.add_argument('-l' , '--log-file', type=str, default="deploypl.log",
                         help='log file location (default: deploypl.log)')
      parser.add_argument('-c' , '--config', type=str,
                         #default=IOManager.DEFAULT_CONFIG_LOC,
                         help='configuration file location')
      parser.add_argument('-d' , '--debug', action='store_true',
                         help='increase log output level')
      parser.add_argument('-v' , '--verbose', action='store_true',
                         help='status print node descriptions')
      parser.add_argument('-vv' , '--vverbose', action='store_true',
                         help='print info about non-usable nodes')
      parser.add_argument('-n' , '--names', action='store_true',
                         help='status print node names, not addresses')

      self.args = parser.parse_args()
      return self.args

   ########################################################
   # CONFIGPARSER
   ########################################################

   def configuration(self):
      """
      Parse configuration file
      """

      if self.args == None or self.args.config == None:
         raise IOSException("Arguments not found")

      self.config = configparser.ConfigParser()
      parsed      = self.config.read(self.args.config)
      if not parsed:
         print("Configuration file not found:", self.args.config)
         sys.exit(1)        

      # copy cfg file to /tmp/
      #if self.args.config != IOManager.DEFAULT_CONFIG_LOC:
      #   shutil.copyfile(self.args.config, IOManager.DEFAULT_CONFIG_LOC)
      # Load config
      self._load_config()
      return self.config

   def _load_config(self):
      """
      Load configuration
      """
      
      self.slice = self.config["core"]["slice"]
      self.user  = self.config["core"]["user"]
      
      # PL settings
      self._nodedir = self._to_absolute(self.config["core"]["nodes_dir"])
      self._datadir = self._to_absolute(self.config["core"]["data_dir"])
      self._logdir  = self._to_absolute(self.config["core"]["log_dir"])
      self._rawfile = self._to_absolute(self.config["core"]["raw_nodes"], 
                                          root=self._nodedir)
      self.userdir  = self._to_absolute(self.user, root=self._logdir)
      self.pkgfile  = self._to_absolute(IOManager.PKG_FILE, root=self.userdir)
      
      self.threadlimit  = int(self.config["core"]["thread_limit"])
      self.sshlimit     = int(self.config["core"]["ssh_limit"])
      self.sshkeyloc    =     self.config["core"]["ssh_keyloc"]
      self.period       = int(self.config["core"]["probing_period"])
      self.initialdelay =    (self.config["core"]["initial_delay"] == 'yes')

      self._package_list()

   def _package_list(self):
      """
      load pkg list from file
      """
      self.pkglist = []
      if not self.userdir:
         return
   
      def pkgs(line):
         return (line and not line.startswith(';'))
      
      with open(self.pkgfile, 'r') as f:
         lines        = map(str.rstrip, f.readlines())
         self.pkglist = list(filter(pkgs, lines))

   def _to_absolute(self, path, root=None):
      """
      Convert path to absolute if it's not already
      """
      if not path:
         return None
      if path.startswith("/"):
         return path
      if not root:
         root = self.cwd

      return "/".join([root, path])

   ########################################################
   # LOGGING
   ########################################################

   def log(self, decoy=False, console=False, logfile=True, errfile=False):
      """
      load logging facility

      """
      if decoy:
         decoy_logger  = lambda _ : None
         self.debug    = self.info     \
                       = self.warn     \
                       = self.error    \
                       = self.critical \
                       = decoy_logger
         return

      if self.args == None:
         raise IOManagerException("Arguments not found")
      if self.config == None:
         raise IOManagerException("Configuration not found")

      # create logger
      self.logger = logging.getLogger(self.child.__class__.__name__)
      self.logger.setLevel(logging.DEBUG)

      # console handler and set level to debug
      if console:
         ch = logging.StreamHandler()
         ch.setLevel(logging.INFO if self.args.debug else logging.ERROR)

      # XXX
      #filehandler = logging.handlers.TimedRotatingFileHandler('/tmp/daemon.log',
      #                                 when='midnight',interval=1,backupCount=10)
      # log file handler
      if logfile:
         fh = logging.FileHandler(self._to_absolute(self.args.log_file, 
                                                   root=self._logdir))
         fh.setLevel(logging.DEBUG if self.args.debug else logging.INFO)

      # error file handler
      if errfile:
         eh = logging.FileHandler(self._to_absolute(self.args.error_file, 
                                                   root=self._logdir))
         eh.setLevel(logging.ERROR)

      # add formatter to handlers & handlers to logger
      formatter = logging.Formatter("%(asctime)s : %(levelname)-5s : %(message)s",
                                    "%Y-%m-%d %H:%M:%S")
      if console:
         ch.setFormatter(formatter)
         self.logger.addHandler(ch)
      if logfile:
         fh.setFormatter(formatter)
         self.logger.addHandler(fh)
      if errfile:
         eh.setFormatter(formatter)
         self.logger.addHandler(eh)

      # log functions
      self.debug    = self.logger.debug
      self.info     = self.logger.info
      self.warn     = self.logger.warn
      self.error    = self.logger.error
      self.critical = self.logger.critical

      return self.logger

class IOManagerException(Exception):
   """
   IOManagerException(Exception)
   """
   def __init__(self, value):
      self.value = value

   def __str__(self):
      return repr(self.value)
      

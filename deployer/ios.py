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
   DEFAULT_CONFIG_LOC="/tmp/deploypl.ini"

   def __init__(self, child=None, **kwargs):

      super().__init__(**kwargs)

      if child == None:
         raise IOSException("Child class not found")
      self.child    = child
      
      self.args   = None
      self.config = None
      self.logger = None

   def load_ios(self):
      """
      load_ios
      
      Load all ios
      """
      self.arguments()
      self.configuration()
      if 'start' in self.args.cmd:
         self.log()

   ########################################################
   # ARGPARSE
   ########################################################

   def arguments(self):
      """
      Parse arguments

         Used mostly to provide the location of the config file.
      """

      parser = argparse.ArgumentParser(description='PlanetLab deployer')
      #parser.add_argument('username', nargs=1, help='PlanetLab username', type=str)
      #parser.add_argument('login', nargs=1, help='PlanetLab website username', type=str)
      #parser.add_argument('password', nargs=1, help='PlanetLab website password', type=str)
      parser.add_argument('cmd', help='start|stop|restart|status', type=str,
                           choices=["start", "stop", "restart", "status"])

      parser.add_argument('-l' , '--log-file', type=str, default="deploypl.log",
                         help='log file location (default: deploypl.log)')
      parser.add_argument('-e' , '--error-file', type=str, default="errors.log",
                         help='error file location (default: error.log)')

      parser.add_argument('-c' , '--config', type=str,
                         default=IOManager.DEFAULT_CONFIG_LOC,
                         help='configuration file location')
      parser.add_argument('-d' , '--debug', action='store_true',
                         help='increase output level') 

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
      if self.args.config != IOManager.DEFAULT_CONFIG_LOC:
         shutil.copyfile(self.args.config, IOManager.DEFAULT_CONFIG_LOC)

      return self.config

   ########################################################
   # LOGGING
   ########################################################

   def log(self, console=False, logfile=True, errfile=False):
      """
      load logging facility
      """
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

      # TODO
      #filehandler = logging.handlers.TimedRotatingFileHandler('/tmp/daemon.log',
      #                                 when='midnight',interval=1,backupCount=10)
      # log file handler
      if logfile:
         fh = logging.FileHandler(self.config["core"]["logging_dir"]+"/"+self.args.log_file)
         fh.setLevel(logging.DEBUG if self.args.debug else logging.INFO)

      # error file handler
      if errfile:
         eh = logging.FileHandler(self.config["core"]["logging_dir"]+"/"+self.args.error_file)
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



      

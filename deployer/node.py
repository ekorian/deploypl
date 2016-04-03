"""
node.py

   PL nodes

@author: K.Edeline
"""
import threading
import hashlib
import enum
import sys

from collections import Counter

from pkg_resources import resource_filename

import pssh
from sqlalchemy import MetaData, Table, Column
from sqlalchemy import Integer, String, Boolean, Enum
from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import mapper, relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
SQLITE_INT_MAX = 9223372036854775807

class PLNodeState(enum.Enum):
   """
   PLNodeState

   """
   ## usable, the node is accessible 
   usable      = 1

   ## accessible, ssh session was established to the node but one
   ## mighty PlanetLab bug prevents using it properly
   accessible  = 2

   ## reachable, the node is answering to ping requests
   ## but no ssh session can be established
   reachable   = 3

   ## unreachable, node is not answering ping requests, 
   ## probably offline or changed name
   unreachable = 4

   #def __str__(self):
   #   return self.name

class PLNode(Base):
   """
   PLNode
   
   """
   __tablename__  = "node"
   id        = Column(Integer, primary_key=True)
   name      = Column(String(255))
   authority = Column(String(4))
   state     = Column(Integer)
   kernel    = Column(String(255))
   os        = Column(String(255))
   vsys      = Column(Boolean)
   
   def __init__(self, name, authority, state=None):
      self.name      = name
      self.id        = self._id()
      self.authority = authority
      if state is None:
         self._state  = PLNodeState.unreachable
      else:
         self._state  = PLNodeState(state)

      self.kernel = "2.6"
      self.os     = "Ubuntu Saucy"
      self.vsys   = False
      self._update_state()
           
   def _update_state(self):
      self.state = self._state.value
      return self

   def _update_state_reverse(self):
      self._state = PLNodeState(self.state)
      return self

   def _id(self):
      return int(hashlib.sha1(bytes(self.name, "ascii")).hexdigest(), 
                                                     16) % SQLITE_INT_MAX

   def __str__(self):
      return "{} node {} is in state {}".format(self.authority, 
                                                self.name, 
                                                self._state)
   def __eq__(self, other):
      return (isinstance(other, self.__class__)
            and self.id == other.id)

   def __ne__(self, other):
        return not self.__eq__(other) 

class PLNodePool(object):
   """
   PLNodePool
   """

   def __init__(self, pld, raw_file, initial_delay=0, interval=3600):
      """
      
      @param raw_file contains copypaste of nodes listed in slice from PL website
      """
      self.pld = pld
      self.initial_delay = 0
      self.interval = interval
      self.pool = []

      # Init sqlite database
      db_loc = resource_filename(__name__, 'deploypl.sqlite')
      self.engine = create_engine('sqlite:////'+db_loc)#, echo=True)
      Base.metadata.create_all(self.engine)
      self.session = sessionmaker(self.engine)()

      # Load & merge node pools
      db_pool   = self._load_db()
      file_pool = self._load_raw(raw_file)
      self.pool = self._merge_pools(db_pool, file_pool)

      # If database is empty, save nodes
      if not db_pool and file_pool: 
         self._add_all()
         
      # Ping service
      self.timer = threading.Timer(self.initial_delay, self.poll)
      # XXX one schedule.enter per state

   def _merge_pools(self, db_pool, file_pool):
      """
      Merge node pools
      """
      if not db_pool and not file_pool:
         raise PLNodePoolException("Empty node pool")
      if not db_pool:
         self.pld.debug("read {} node entries from file".format(len(file_pool)))
         return file_pool
      if not file_pool:
         self.pld.debug("read {} node entries from db".format(len(db_pool)))
         return db_pool

      # Add new file nodes to db nodes
      new_nodes = []
      for file_n in file_pool:
         if file_n not in db_pool:
            new_nodes.append(file_n)

      self.pld.debug("read {} node entries from db and {} from file".format(
                                                            len(db_pool), 
                                                            len(new_nodes)))      
      return db_pool + new_nodes

   def _load_raw(self, raw_file):
      """
      Load nodes from raw file
      """
      pool = []
      if not raw_file:
         return pool

      # Load nodes from file
      with open(raw_file, 'r') as f:
         raw_nodes = map(str.split, f.readlines())
         for name, auth, state in raw_nodes:

            # keep only node with boot state
            if state == "boot":
               node = PLNode(name, auth)
               pool.append(node)
      return pool

   def _add_all(self):
      self.session.add_all(self.pool)
      self.session.commit()

   def _load_db(self):
      """
      Load nodes from database
      """
      query = self.session.query(PLNode).all()
      return [n._update_state_reverse() for n in query]

   def run(self):
      self.timer.start()

   def poll(self):
      """
      Poll nodepool
      """      
      ## ping

      ## ssh
   
      ## reseted, ro node ?


      ## if reseted or first time
      self.profile()

      # schedule next poll
      self.timer = threading.Timer(self.interval, self.poll)
      self.timer.start()

   def profile(self):
      """
      get kernel, distrib, ip, vsys, 
      check for broken packet manager (& fix)
      """
      pass

   def states(self):
      """
      @return node state count as a list
      """
      return Counter([n._state for n in self.pool]).most_common()

   def authorities(self):
      """
      @return node auth count as a list
      """
      return Counter([n.authority for n in self.pool]).most_common()

   def __str__(self):
      return "\n".join([str(node) for node in self.pool])


class PLNodePoolException(Exception):
   """
   PLNodePoolException(Exception)
   """

   def __init__(self, value):
      self.value = value

   def __str__(self):
      return repr(self.value)


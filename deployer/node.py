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
from contextlib import contextmanager
from pkg_resources import resource_filename

from sqlalchemy import MetaData, Table, Column
from sqlalchemy import Integer, String, Boolean, Enum
from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import mapper, relationship, sessionmaker
from sqlalchemy.orm.session import make_transient
from sqlalchemy.ext.declarative import declarative_base

from deployer.ping import ping
from deployer.resolver import AsyncResolver, is_valid_ipv4_address


Base = declarative_base()

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

   def __str__(self):
      return self.name

class PLNode(Base): #PLNodeBase
   """
   PLNode
   
   """

   # SQLAlchemy attributes
   __tablename__  = "node"
   id        = Column(Integer, primary_key=True)
   name      = Column(String(255))
   addr      = Column(String(64)) # XXX
   authority = Column(String(4))
   state     = Column(Integer)
   kernel    = Column(String(255))
   os        = Column(String(255))
   vsys      = Column(Boolean)
   #last_seen = Column(Time)

   @staticmethod
   def keys():
      """
      Returns a list of key attributes (keys)
      """
      keys = PLNode.__table__.columns.keys()
      keys.remove('id')
      keys.remove('addr')
      keys.remove('name') # XXX
      return keys
   
   def __init__(self, name, authority, state=None):
      self.name      = name
      self.id        = self._id()
      self.authority = authority

      if state is None:
         self._state  = PLNodeState.unreachable
      else:
         self._state  = PLNodeState(state)

      self.kernel    = "Unknown"
      self.os        = "Unknown"
      self.vsys      = False
      self.last_seen = None 
      self.addr      = None
   
      self._update_state()
           
   def _update_time(self):
      self.last_seen = time.time()

   def _update_state(self):
      self.state = self._state.value
      return self

   def _update_state_reverse(self):
      self._state = PLNodeState(self.state)
      return self

   def to_dict(self):
      return { "name"      : self.name,
               "authority" : self.authority,
               "state"     : self.state,
               "kernel"    : self.kernel,
               "os"        : self.os,
               "vsys"      : self.vsys,
             }

   def _id(self):
      return int(hashlib.sha1(bytes(self.name, "ascii")).hexdigest(), 
                                                     16) % (2**63 - 1)
   def __str__(self):
      return "{} node {} is in state {}".format(self.authority, 
                                                self.name, 
                                                self._state)
   def __eq__(self, other):
      return (isinstance(other, self.__class__)
            and self.id == other.id)

   def __ne__(self, other):
        return not self.__eq__(other) 

   def ping(self):
      # ping -q -w 5 -c 1
      result = ping(self.addr, deadline=5, count=1)
      answer = 'received'
      if answer in result and result[answer] > 0:

         # Got an answer, update node state
         self._update_time()
         if self.state == PLNodeState.unreachable:
            self.state = PLNodeState.reachable
      else:

         # No answer
         self.state = PLNodeState.unreachable  

@contextmanager
def session_scope(daemon, db_loc):
   """
   Provide a transactional scope around database operations.
   """
   daemon.root()

   engine = create_engine('sqlite:////'+db_loc)
   Base.metadata.create_all(engine)
   session = sessionmaker(engine)()
   session.expire_on_commit = False

   try:
      yield session
      session.commit()
   except:
      session.rollback()
      raise PLNodePoolException("Database error")
   finally:
      session.close()
      engine.dispose()

      daemon.drop_privileges()

class PLNodePool(object):
   """
   PLNodePool

   """

   def __init__(self, daemon, rawfile=None):
      """
      @param raw_file contains copypaste of nodes listed in slice from PL website
      """
      self.daemon = daemon
      self.pool = []

      self.db_loc = resource_filename(__name__, 'deploypl.sqlite')#XXX init without db
      
      self._merge(rawfile)

   def _merge(self, rawfile):
      """
      Load nodes from database, parse nodes from raw-nodes file,
      Add new nodes found from file to database nodes, update self.pool,
      and add new nodes to the database.
      """
      filepool = self._load_raw(rawfile)
      with session_scope(self.daemon, self.db_loc) as session:

         # Load & merge node pools
         dbpool   = self._load_db(session)
         newnodes = self._merge_pools(dbpool, filepool)

         # Save new nodes to db
         session.add_all(newnodes)

   def _lookup(self, pool):
      """
      Resolve names of node from pool

      """
      if not pool:
         return []

      # Queries
      self.daemon.debug("Performing {} DNS lookups".format(len(pool)))
      names = [node.name for node in pool]
      resolver = AsyncResolver(names)
      res = resolver.resolveA()

      # Filter out invalid addresses
      for node in pool:
         addr = res[node.name]
         if addr and is_valid_ipv4_address(addr):
            node.addr = addr

      validpool = list(filter(lambda n: n.addr != None, pool))
      self.daemon.debug("Received {} valid DNS responses".format(len(validpool)))

      return validpool

   def update(self):
      """
      update node table with nodes from pool

      @pre: all node from self.node are already present in the database
      """
      # Update database
      with session_scope(self.daemon, self.db_loc) as session:
         #dbpool   = self._load_db(session)
         for node in self.pool:
            node._update_state()
            session.query(PLNode).filter_by(id=node.id).update(node.to_dict())


   def _merge_pools(self, dbpool, filepool):
      """
      Merge node pools, returns nodes that were not present in db
      """
      if not dbpool and not filepool:
         raise PLNodePoolException("Empty node pool")

      # Add new file nodes to db nodes
      newnodes = []
      for filenode in filepool:
         if filenode not in dbpool:
            newnodes.append(filenode)

      self.daemon.debug("read {} node entries from db and {} from file".format(
                                                            len(dbpool), 
                                                            len(newnodes)))  
      # Lookup newnodes addresses
      newnodes = self._lookup(newnodes)    
      
      # Add newnodes to pool
      self.pool = dbpool + newnodes
      return newnodes

   def _load_raw(self, rawfile):
      """
      Load nodes from rawfile
      """
      pool = []
      if not rawfile:
         return pool

      # Load nodes from file
      with open(rawfile, 'r') as f:
         # Keep 3-tuples
         rawnodes = map(str.split, f.readlines())
         rawnodes = [x for x in rawnodes if x]

         for name, auth, state in rawnodes:
            # Keep nodes with boot state
            if state == "boot":
               node = PLNode(name, auth)
               pool.append(node)

      return pool

   def _load_db(self, session):
      """
      Load nodes from database
      """
      query = session.query(PLNode).all()
      return [n._update_state_reverse() for n in query]

   def status(self):
      """
      @return node state count as a list
      """
      attributes  = PLNode.keys()
      counterdict = {}
      pooldicts   = [n.to_dict() for n in self.pool]

      # count attributes
      for a in attributes:
         counterdict[a] = Counter([node[a] for node in pooldicts]).most_common()

      return counterdict

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


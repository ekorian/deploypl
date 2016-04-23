"""
node.py

   PL nodes

@author: K.Edeline
"""
import hashlib
import enum
import time
import sys

from datetime import datetime
from collections import Counter
from contextlib import contextmanager
from pkg_resources import resource_filename

from sqlalchemy import MetaData, Table, Column, DateTime
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.types import SchemaType, TypeDecorator
from sqlalchemy.types import Enum as SAEnum

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from deployer.resolver import AsyncResolver, is_valid_ipv4_address


Base = declarative_base()

class EnumType(SchemaType, TypeDecorator):
    def __init__(self, enum, name):
        self.enum = enum
        self.name = name
        members = (member.value for member in enum)
        kwargs = {'name': name}

        self.impl = SAEnum(*members, **kwargs)

    def _set_table(self, table, column):
        self.impl._set_table(table, column)

    def copy(self):
        return EnumType(self.enum, self.name)

    def process_bind_param(self, enum_instance, dialect):
        if enum_instance is None:
            return None

        return enum_instance.value

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        return self.enum(value)

class DBEnum(enum.Enum):
    def __init__(self, db_repr, description=None):
        if description is None:
            description = db_repr
            db_repr = self.name

        self._value_ = db_repr
        self.description = description

    @classmethod
    def as_type(cls, name):
        return EnumType(cls, name)

    @classmethod
    def get_description_mapping(cls):
        return dict((member.name, member.description) for member in cls)

## PLNodeState order for comparison
PLNodeState_order = {"unreachable" : 1,
                     "reachable"  : 2,
                     "accessible"  : 3,
                     "usable"      : 4
                     }

class PLNodeState(DBEnum):
   """
   PLNodeState

   XXX: when sqlalchemy 1.1 get released, replace by native
   Python34 enum support.
   """
   ## usable, the node is accessible 
   usable      = "usable"

   ## accessible, ssh session was established to the node but one
   ## mighty PlanetLab bug prevents using it properly
   accessible  = "accessible"

   ## reachable, the node is answering to ping requests
   ## but no ssh session can be established
   reachable   = "reachable"

   ## unreachable, node is not answering ping requests, 
   ## probably offline or changed name
   unreachable = "unreachable"

   def __str__(self):
      return self.name
   def __lt__(self, other):
      return PLNodeState_order[self.value] <  PLNodeState_order[other.value]
   def __le__(self, other):
      return PLNodeState_order[self.value] <= PLNodeState_order[other.value]
   def __gt__(self, other):
      return PLNodeState_order[self.value] >  PLNodeState_order[other.value]
   def __ge__(self, other):
      return PLNodeState_order[self.value] >= PLNodeState_order[other.value]

class PLNode(Base):
   """
   PLNode
   
   """
   ## SQLAlchemy attributes
   __tablename__  = "node"
   id        = Column(Integer, primary_key=True)
   name      = Column(String(255))
   addr      = Column(String(64))
   authority = Column(String(4))
   state     = Column(PLNodeState.as_type("state"), nullable=False)
   kernel    = Column(String(255))
   os        = Column(String(255))
   vsys      = Column(Boolean)
   last_seen = Column(DateTime)

   @staticmethod
   def columns(data_only=True):
      """
      Returns column names of data attributes (not indexes)
         Skips id, name, addr, last_seen
      """
      keys = PLNode.__table__.columns.keys()
      to_remove = ['id']
      if data_only:
         to_remove += ['addr', 'name', 'last_seen']
      return [c for c in keys if c not in to_remove]
   
   def __init__(self, name, authority, state=None):
      self.name      = name
      self.id        = self._id()
      self.authority = authority

      if state is None:
         self.state  = PLNodeState.unreachable
      else:
         self.state  = PLNodeState(state)

      ## set default node values
      self.kernel    = "UNKNOWN"
      self.os        = "UNKNOWN"
      self.last_seen = datetime(1, 1, 1, 0, 0)
      self.vsys      = False
      self.addr      = None

   def _update_time(self):
      self.last_seen = datetime.utcnow()

   def to_dict(self):
      d = {k : getattr(self, k) 
               for k in self.columns(data_only=False)}
      return d

   def update(self, to_update):
      """
      Update node state from value of to_update 
      @param to_update {'name': value}
      self.__dict__.update( kwargs )
      """
      for k, d in to_update.items():
         if "state" in k:
            self._update__state(d)
         setattr(self, k, d)
         
   def _update__state(self, state):
      """
      update node state and lastseen ts
      """
      if state > PLNodeState.unreachable:
         self._update_time()

   def _id(self):
      return int(hashlib.sha1(bytes(self.name, "ascii")).hexdigest(), 
                                                     16) % (2**63 - 1)
   def __str__(self):
      return "{} node {} is in state {}".format(self.authority, 
                                                self.name, 
                                                self.state)
   def __eq__(self, other):
      return (isinstance(other, self.__class__)
            and self.id == other.id)

   def __ne__(self, other):
        return not self.__eq__(other)  

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
      self.pool   = []
      self.db_loc = resource_filename(__name__, 'deploypl.sqlite')
      
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
      names    = [node.name for node in pool]
      resolver = AsyncResolver(names)
      res      = resolver.resolveA()

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
      with session_scope(self.daemon, self.db_loc) as session:
         for node in self.pool:
            session.query(PLNode).filter_by(id=node.id).update(node.to_dict())

      self.daemon.debug("database updated")

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
      return [n for n in query]

   def status(self, min_state=None, string=False):
      """
      @param min_state consider only node with state >= min_state
      @param string return status as a string

      @return node state count as a list

      """    
      if min_state != None:
         pool = self._filter_ge(min_state) 
      else:
         pool = self.pool

      attributes  = PLNode.columns()
      counterdict = {}
      pooldicts   = [n.to_dict() for n in pool]

      # count attributes
      for a in attributes:
         counterdict[a] = Counter([node[a] for node in pooldicts]).most_common()

      if string:
         status_str = self._status_tostr(counterdict)
         if not status_str:
            return "No {} node found.\n".format(str(min_state) 
                                                if min_state else "reachable")
         else:
            return status_str

      return counterdict

   def _status_tostr(self, status, spaced=False):
      """
      convert status to string
      """
      status_str = ""
      for key, count in status.items():
         status_str += key+":\n"
         if not count:
            return None
         for k, v in count:
            status_str += "  "+str(k)+": "+str(v)+"\n"
         if spaced:
            status_str += "\n"

      return status_str

   def __str__(self):
      return "\n".join([str(node) for node in self.pool])

   def _filter_eq(self, state):
      return list(filter(lambda n: n.state == state, self.pool))

   def _filter_ge(self, state):
      return list(filter(lambda n: n.state >= state, self.pool)) 

   def _set(self, attribute, attributelist):
      """
      Set 'attribute' with value from 'attributelist'.
      'attributelist' must be ordered like self.pool
      """
      assert len(self.pool) == len(attributelist)
      for i, value in enumerate(attributelist):
         self.pool[i].update({attribute: value})

   def _set_node(self, addr, attribute, value):
      """
      Set 'attribute' value of node with addr 'addr' to 'value'.
      
      """
      for node in self.pool:
         if node.addr == addr:
            node.update({attribute: value})
            break

   def _update_pool(self, dictlist, min_state=None, state=None):
      """
      map(node.update(), dictlist)
      'dictlist' must be ordered like self.pool

      @param min_state consider only node with state >= min_state
      """
      pool = self.pool
      if min_state != None:
         pool = self._filter_ge(min_state)
      elif state != None:
         pool = self._filter_eq(state)

      assert len(dictlist) == len(pool)
      for i, d in enumerate(dictlist):
         pool[i].update(d)

   def _get(self, attribute, min_state=None, state=None):
      """
      @param min_state consider only node with state >= min_state

      @return a list of nodes 'attribute'
      """
      pool = self.pool
      if min_state != None:
         pool = self._filter_ge(min_state)
      elif state != None:
         pool = self._filter_eq(state)

      return [getattr(node, attribute) for node in pool]

class PLNodePoolException(Exception):
   """
   PLNodePoolException(Exception)
   """

   def __init__(self, value):
      self.value = value

   def __str__(self):
      return repr(self.value)


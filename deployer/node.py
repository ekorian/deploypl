"""
node.py

   PL nodes

@author: K.Edeline
"""

from enum import Enum
from collections import Counter

class PLNodeState(Enum):
   """
   PLNodeState

   """
   ## usable means the node is accessible 
   usable      = 1

   ## accessible means that an ssh was established to the node, but one of
   ## the mighty PlanetLab bugs prevent its use
   accessible  = 2

   ## reachable means that the node is answering to ping requests, 
   ## but no ssh session can be established
   reachable   = 3

   ## unreachable means that node is not answering ping requests, 
   ## probably offline or changed name
   unreachable = 4

   def __str__(self):
      return self.name

class PLNode(object):
   """
   PLNode
   
   """
   def __init__(self, name, authority, state=None):
      self.name      = name
      self.authority = authority
      if state is None:
         self.state     = PLNodeState.unreachable
      else:
         self.state     = PLNodeState(state)
      
   def __str__(self):
      return "{} node {} is in state {}".format(self.name, self.authority, self.state)

class PLNodePool(object):
   """
   PLNodePool
   """

   def __init__(self, raw_file):
      """
      
      @param raw_file contains copypaste of nodes listed in slice from PL website
      """
      self.pool = []

      # Add nodes to pool
      with open(raw_file, 'r') as f:
         raw_nodes = map(str.split, f.readlines())
         for name, auth, state in raw_nodes:

            # keep only node with boot state
            if state == "boot":
               node = PLNode(name, auth)
               self.pool.append(node)

      
   def states(self):
      """
      @return node state count as a list
      """
      return Counter([n.state for n in self.pool]).most_common()

   def authorities(self):
      """
      @return node auth count as a list
      """
      return Counter([n.authority for n in self.pool]).most_common()

   def __str__(self):
      return "\n".join([str(node) for node in self.pool])





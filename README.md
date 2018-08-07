# deploypl
   **PlanetLab deployer**
   - Maintains active node pool
   - Node profiling
  
## Getting started quickly

   - Modify deploypl.ini with your own informations
   - Go to the planetlab website you registered to and copypaste the nodes listed in boot state to nodes/raw-nodes.txt
   - Start the daemon: $ sudo deploypl start -c deploypl.ini
   - Wait a few minutes
   - $ deploypl status [-v] [-vv]


## Dependencies
   - sqlalchemy
   - pssh (pip install pssh or git clone http://code.google.com/p/parallel-ssh/)
   - adns, python3-adns (https://github.com/trolldbois/python3-adns/)

## Sample output
##### List nodes in usable state 
    ko@ko:~/$ deploypl status

    1.2.3.4
    1.2.3.5
    .
    .
    1.2.3.254
    1.2.3.255


##### Print profiles of nodes in usable state (kernel, authority, etc)
    ko@ko:~/$ deploypl status -v

    authority:
      PLC: 96
      PLE: 17
    vsys:
      False: 6
      True: 107
    kernel:
      Linux 2.6.32-20.planetlab.i686: 84
      Linux 2.6.32-36.onelab.x86_64: 7
      Linux 2.6.27.57-33.planetlab: 6
      Linux 2.6.32-36.onelab.i686: 6
      Linux 2.6.32-131.vs230.web10027.xidmask.2.mlab.i686: 5
      Linux 3.11.10-100.fc18.x86_64: 2
      Linux 2.6.32-34.planetlab.x86_64: 1
      Linux 4.1.8-200.fc22.x86_64: 1
      Linux 4.2.5-201.fc22.x86_64: 1
    os:
      Fedora release 8 (Werewolf): 91
      Fedora release 14 (Laughlin): 9
      Fedora release 12 (Constantine): 8
      CentOS release 6.4 (Final): 5
    state:
      usable: 113

##### Print profiles of all nodes
    ko@ko:~/$ deploypl status -vv

    authority:
      PLC: 456
      PLE: 72
    vsys:
      False: 419
      True: 109
    kernel:
      Linux 2.6.32-20.planetlab.i686: 86
      Linux 2.6.32-36.onelab.x86_64: 7
      Linux 2.6.27.57-33.planetlab: 6
      Linux 2.6.32-36.onelab.i686: 6
      Linux 2.6.32-131.vs230.web10027.xidmask.2.mlab.i686: 5
      Linux 3.11.10-100.fc18.x86_64: 2
      Linux 2.6.32-34.planetlab.x86_64: 1
      Linux 4.1.8-200.fc22.x86_64: 1
      Linux 4.2.5-201.fc22.x86_64: 1
      UNKNOWN: 413
    os:
      Fedora release 8 (Werewolf): 93
      Fedora release 14 (Laughlin): 9
      Fedora release 12 (Constantine): 8
      CentOS release 6.4 (Final): 5
      UNKNOWN: 413
    state:
      unreachable: 285
      reachable: 125
      usable: 113
      accessible: 5


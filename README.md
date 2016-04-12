# deploypl
   **PlanetLab deployer**
   - Maintains active node pool
  
## Getting started quickly

   - Modify deploypl.ini with your own informations
   - Go to the planetlab website you registered to and copypaste the nodes listed in boot state to nodes/raw-nodes.txt
   - Start the daemon: $ sudo deploypl start -c deploypl.ini
   - Wait a few minutes
   - $ deploypl status [-v] [-vv]


## Dependencies
   - sqlalchemy
   - pssh (pip install pssh or git clone http://code.google.com/p/parallel-ssh/)
   - python3-adns (pip install adns)

## Sample output
    

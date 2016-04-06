"""
ping.py

   pinger module

@author: K.Edeline

"""
import re
import subprocess

_pingopt_count = "-c"
_pingopt_deadline = "-w"
_pingopt_quiet = "-q"

regex1 = re.compile(r'PING ([a-zA-Z0-9.\-]+) \(')
regex2 = re.compile(r'(\d+) packets transmitted, (\d+) received')
regex3 = re.compile(r'(\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)')

def ping_process(dipaddr, progname='ping', deadline=5, quiet=True, period=None, count=1):
   """
   return a ping subprocess.Popen

   """
   ping_argv = [progname]
   if quiet:
      ping_argv += [_pingopt_quiet]
   if period is not None:
      ping_argv += [_pingopt_period, str(period)]
   if count is not None:
      ping_argv += [_pingopt_count, str(count)]
   if deadline is not None:
      ping_argv += [_pingopt_deadline, str(deadline)]
   ping_argv += [str(dipaddr)]

   # Run subprocess
   try:
      p=subprocess.Popen(ping_argv, stdout=subprocess.PIPE)
   except subprocess.CalledProcessError: 
      pass   

   return p

def ping_parse(ping_output):
   """
   Parses the `ping_output` string into a dictionary containing the following
   fields:
     `host`: *string*; the target hostname that was pinged
     `sent`: *int*; the number of ping request packets sent
     `received`: *int*; the number of ping reply packets received
     `minping`: *float*; the minimum (fastest) round trip ping request/reply
                 time in milliseconds
     `avgping`: *float*; the average round trip ping time in milliseconds
     `maxping`: *float*; the maximum (slowest) round trip ping time in
                 milliseconds
     `jitter`: *float*; the standard deviation between round trip ping times
                 in milliseconds
   """
   
   host = _get_match_groups(ping_output, regex1)[0]
   sent, received = _get_match_groups(ping_output, regex2)

   try:
      minping, avgping, maxping, jitter = _get_match_groups(ping_output,
                                                           regex3)
   except:
      minping, avgping, maxping, jitter = ['NaN']*4

   return {'host': host, 'sent': int(sent), 'received': int(received), 
         'minping': minping, 'avgping': avgping, 'maxping': maxping,
         'jitter': jitter}


def _get_match_groups(ping_output, regex):
   match = regex.search(ping_output)
   if not match:
      raise Exception('Invalid PING output:\n' + ping_output)
   return match.groups()


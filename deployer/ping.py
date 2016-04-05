"""
ping.py

   pinger module

@author: K.Edeline
"""

import re
import sys
import subprocess
from subprocess import check_output

_pingopt_count = "-c"
_pingopt_deadline = "-w"
_pingopt_quiet = "-q"

def ping(dipaddr, progname='ping', deadline=5, quiet=True, period=None, count=1):
   output = _ping_process(dipaddr, progname=progname, deadline=deadline, 
                                   quiet=quiet, period=period, count=count)
   return _ping_parse(str(output))

def _ping_process(dipaddr, progname='ping', deadline=5, quiet=True, period=None, count=1):
   """
   subprocess ping

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

   return check_output(ping_argv)

def _ping_parse(ping_output): # ping $ADDR -q -w 3 -c 1
   """
   Parses the `ping_output` string into a dictionary containing the following
   fields:
     `host`: *string*; the target hostname that was pinged
     `sent`: *int*; the number of ping request packets sent
     `received`: *int*; the number of ping reply packets received
     `packet_loss`: *int*; the percentage of  packet loss
     `minping`: *float*; the minimum (fastest) round trip ping request/reply
                 time in milliseconds
     `avgping`: *float*; the average round trip ping time in milliseconds
     `maxping`: *float*; the maximum (slowest) round trip ping time in
                 milliseconds
     `jitter`: *float*; the standard deviation between round trip ping times
                 in milliseconds
   """

   matcher = re.compile(r'PING ([a-zA-Z0-9.\-]+) \(')
   host = _get_match_groups(ping_output, matcher)[0]

   matcher = re.compile(r'(\d+) packets transmitted, (\d+) received, (\d+)% packet loss')
   sent, received, packet_loss = _get_match_groups(ping_output, matcher)

   try:
      matcher = re.compile(r'(\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)')
      minping, avgping, maxping, jitter = _get_match_groups(ping_output,
                                                           matcher)
   except:
      minping, avgping, maxping, jitter = ['NaN']*4

   return {'host': host, 'sent': sent, 'received': received, 'packet_loss': packet_loss,
         'minping': minping, 'avgping': avgping, 'maxping': maxping,
         'jitter': jitter}


def _get_match_groups(ping_output, regex):
   match = regex.search(ping_output)
   if not match:
      raise Exception('Invalid PING output:\n' + ping_output)
   return match.groups()


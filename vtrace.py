#!/usr/bin/env python
# Monitor SolidFire volume performance.
# Copyright (c) 2018 Allan McAleavy
# Licensed under the Apache License, Version 2.0 (the "License")
from solidfire.factory import ElementFactory
from solidfire import common
import logging
import math
import argparse
from time import sleep, strftime
from termcolor import colored
import urllib3
urllib3.disable_warnings()
common.setLogLevel(logging.WARN)

# arguments
count = 60
interval = 1

examples = """examples:
    vtrace <array> <volume id> count interval 
"""
# arguments
parser = argparse.ArgumentParser(
    description="Gather performance data from SolidFire Arrays",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)
parser.add_argument("array", help="Please add Array")
parser.add_argument("volume", help="Please add volumeid")
parser.add_argument("interval", nargs="?", default=1,
    help="output interval, in seconds")
parser.add_argument("count", nargs="?", default=99999999,
    help="number of outputs")
args = parser.parse_args()

if str(args.array):
   array=args.array
if not str(args.array):
   exit

volume=int(args.volume)
interval=int(args.interval)
countdown = int(args.count)

array=args.array
try:
    sfe = ElementFactory.create(array, "<your username>", "<your password>")
except:
    print("Cant Connect to array %s" %(array))
    exit()

try:
   stat = sfe.get_volume_stats(volume)
except:
   print("Cant connect to volume id: %d on Array %s" %(volume,array))
   exit()

print('Tracing... Output every %d secs. Hit Ctrl-C to end' % interval)

exiting = 0

print ("%-12s %-12s  %-20s \t|%-10s %-8s %-10s %-10s %-12s %-13s %-6s %-10s %-8s %-8s %-8s %-8s %-5s %-5s" %
      ("TIME","SET MIN/MAX/BST","CUR MIN/MAX/BST","IOSIZE(kb)","IOPS","IOPSQOS","CURBW(MB)","BW_QOS(MB)","BURST_QOS(MB)","VUTIL%","BURSTCRED","RLT(us)","WLT(us)","LAT(us)","QDEPTH","IOQOS","BWQOS"))

while 1:
    try:
        sleep(interval)
    except KeyboardInterrupt:
        exiting = 1

    stat = sfe.get_volume_stats(volume)
    qos = sfe.list_volumes(volume).volumes[0]
    volstats = stat.volume_stats
    qos4io = colored('N    ','green')
    qos4bw = colored('N    ','green')

# get the upper bucket size

    hbsize=0
    if volstats.average_iopsize >0:
        hbsize = int(pow(2, math.ceil(math.log(volstats.average_iopsize, 2))))

# get lower bucket size = higher bucket size / 2
# Set minimums for IOPS < 4Kb

    lbsize = (hbsize /2)
    if lbsize < 4096:
        lbsize = 4096

    if hbsize < 4096:
        hbsize = 4096

    lbcost = qos.qos.curve[str(lbsize)]
    hbcost = qos.qos.curve[str(hbsize)]
    lbsize = lbsize / 1024
    hbsize = hbsize / 1024
    iosize = math.ceil(float(volstats.average_iopsize)/1024)
    costep = float(hbcost - lbcost ) / float(lbsize)
    curcost = ((iosize - lbsize)) * float(costep) + lbcost
    minlim = qos.qos.min_iops  * ( qos.qos.curve['4096'] )/ float(curcost)
    burstlim = qos.qos.burst_iops  * ( qos.qos.curve['4096'] )/ float(curcost)
    curlim = qos.qos.max_iops  * ( qos.qos.curve['4096'] )/ float(curcost)
    bwqos=(iosize * (float(100)/float(curcost) * qos.qos.burst_iops))

    if volstats.actual_iops >= curlim:
        qos4io=colored('Y    ','red')

    eqos=(iosize * curlim)
    cbw=(iosize *volstats.actual_iops)

    if cbw >0:
       if cbw >= eqos:
          qos4bw = colored('Y    ','red')
       if int(cbw) >= int(bwqos):
          qos4burst = colored('Y    ','red')

    print ("%-12s %d/%d/%d %d/%d/%-10d \t| %-10.0f %-8d %-10d %-10.0f %-12.0f %-13.0f %-6.2f %-10d %-8d %-8d %-8d %-8d %-5s %-5s" % (strftime("%H:%M:%S"),qos.qos.min_iops,
                                                                             qos.qos.max_iops,qos.qos.burst_iops,minlim,curlim,burstlim,iosize,
                                                                             volstats.actual_iops,
                                                                             curlim,
                                                                             cbw/1024,
                                                                             eqos/1024,
                                                                             bwqos/1024,volstats.volume_utilization *100,volstats.burst_iopscredit,
                                                                             volstats.read_latency_usec,volstats.write_latency_usec,volstats.latency_usec,
                                                                             volstats.client_queue_depth,qos4io,qos4bw))
    countdown -= 1
    if exiting or countdown == 0:
        print("Detaching...")
        exit()

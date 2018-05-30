#!/usr/bin/python
# Get QOS details for SolidFire I/O Sizes.
# Copyright (c) 2018 Allan McAleavy
# Licensed under the Apache License, Version 2.0 (the "License")


import collections
import math
import argparse

examples = """examples:
    ./table.py min_iops max_iops burst_iops
"""
# arguments
parser = argparse.ArgumentParser(
    description="Gather performance data from SolidFire Arrays",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)
parser.add_argument("min", default=1500, help="Min IOPS")
parser.add_argument("max", default=3000, help="Max IOPS")
parser.add_argument("burst",default=200000, help="Burst IOPS")
args = parser.parse_args()

min_iops=int(args.min)
max_iops=int(args.max)
burst_iops=int(args.burst)

costs = {4:100,8:160,16:270,32:500,64:1000,128:1950,256:3900,512:7600,1024:15000}
od = collections.OrderedDict(sorted(costs.items()))

print("%-8s %-8s %-8s %-8s %-8s %-8s %-8s %-8s " % ("IOSIZE","COST","MINIOPS","MAXIOPS","BIOPS","MINMB","MAXMB","BURSTMB"))
for average_iopsize in range(1,1025):
    hbsize=0
    if average_iopsize >=1:
       hbsize = int(pow(2, math.ceil(math.log(average_iopsize, 2))))
    if hbsize < 4:
       hbsize = 4

    lbsize = (hbsize /2)
    if lbsize < 4:
       lbsize = 4

    lbcost = od[lbsize]
    hbcost = od[hbsize]
    costep = float(hbcost - lbcost ) / float(lbsize)
    curcost = ((average_iopsize - lbsize) * costep) + lbcost
    print ("%-8d %-8d %-8.0f %-8.0f %-8.0f %-8.0f %-8.0f %-8.0f" % (average_iopsize,curcost,(float(100)/float(curcost) * min_iops),
                                             (float(100)/float(curcost)) * max_iops,(float(100)/float(curcost) * burst_iops),
                                             (average_iopsize * (float(100)/float(curcost) * min_iops))/1024,
                                             (average_iopsize * (float(100)/float(curcost) * max_iops))/1024,
                                             (average_iopsize * (float(100)/float(curcost) * burst_iops))/1024
                                              ))

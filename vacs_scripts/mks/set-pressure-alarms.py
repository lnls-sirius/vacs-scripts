#!/usr/bin/env python3
import argparse
from epics import caput

# bo-tb-ts-mks-pressure  si-mks-pressure
with open('bo-tb-ts-mks-pressure') as _f:
    pvs = [p.replace('\n','') for p in _f.readlines()]

for pv in pvs:
    caput('{}.HIGH'.format(pv), 1e-8, timeout=1)
    caput('{}.HIHI'.format(pv), 1e-7, timeout=1)


with open('si-mks-pressure') as _f:
    pvs = [p.replace('\n','') for p in _f.readlines()]

for pv in pvs:
    caput('{}.HIGH'.format(pv), 1e-9, timeout=1)
    caput('{}.HIHI'.format(pv), 1e-8, timeout=1)

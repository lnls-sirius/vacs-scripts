#!/usr/bin/env python3
import requests

res = requests.get("https://10.0.38.42/mgmt/bpl/getPVStatus?pv=SR-*SIPC*&reporttype=short", verify=False)
pvs = set()

for data in res.json():
    if data['status'] != 'Paused':
        pvs.add(data['pvName'].split(':')[0] + data['pvName'].split(':')[1])
print(pvs)
        

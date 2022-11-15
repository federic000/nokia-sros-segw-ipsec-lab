#!/bin/bash
# this script takes MAC-Addresses from the nodes in order to have the otg script working 

MAC1=`gnmic -a clab-segw-sros-01-sros4:57400 -u grpc -p ipsec-2022 --insecure get --path /state/port[port-id=1/1/3]/hardware-mac-address | grep -o -E "([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}"`

MAC2=`gnmic -a clab-segw-sros-01-srl3:57400 --skip-verify -u admin -p admin -e ascii get --path /interface[name=ethernet-1/5]/ethernet/hw-mac-address | grep -o -E "([[:xdigit:]]{2,2}:){5}[[:xdigit:]]{1,2}"`

printf "\n"
echo "MAC address for node sros4 port 1/1/3 = $MAC1 - MAC address for node srl3 interface e1/5 = $MAC2" 
echo "Usage example: ./otg-gtpv1-upanddown_v0.py 15000 30000 243 980 100 200 180 $MAC1 $MAC2"
printf "\n"


#!/usr/bin/env python3

# the script reads a csv file with useful data to setup static tunnels on a Nokia SR-OS router 
# then it uses gnmic tool to push configuration on the node.  
import sys
import time
import warnings
warnings.filterwarnings("ignore")
from timeit import default_timer as timer
import subprocess
import shlex
import csv 
import ipaddress 


def command_string_build_pub(csvinputfile, node_address, username, passwd, operation): 
    # function that builds the command line string by reading args from a csv file, PUBLIC SIDE of STATIC tunnel configuration.
    with open(csvinputfile, mode='r') as csv_file:
      csv_reader = csv.DictReader(csv_file)
      line_count = 0
      for row in csv_reader:
          if line_count == 0:
             print(f'Public side - file Column names are : {", ".join(row)}')
             line_count += 1
          clistring = []
          # interface name and addressing
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id"]}]/interface/interface-name --update-value {row["int_name"]}')
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id"]}]/interface[interface-name={row["int_name"]}]/ipv4/primary/address --update-value "{row["ip_address"]}" --update-path \
/configure/service/vprn[service-name={row["vprn_id"]}]/interface[interface-name={row["int_name"]}]/ipv4/primary/prefix-length --update-value {row["prefix_len"]}')
          # interface sap id 
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id"]}]/interface[interface-name={row["int_name"]}]/sap/sap-id --update-value tunnel-1.public:{row["sap_id_tg1"]}')
          # attach interface to OSPF instance 0 AREA 0, make it "passive"  
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id"]}]/ospf[ospf-instance=0]/area[area-id=0]/interface/interface-name --update-value {row["int_name"]}')
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id"]}]/ospf[ospf-instance=0]/area[area-id=0]/interface[interface-name={row["int_name"]}]/passive --update-value "true"')
          k = 0
          while k < len(clistring):
                print("PUB-SIDE pushing cli string: {}\n".format (clistring[k])) 
                config_push(clistring[k])
                time.sleep(0.5) # to be tuned in case of smaller/larger config push 
                k += 1 
          line_count += 1
      print(f'Total Processed {line_count -1} line(s) from the csv input file') 


def command_string_build_pri(csvinputfile, node_address, username, passwd, operation):
    # function that builds the command line string by reading args from a csv file, PRIVATE SIDE of STATIC tunnel configuration.
    with open(csvinputfile, mode='r') as csv_file:
      csv_reader = csv.DictReader(csv_file)
      line_count = 0
      for row in csv_reader:
          if line_count == 0:
             print(f'Private side - File Column names are {", ".join(row)}')
             line_count += 1
          clistring = []
          # security policy configuration with private(inner) IP addressing 
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/ipsec/security-policy/id --update-value {row["sec_pol_id"]}') 
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/ipsec/security-policy[id={row["sec_pol_id"]}]/entry/entry-id --update-value "10"')
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/ipsec/security-policy[id={row["sec_pol_id"]}]/entry[entry-id=10]/local-ip/address --update-value "{row["loc_ip_addr"]}"')
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/ipsec/security-policy[id={row["sec_pol_id"]}]/entry[entry-id=10]/remote-ip/address --update-value "{row["rem_ip_addr"]}"')
          # create interface with type "tunnel" 
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface/interface-name --update-value {row["int_name_priv"]} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/tunnel --update-value "true"')
          # create sap
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap/sap-id --update-value tunnel-1.private:{row["sap_id_tg1"]}')
          # create tunnel name instance
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap[sap-id=tunnel-1.private:{row["sap_id_tg1"]}]/ipsec-tunnel/name --update-value {row["tunn_name"]}')
          # dynamic keying and ike/esp policies  
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap[sap-id=tunnel-1.private:{row["sap_id_tg1"]}]/ipsec-tunnel[name={row["tunn_name"]}]/key-exchange/dynamic/ike-policy --update-value 1')
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap[sap-id=tunnel-1.private:{row["sap_id_tg1"]}]/ipsec-tunnel[name={row["tunn_name"]}]/key-exchange/dynamic/pre-shared-key --update-value testing123') 
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap[sap-id=tunnel-1.private:{row["sap_id_tg1"]}]/ipsec-tunnel[name={row["tunn_name"]}]/key-exchange/dynamic/ipsec-transform:::json:::[1]')
          # tunnel endpoint and delivery service
          # add +1 to 4th octet on TEIP address 
          ip_decimal = row["ip_address"]
          teip_pub = ipaddress.IPv4Address(ip_decimal)
          teip_prv = teip_pub+1 
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap[sap-id=tunnel-1.private:{row["sap_id_tg1"]}]/ipsec-tunnel[name={row["tunn_name"]}]/tunnel-endpoint/local-gateway-address --update-value {teip_prv} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap[sap-id=tunnel-1.private:{row["sap_id_tg1"]}]/ipsec-tunnel[name={row["tunn_name"]}]/tunnel-endpoint/remote-ip-address --update-value 18.19.20.1 --update \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap[sap-id=tunnel-1.private:{row["sap_id_tg1"]}]/ipsec-tunnel[name={row["tunn_name"]}]/tunnel-endpoint:::json:::\'{{"delivery-service":"100"}}\'')
          # apply security policy to tunnel 
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap[sap-id=tunnel-1.private:{row["sap_id_tg1"]}]/ipsec-tunnel[name={row["tunn_name"]}]/security-policy/id --update-value {row["sec_pol_id"]}')
          # enable the tunnel 
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/interface[interface-name={row["int_name_priv"]}]/sap[sap-id=tunnel-1.private:{row["sap_id_tg1"]}]/ipsec-tunnel[name={row["tunn_name"]}]/admin-state --update-value enable') 
          # add static routes for the IXIA-C to receive traffic
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/static-routes/route[ip-prefix={row["loc_ip_addr"]}][route-type=unicast]/next-hop[ip-address={row["ixia-ip1"]}]/admin-state --update-value enable')
          clistring.append(f'gnmic -a {node_address} -u {username} -p {passwd} --insecure {operation} --update-path \
/configure/service/vprn[service-name={row["vprn_id_priv"]}]/static-routes/route[ip-prefix={row["ixia-ip2"]}][route-type=unicast]/ipsec-tunnel[ipsec-tunnel-name={row["tunn_name"]}]/admin-state --update-value enable')
          k = 0
          while k < len(clistring):
                print("PRIV-SIDE pushing cli string: {}\n".format (clistring[k]))
                config_push(clistring[k])
                time.sleep(0.5) # to be tuned in case of smaller/larger config push  
                k += 1
          line_count += 1
      print(f'Processed {line_count -1} line(s) from the csv input file')


def config_push(command_string):
    # function that executes gnmic to push configuration on the node
    # shlex splits the command line strings into args for subprocess 
    command_line_gnmic = shlex.split(command_string) 
    process = subprocess.run(command_line_gnmic,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,
                     universal_newlines=True)
    print("standard output : - {}\n".format (process.stdout)) 
    if not process.stderr == "":
       print("standard error : - {}\n".format (process.stderr))


def main(inputfile):
    # main function...
    command_string_build_pub(inputfile, "172.20.20.6:57400", "grpc", "ipsec-2022", "set")
    command_string_build_pri(inputfile, "172.20.20.6:57400", "grpc", "ipsec-2022", "set")

if __name__ == "__main__":
    # starting point takes a csv filename as input 
    main(sys.argv[1])


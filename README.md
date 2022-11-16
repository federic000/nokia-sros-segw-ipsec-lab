# Security Gateway Lab based on Nokia SR-OS and Nokia SRL

what's a __SeGW__ is defined by 3GPP within the TS 33.210 specification. 

_"The border between the security domains is protected by Security Gateways (SEGs).The SEGs are responsible for enforcing the security policy of a security domain towards other SEGs in the destination security domain."_ 

In essence, SeGW is the IPSec termination point for the secured RAN traffic on 4G and 5G networks.  

## Lab info 

1. Runs on [Containerlab](https://github.com/srl-labs/containerlab) 
2. It heavily uses linux bridges for connectivity between containers so please set them up accordingly.  
3. Releases: SR-OS 22.10.R1 and SRL 22.6.4  
4. [IXIA-C-One](https://github.com/orgs/open-traffic-generator/packages/container/package/ixia-c-one) is also used to generate GTP traffic and send it across the SeGW cluster 
5. OTG API's allows for generate any kind of traffic with [snappi](https://github.com/open-traffic-generator/snappi), here GTPv1 is modeled to simulate typical RAN traffic.
6. Main purpose of the lab is for the network operators to be familair with new MC-IPsec N:M functionality 
7. N:M allows for the deployment of SeGW clusters, while offering full stateful redundancy for thousands of IPSec tunnels. 

A diagram of the setup is shown here: 

![a diagram is provided for reference](./docs/n2m_lab1.png)




### General setup 

Setup is made out of few nodes : 
- 3 Nokia SR-OS nodes, sros1-2 and 3, which are making up the SeGW cluster  
- 1 Nokia SR-OS node, sros4, used to establish tunnels 
- 2 Nokia SRL nodes, srl1-2, required to emulate an access network (public side, encrypted)
- 1 Nokia SRL node, srl3, required to emulate the core network (private side, clear-text) 
- 1 IXIA-C container node which provides for traffic generation to/from the core network to/from the access network 

### Deploying the lab 

Just run `clab deploy` in the working directory to startup the lab. 
To stop the lab, `clab destroy`. 

Startup takes some time depending on the hardware resources you have. SROS nodes startup is delayed too, to make it run smoother, feel free to edit the clab yml file based on your deployment scenario. When it's ready you should see something as:  

```
+---+--------------------------+--------------+------------------------------------------------------+---------------------+---------+----------------+----------------------+
| # |           Name           | Container ID |                        Image                         |        Kind         |  State  |  IPv4 Address  |     IPv6 Address     |
+---+--------------------------+--------------+------------------------------------------------------+---------------------+---------+----------------+----------------------+
| 1 | clab-segw-sros-01-ixia-c | c5706b2d0721 | ghcr.io/open-traffic-generator/ixia-c-one:0.0.1-3423 | keysight_ixia-c-one | running | 172.20.20.4/24 | 2001:172:20:20::4/64 |
| 2 | clab-segw-sros-01-srl1   | 763c7b8f5fb4 | ghcr.io/nokia/srlinux                                | srl                 | running | 172.20.20.7/24 | 2001:172:20:20::7/64 |
| 3 | clab-segw-sros-01-srl2   | 3f1f95ef1f4c | ghcr.io/nokia/srlinux                                | srl                 | running | 172.20.20.2/24 | 2001:172:20:20::2/64 |
| 4 | clab-segw-sros-01-srl3   | d03dd26e4e56 | ghcr.io/nokia/srlinux                                | srl                 | running | 172.20.20.8/24 | 2001:172:20:20::8/64 |
| 5 | clab-segw-sros-01-sros1  | 1fcb4e9d4f00 | vrnetlab/vr-sros:22.10.R1                            | vr-sros             | running | 172.20.20.9/24 | 2001:172:20:20::9/64 |
| 6 | clab-segw-sros-01-sros2  | 00e2d21680a7 | vrnetlab/vr-sros:22.10.R1                            | vr-sros             | running | 172.20.20.6/24 | 2001:172:20:20::6/64 |
| 7 | clab-segw-sros-01-sros3  | 2c3f1de6d76a | vrnetlab/vr-sros:22.10.R1                            | vr-sros             | running | 172.20.20.5/24 | 2001:172:20:20::5/64 |
| 8 | clab-segw-sros-01-sros4  | 9b327f51a6bd | vrnetlab/vr-sros:22.10.R1                            | vr-sros             | running | 172.20.20.3/24 | 2001:172:20:20::3/64 |
+---+--------------------------+--------------+------------------------------------------------------+---------------------+---------+----------------+----------------------+
```

### Accessing the network elements 

Containerlab provides for /etc/hosts configuration, so nodes can normally be accessed with `ssh -l admin clab-segw-sros-01-sros4`

### Configuration

For all the nodes, SR-OS and SRL configuration is already provided at startup. SR-OS nodes are configued in "mixed mode" to allow usage of both classic-cli and md-cli. 

#### Configuration details 

**L2** connectivity is built with bridges, this allows for usage of dot1q interfaces across all the nodes. 
**IP underlay** is made with OSPF, while L3-VPN servcies (VPRN) are connected by direct links (tagged VLANs) in the proper configuration context. 

For the details how node IGP's and routing, please have a look to configurations udner the configs folder. Please note: there could te configuration items which are unnecessary or partially done in some nodes. 

#### SeGW cluster 

As said above, the main purpose of this lab is to play with a new feature available in SR-OS, hereafter called N:M or N2M. 
N2M allows for the setup of a SeGW ipsec-domain, this is defined under the context `[gl:/configure redundancy multi-chassis]`, here all the peering nodes participating to ipsec-domain are configured and declared, roles, priority and bfd (optional) parameters must be defined here. 

For the details, please refer to official Nokia SR-OS documentation [here](https://documentation.nokia.com/sr/22-10/index.html) 

Other parts of configuration for nodes sros1-2-3-4
1. sros1-2-3 nodes belong to the same ipsec-domain "1", where sros1 has higher priority and it's the active main termination point for ipsec tunnels. 
2. sros2 is an active backup node for sros1, while sros3 is the "dormant" backup node. 
3. under steady conditions, tunnels are started from sros4 (no need to bring up tunnels, as soon as traffic is generated by ixia-c, tunnels will be brought up by sros4 automatically) and are managed by sros1. 
4. traffic flow follows this path 
- ixia-c pushes 2 flows, upstream and downstream. 
- on the upstream direction traffic flows from ixia-c -> sros4(encrypts) -> srl1-2 -> sros1 (or another node of the cluster, decrypts) and sends traffic to srl3 -> srl3 in turns sends traffic back to ixia-c closing the loop. 
- on the downstream: ixia-c -> srl3 -> sros1 (or another node if the cluster in case of failures, encrypts) -> srl1-2 -> sros4 (decrypts) -> traffic back to ixia-c   

### Traffic generation 

1. check required mac addresses by running the script `./otg-retrieve-mac-addresses.sh`, it uses [gNMIc](https://github.com/karimra/gnmic) to retrieve hw-mac-addresses. 
2. execute the suggested command line as `./otg-gtpv1-upanddown_v0.py 15000 30000 243 980 100 200 180 52:54:00:b6:3e:03 1A:EF:11:FF:00:05`




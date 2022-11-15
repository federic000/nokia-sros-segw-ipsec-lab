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
To stop the lab, `clab destroy`

### Accessing the network elements 

Containerlab provides for /etc/hosts configuration, so nodes can normally be accessed with `ssh -l admin clab-segw-sros-01-sros4`

### Configuration

For all the nodes, SR-OS and SRL configuration is already provided at startup. SR-OS nodes are configued in "mixed mode" to allow usage of both classic-cli and md-cli. 

### Traffic generation 

1. check required mac addresses by running the script `./otg-retrieve-mac-addresses.sh`, it uses gNMIc to retrieve hw-mac-addresses. 
2. execute the suggested command line as `./otg-gtpv1-upanddown_v0.py 15000 30000 243 980 100 200 180 52:54:00:b6:3e:03 1A:EF:11:FF:00:05`




#!/usr/bin/env python3
import snappi
import sys
import time
import decimal
from decimal import Decimal
import warnings
warnings.filterwarnings("ignore")
from timeit import default_timer as timer



def upstreamflow(dst_mac, size, pps, totpackets): 
    # port definition
    prt1 = config.ports.port(name='name-port1', location='eth1')[-1]
    prt2 = config.ports.port(name='name-port2', location='eth2')[-1]
    # flow definition
    flw = config.flows.flow(name='flw')[-1]
    flw.tx_rx.port.tx_name = prt1.name
    flw.tx_rx.port.rx_name = prt2.name
    flw.size.fixed = size
    flw.rate.pps = pps
    flw.duration.fixed_packets.packets = totpackets
    flw.metrics.enable = True
    # packet crafting: gtpv1 flow with variable teid
    eth1, ip1, udp1, gtp1 = flw.packet.ethernet().ipv4().udp().gtpv1()
    eth1.src.value, eth1.dst.value = "00:00:00:99:99:99", dst_mac
    ip1.src.values = ["172.16.146.10","172.16.147.10","172.16.148.10","172.16.149.10", "172.16.150.10"] 
    ip1.dst.values = ["200.0.0.14","200.0.0.13","200.0.0.12","200.0.0.11","200.0.0.10"]
    udp1.src_port.value = 2152
    udp1.dst_port.value = 2152
    gtp1.version.value = 1
    gtp1.protocol_type.value = 1
    gtp1.reserved.value = 1
    gtp1.message_length.value = 88
    gtp1.message_type.value = 255
    gtp1.teid.increment.start = 12345
    gtp1.teid.increment.step = 10
    gtp1.teid.increment.step = 500

def downstreamflow(dst_mac, size, pps, totpackets):
    # port definition downstream flow
    prt3 = config.ports.port(name='name-port3', location='eth1')[-1]
    prt4 = config.ports.port(name='name-port4', location='eth2')[-1]
    # flow definition
    flwd = config.flows.flow(name='flwd')[-1]
    flwd.tx_rx.port.tx_name = prt4.name
    flwd.tx_rx.port.rx_name = prt3.name
    flwd.size.fixed = size
    flwd.rate.pps = pps
    flwd.duration.fixed_packets.packets = totpackets
    flwd.metrics.enable = True
    # packet crafting: gtpv1 flow with variable teid
    eth1, ip1, udp1, gtp1 = flwd.packet.ethernet().ipv4().udp().gtpv1()
    eth1.src.value, eth1.dst.value = "00:00:00:98:98:98", dst_mac
    ip1.src.values = ["200.0.0.14","200.0.0.13","200.0.0.12","200.0.0.11","200.0.0.10"] 
    ip1.dst.values = ["172.16.146.10","172.16.147.10","172.16.148.10","172.16.149.10","172.16.150.10"]
    udp1.src_port.value = 2152
    udp1.dst_port.value = 2152
    gtp1.version.value = 1
    gtp1.protocol_type.value = 1
    gtp1.reserved.value = 1
    gtp1.message_length.value = 88
    gtp1.message_type.value = 255
    gtp1.teid.increment.start = 5678
    gtp1.teid.increment.step = 1
    gtp1.teid.increment.step = 500

def transmitter():
    print("Starting transmit on all configured flows ...")
    ts = api.transmit_state()
    ts.state = ts.START
    api.set_transmit_state(ts)

def stopper():
    print("Stopping transmit on all configured flows ...")
    ts = api.transmit_state()
    ts.state = ts.STOP
    api.set_transmit_state(ts)

def metrics_new(api, cfg):
    # create a port metrics request and filter based on port names
    req = api.metrics_request()
    req.port.port_names = [p.name for p in cfg.ports]
    # include only sent and received packet counts
    req.port.column_names = [req.port.FRAMES_TX, req.port.FRAMES_RX]
    # fetch port metrics
    res = api.get_metrics(req)
    # calc. upstream metrics
    total_tx_up = res.port_metrics[0].frames_tx
    total_rx_up = res.port_metrics[1].frames_rx
    expected_up = cfg.flows[0].duration.fixed_packets.packets  
    transmit_rate_port1_up = max(res.port_metrics[0].bytes_tx_rate,1) 
    receive_rate_port2_up = res.port_metrics[1].bytes_rx_rate
    kbps_tx_up = (transmit_rate_port1_up*8) / 1024
    kbps_rx_up = (receive_rate_port2_up*8) / 1024
    # calc. downstream metrics 
    total_tx_dw = res.port_metrics[3].frames_tx
    total_rx_dw = res.port_metrics[2].frames_rx
    expected_dw = cfg.flows[1].duration.fixed_packets.packets
    transmit_rate_port1_dw = max(res.port_metrics[3].bytes_tx_rate,1)
    receive_rate_port2_dw = res.port_metrics[2].bytes_rx_rate
    kbps_tx_dw = (transmit_rate_port1_dw*8) / 1024
    kbps_rx_dw = (receive_rate_port2_dw*8) / 1024
    delta_up = max(res.port_metrics[0].frames_tx - res.port_metrics[1].frames_rx, 0)
    delta_dw = max(res.port_metrics[3].frames_tx - res.port_metrics[2].frames_rx, 0)
    # print out metrics into columns 
    print("{:_<12} {:_<12} {:_<12} {:_<8} {:_<12.1f} {:_<10.1%} :: {:_<12} {:_<12} {:_<12} {:_<8} {:_<12.1f} {:_<8.1%}".format \
    (expected_dw, res.port_metrics[3].frames_tx, res.port_metrics[2].frames_rx, delta_dw, kbps_rx_dw, (1 * total_rx_dw/total_tx_dw), \
    expected_up, res.port_metrics[0].frames_tx, res.port_metrics[1].frames_rx, delta_up, kbps_rx_up, (1 * total_rx_up/total_tx_up)))
    # exits when #[max_packets] have been sent, either from UPstream or from DOWNstream flows.  
    max_pp = max(expected_dw, expected_up)
    if expected_dw > expected_up:
       if (total_tx_dw >= max_pp) and (total_tx_up >= expected_up): 
          print("\n-- flow(s) completed --\n");return True
    elif expected_dw < expected_up: 
         if (total_tx_up >= max_pp) and (total_tx_dw >= expected_dw):
            print("\n-- flow(s) completed --\n");return True        
    elif expected_dw == expected_up:
         if total_tx_up >= max_pp:
            print("\n-- up and downstream flows completed --\n");return True   

def wait_for(func, timeout, interval=0.33):
    start = time.time()
    try :
        while time.time() - start <= timeout:
              if func():
                return True
              time.sleep(interval)
    except KeyboardInterrupt:
        print("keyboard CTRL-C or Timeout occurred !")
        stopper()
    stopper()
    return False

def main(total_packets_up, total_packets_down, size_up, size_down, pps_up, pps_down, max_ela_time):
    ## upstream MAC addres of port 1/1/3 SeGW4-Helper node. 
    upstreamflow("52:54:00:f4:d5:03", size_up, pps_up, total_packets_up)
    ## downstream MAC address of port e1/5 of SRL3
    downstreamflow("1A:0A:11:FF:00:05", size_down, pps_down, total_packets_down)
    api.set_config(config) #push flows to ixia-c 
    transmitter() #start transmitting flows
    print("{:_<12} {:_<12} {:_<12} {:_<8} {:_<12} {:_<8} :: {:_<12} {:_<12} {:_<12} {:_<8} {:_<12} {:_<8}".format \
    ('DW.exp', 'DW.frame_tx', 'DW.frame_rx','Deltadw', 'DW.kbps_rx', 'DW.perc_rx', 'UP.exp', 'UP.frame_tx', 'UP.frame_rx', 'Deltaup','UP.kbps_rx', 'UP.perc_rx'))
    assert wait_for(lambda: metrics_new(api, config), max_ela_time), "cycle complete or Metrics validation failed!"
    print("-- test finished ! --\n")

if __name__ == "__main__":
    # input reads 7 args(integers) as tot packets up, tot packets down, packet_size for up and down, pps rate for up and down, max elapsed time
    n = len(sys.argv)
    if n != 8: 
       print ("7 args required : tot packets up, tot packets down, packet_size for up and down, pps rate for up and down, max elapsed time (all INTEGERS) \n")
       print ("e.g. : %s 1500 30000 243 980 100 200 180 \n" % sys.argv[0])  
       sys.exit() 
    print("\n args passed ->", end = " ")
    for i in range(1, n):
        print(sys.argv[i], end = " ")
    print("\n")
    # the setup of ixia-c api channel
    api = snappi.api(location='https://clab-segw-sros-01-ixia-c')
    config = api.config()
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]))



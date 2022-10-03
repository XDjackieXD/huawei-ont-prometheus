#!/usr/bin/env python3
import sys
import time
import telnetlib
import re
import prometheus_client

# "display optic" output example

#LinkStatus  : ok 
#Voltage      : 3322 (mV)
#Bias         : 13 (mA)
#Temperature  : 36 (C)
#RxPower      : -17.26 (dBm)
#TxPower      :  2.34 (dBm)
#RfRxPower    : -- (dBm)
#RfOutputPower: -- (dBmV)
#VendorName   : HUAWEI         
#VendorSN     : 1937WJ3xxxx   
#VendorRev    :
#VendorPN     : HW-BOB-0007     
#DateCode     : 191024

ont_host        = "192.168.100.1"
ont_user        = "root"
ont_password    = "admintelecom"

# Python method to test if a string is a float
def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

# Open telnet connexion
tn = telnetlib.Telnet(ont_host, 23, 5)
#tn.set_debuglevel(True)

# authentication
tn.read_until(b"Login:")
tn.write(ont_user.encode('ascii') + b"\n")
tn.read_until(b"Password:")
tn.write(ont_password.encode('ascii') + b"\n")
tn.read_until(b"WAP>")

prometheus_client.start_http_server(8000)
link_state = prometheus_client.Gauge('link_state', 'If the Link is up or down')
voltage = prometheus_client.Gauge('voltage', 'Internal system supply voltage in mV')
bias_current = prometheus_client.Gauge('bias_current', 'TX laser bias current in mA')
temperature = prometheus_client.Gauge('temperature', 'Internal temperature in °C')
rx_power = prometheus_client.Gauge('rx_power', 'Receive signal strength in dBm')
tx_power = prometheus_client.Gauge('tx_power', 'Transmit signal strength in dBm')

graphite_data = []

def update_data():
    # display optic stats
    tn.write(b"display optic\n")
    optic_stats = tn.read_until(b"WAP>", 10).decode()

    for line in optic_stats.split("\r\n"):
        # LinkStatus
        if line.startswith('LinkStatus'):
            re_val = re.compile("^LinkStatus  : (\S*)\s*$")
            result = re_val.match(line)[1]
            if str(result) == "ok":
                link_state.set(1)
            else:
                link_state.set(0)

        # Voltage
        elif line.startswith('Voltage'):
            re_val = re.compile("^Voltage      :\s*(\S*)\s*\(mV\)$")
            result = re_val.match(line)[1]
            if str(result).isdigit():
                voltage.set(int(result))

        # Bias Current
        elif line.startswith('Bias'):
            re_val = re.compile("^Bias         :\s*(\S*)\s*\(mA\)$")
            result = re_val.match(line)[1]
            if str(result).isdigit():
                bias_current.set(int(result))

        # Temperature
        elif line.startswith('Temperature'):
            re_val = re.compile("^Temperature  :\s*(\S*)\s*\(C\)$")
            result = re_val.match(line)[1]
            if str(result).isdigit():
                temperature.set(int(result))

        # RxPower
        elif line.startswith('RxPower'):
            re_val = re.compile("^RxPower      :\s*(\S*)\s*\(dBm\)$")
            result = re_val.match(line)[1]
            if isfloat(result):
                rx_power.set(float(result))

        # TxPower
        elif line.startswith('TxPower'):
            re_val = re.compile("^TxPower      :\s*(\S*)\s*\(dBm\)$")
            result = re_val.match(line)[1]
            if isfloat(result):
                tx_power.set(float(result))


while True:
    try:
        update_data()
    except:
        print('Error getting data from ONT, reopening Telnet connection...', file=sys.stderr)
        tn.close()
        time.sleep(5)

        # Open telnet connexion
        tn = telnetlib.Telnet(ont_host, 23, 5)
        #tn.set_debuglevel(True)

        # authentication
        tn.read_until(b"Login:")
        tn.write(ont_user.encode('ascii') + b"\n")
        tn.read_until(b"Password:")
        tn.write(ont_password.encode('ascii') + b"\n")
        tn.read_until(b"WAP>")

    time.sleep(60)

# disconnect
tn.write(b"quit\n")
tn.close()

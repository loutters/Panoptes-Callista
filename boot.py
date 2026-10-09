import wifimgr
import network
import time
import machine

try:
  import usocket as socket
except:
  import socket

# WiFi parameters
# ssid = 'YOUR-SSID'
# password = 'YOUR-PASSWORD'

# Define ESP32 name
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.config(dhcp_hostname = 'AstroWeatherStation')

# Comment to use standard WiFi connection
wlan = wifimgr.get_connection()

# Uncomment to use standard WiFi connection
# wlan.connect(ssid, password)
# t0 = time.time()
# while not wlan.isconnected():
#     print('.', end = " ")
#     time.sleep_ms(100)
#     if time.time()-t0 > 10:
#         machine.reset()

if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass 

# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print("Connection successful")
print('dhcp_hostname: {}'.format(wlan.config('dhcp_hostname')))
print('network config: ', wlan.ifconfig())
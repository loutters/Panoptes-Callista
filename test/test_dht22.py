from machine import Pin
from time import sleep
import math
import dht

sensor = dht.DHT22(Pin(0))

def dew_point(tc, rh):
    # tc: Temperature in Celsius
    # rh: Relative humidity
    # From: https://en.wikipedia.org/wiki/Dew_point#Calculating_the_dew_point
    b = 17.625
    c = 243.04 # degC
    gamma = math.log(rh/100) + b*tc/(c+tc)
    td = c*gamma/(b-gamma)
    return td

while True:
  try:
    sleep(1)     # the DHT22 returns at most 1 measurement every 2s
    sensor.measure()     # Recovers measurements from the sensor
    tc = sensor.temperature()
    rh = sensor.humidity()
    td = dew_point(tc, rh)
    print(f"Temperature : {tc:.1f}°C")
    print(f"Humidity    : {rh:.1f}%")
    print(f"Dew point   : {td:.1f}°C")
  except OSError as e:
    print("Failed reception")
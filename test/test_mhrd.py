from machine import Pin, ADC
import time

MHRDsensor = ADC(Pin(1))
MHRDsensor.width(ADC.WIDTH_12BIT)
MHRDsensor.atten(ADC.ATTN_11DB)

while True:
    rain = MHRDsensor.read()
    print(rain)
    time.sleep(2)
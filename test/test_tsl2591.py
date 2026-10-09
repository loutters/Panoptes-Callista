from machine import I2C, Pin
import tsl2591
import time

# ESP8266 sous MicroPython
i2c = I2C(0, sda=Pin(22), scl=Pin(23), freq=400_000)

tsl = tsl2591.TSL2591(i2c = i2c)

# To test saturation without auto-gain
# GAIN_LOW (1x ->115000lux)
# GAIN_MED (25x ->4600lux)
# GAIN_HIGH (428x ->270lux)
# GAIN_MAX (9876x ->6lux)
# tsl.gain = tsl2591.GAIN_LOW
# 100MS
# 200MS
# 300MS
# 400MS
# 500MS
# 600MS
# tsl.integration_time = tsl2591.INTEGRATIONTIME_100MS

while True:
    # To test saturation without auto-gain
#     try:
#         tsl_lux = tsl.lux
#     except RuntimeError: # Luminosity saturation
#         tsl_lux = -1

    tsl_lux = tsl.lux_auto_gain
    tsl_ir = tsl.infrared
    tsl_vis = tsl.visible
    tsl_full = tsl.full_spectrum
    print(f"{tsl_lux:.5f} lux | Gain: {tsl.gain}")
#     print(f" Infrared (0-65535)          : {tsl_ir:.5f}")
#     print(f" Visible (0-2147483647)      : {tsl_vis:.5f}")
#     print(f" Full spectrum (0-2147483647): {tsl_full:.5f}")
    time.sleep(1)

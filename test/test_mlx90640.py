import time
from machine import Pin, I2C
from mlx90640 import MLX90640, RefreshRate, init_float_array

i2c = I2C(0, sda=Pin(22), scl=Pin(23), freq=400000)
mlx = MLX90640(i2c)
mlx.refresh_rate = RefreshRate.REFRESH_2_HZ
frame = init_float_array(768)
while True:
    mlx.get_frame(frame)
    mlx.get_frame(frame)
    print(frame)
    time.sleep(2)
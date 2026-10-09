import time
import math
from machine import I2C, Pin, RTC, ADC

try:
  import usocket as socket
except:
  import socket
  
import dht
from mlx90640 import MLX90640, RefreshRate, init_float_array
import tsl2591

# To connect to weather station : http://astroweatherstation/index.html or http://10.42.0.126/index.html

# Define time
rtc = RTC()
# Initialize I2C
i2c = I2C(0, sda=Pin(22), scl=Pin(23), freq=400_000)
# DHT22 Temperature+Humidity
DHT22sensor = dht.DHT22(Pin(0))
# MLX90640 Infrared camera
MLX90640sensor = MLX90640(i2c)
MLX90640sensor.refresh_rate = RefreshRate.REFRESH_2_HZ
ir_frame = init_float_array(768)
# MH-RD Rain sensor
MHRDsensor = ADC(Pin(1))
MHRDsensor.width(ADC.WIDTH_12BIT)
MHRDsensor.atten(ADC.ATTN_11DB)
# TSL2591 luminosity
TSL2591 = tsl2591.TSL2591(i2c=i2c)
TSL2591.gain = tsl2591.GAIN_HIGH
TSL2591.integration_time = tsl2591.INTEGRATIONTIME_100MS

def dew_point(tc, rh):
    # tc: Temperature in Celsius
    # rh: Relative humidity
    b = 17.625
    c = 243.04 # degC
    gamma = math.log(rh/100) + b*tc/(c+tc)
    td = c*gamma/(b-gamma)
    return td

def cutout_frame(data, x, y, size_x, size_y, w=32, h=24):
    half_x = size_x // 2
    half_y = size_y // 2
    cut = []
    for i in range(-half_x, half_x + 1):
        for j in range(-half_y, half_y + 1):
            xi = min(max(x + i, 0), w - 1)
            yj = min(max(y + j, 0), h - 1)
            cut.append(data[w*yj + xi])
    return cut

def mean(l):
    n = len(l)
    m = 0
    for i in range(n):
        m += l[i]
    return m/n

# Establish connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(('', 80))
except OSError:
    continue
s.listen(5)

oldsec = -1
oldmins = -1
while True:
    # Get time
    tnow = rtc.datetime()
    year = str(tnow[0])
    month = str(tnow[1]) if tnow[1]>=10 else '0'+str(tnow[1])
    day = str(tnow[2]) if tnow[2]>=10 else '0'+str(tnow[2])
    hour = str(tnow[4]) if tnow[4]>=10 else '0'+str(tnow[4])
    minute = str(tnow[5]) if tnow[5]>=10 else '0'+str(tnow[5])
    sec = int(tnow[6]) if tnow[6]>=10 else '0'+str(tnow[6])
    str_date_time = f"{year}-{month}-{day}T{hour}:{minute}:{sec}"

    # Update every 10s
    if ((int(sec) - int(oldsec) > 10) or (minute != oldmins)):
        oldsec = sec
        oldmins = minute
        
        # DHT22 Temperature+Humidity
        DHT22sensor.measure()
        tc = DHT22sensor.temperature()
        rh = DHT22sensor.humidity()
        td = dew_point(tc, rh)

        # MLX90640 Infrared camera
        MLX90640sensor.get_frame(ir_frame)
        MLX90640sensor.get_frame(ir_frame) # Read twice to solve checkerboard issue
        ir_center = cutout_frame(ir_frame, 16, 12, 5, 5)
        temp_sky = mean(ir_center)
        # Heuristic to check in real conditions
        if (temp_sky < -8.):
            clouds = 0
        elif (temp_sky < 0.):
            clouds = (temp_sky + 8.)/8
        else:
            clouds = 1
            
        # MHRD Rain sensor
        rain_sens = MHRDsensor.read()
        if (rain_sens > 3_000):
            rain = 0
        elif (rain_sens > 2_800):
            rain = -(rain_sens - 3_000)/(3_000-2_800)
        else:
            rain = 1
            
        # TSL2591 luminosity
        tsl_lux = TSL2591.lux_auto_gain
        tsl_ir = TSL2591.infrared
        tsl_vis = TSL2591.visible
        tsl_full = TSL2591.full_spectrum
        
        # Write HTML file
        print(str_date_time)
        file = open("index.html", "w")
        file.write('<html>\n<head><title>AstroWeatherStation</title></head>\n<body>\n')
        file.write('timestamp=' + str_date_time + ' <br />\n')
        file.write(f"ir_sky={temp_sky:.2f} <br />\n")
        file.write(f"clouds={clouds:.2f} <br />\n") # WeatherWatcher keyword
#         file.write('forecast={0:.3f}'.format(clouds) + ' <br />\n') # WeatherWatcher keyword
        file.write(f"temperature={tc:.2f} <br />\n") # WeatherWatcher keyword
        file.write(f"humidity={rh:.2f} <br />\n") # WeatherWatcher keyword
        file.write(f"dew_point={td:.2f} <br />\n")
        file.write(f"rain_sensor={rain_sens:.0f} <br />\n")
        file.write(f"precip={rain:.2f} <br />\n") # WeatherWatcher keyword
#         file.write(f"wind={wind:.2f} <br />\n") # WeatherWatcher keyword
#         file.write(f"gust={gust:.2f} <br />\n") # WeatherWatcher keyword
#         file.write(f"pressure={pressure:.2f} <br />\n") # WeatherWatcher keyword
        file.write(f"luminosity={tsl_lux:.5f} <br />\n")
        file.write('</body>\n')
        file.write('<ir_image>\n')
        file.write(f"ir_image={str(ir_frame)} <br />\n")
        file.write('</ir_image>\n')
        file.write('</html>\n')
        file.close()

    # Upload file
    file = open("index.html", "r")
    response = file.read()
    file.close()
    
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.sendall(response)
    conn.close()
# Connect to Wi-Fi (hotspot)

import network, socket
import machine
import ujson
import time
from mqtt import MQTTClient
import config

# AP info
SSID = config.WIFI_SSID # Network SSID
KEY= config.WIFI_PASS  # Network key

PORT = 80
HOST = "www.google.com"

# Init wlan module and connect to network
print("Trying to connect. Note this may take a while...")

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)

# We should have a valid IP now via DHCP
print("Wi-Fi Connected ", wlan.ifconfig())

# Get addr info via DNS
addr = socket.getaddrinfo(HOST, PORT)[0][4]
print(addr)

# Create a new socket and connect to addr
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(addr)

# Set timeout
client.settimeout(3.0)

# Send HTTP request and recv response
client.send("GET / HTTP/1.1\r\nHost: %s\r\n\r\n"%(HOST))
print(client.recv(1024))

# Close socket
client.close()

# READING TEMPERATURE

import machine
import time
import array

adc_pin = machine.Pin(26) # A0
adc = machine.ADC(adc_pin)

# MQTT stuff
def sub_cb(topic, msg):
   print(msg)

# MQTT Setup
client = MQTTClient(config.SERIAL_NUMBER,
                    config.MQTT_BROKER,
                    user=config.TOKEN,
                    password=config.TOKEN,
                    port=config.PORT)
client.set_callback(sub_cb)
client.connect()
print('connected to MQTT broker')

# The MQTT topic that we publish data to
my_topic = config.TOPIC

# Storing ten values to take average

while True:
    i = 0
    degCelsiusAverage = [0,0,0,0,0,0,0,0,0,0]
    while i <= 9:
        i += 1
        
        reading = adc.read_u16()
        conversion_factor = 3.3/(65536) # convert the raw analog (16-bit) value (0-65535) to volts (3.3 is the supply voltage)
        # We want the volt-analog-digital ratio, that's why 3.3/65536.
        millivolts = reading * conversion_factor * 1000 # Convert volts to millovolts
        # We get the answer in volt per discrete value and multiply by 1000 to get milivolts.
        degCelsiusTemp = (millivolts - 500.0) / 10.0 # Convert millivolts to celsius
        # Math formula given in datasheet to get into Celsius.
        print("Temp number ", i, ": ", degCelsiusTemp)
        degCelsiusAverage[i-1] = degCelsiusTemp
        time.sleep_ms(500)
        
        if i == 10:
            sum = 0.0
            for x in degCelsiusAverage:
                sum += x
            average = sum/10
            print("Average of last 10 reads is: ", average)
            client.publish(topic=my_topic, msg=str(average))
            print("Average has been sent to cloud.")
                
        # It is fluctuating a lot so better to do an average of 10 to get more accurate results.

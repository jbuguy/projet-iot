import time
import smbus2
import bme280

# BME280 sensor address (default)
address = 0x76

# Initialize I2C bus
bus = smbus2.SMBus(1)

# Load calibration parameters
calibration_params = bme280.load_calibration_params(bus, address)

LED_PATH = "/sys/class/leds/ACT/brightness"

def led_on():
    with open(LED_PATH, "w") as f:
        f.write("1")

def led_off():
    with open(LED_PATH, "w") as f:
        f.write("0")


def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

try:
    while True:
        # Read sensor data
        data = bme280.sample(bus, address, calibration_params)

        temperature_celsius = data.temperature
        temperature_fahrenheit = celsius_to_fahrenheit(temperature_celsius)
        pressure = data.pressure
        humidity = data.humidity

        # Print readings
        print("Temperature: {:.2f} °C, {:.2f} °F".format(temperature_celsius, temperature_fahrenheit))
        print("Pressure: {:.2f} hPa".format(pressure))
        print("Humidity: {:.2f} %".format(humidity))

        # Control LED
        if temperature_celsius > 30:
            led_on()
            print("LED ON: Temperature above 30°C")
        else:
            led_off()
            print("LED OFF: Temperature below 30°C")

        # Wait for 5 minutes (300 seconds) before next reading
        time.sleep(5)

except KeyboardInterrupt:
    print('Program stopped by user')

except Exception as e:
    print('An unexpected error occurred:', str(e))


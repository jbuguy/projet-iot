from flask import Flask, jsonify, request
from picamera2 import Picamera2
import RPi.GPIO as GPIO
import smbus2
import bme280
from time import sleep, time
from datetime import datetime
import os

# --- Flask App ---
app = Flask(__name__)

# --- Pin Configuration ---
PINLED = 4
TRIG = 18
ECHO = 24
CLK_PIN = 12
WR_PIN = 27
RD_PIN = 17
INTR_PIN = 22
DATA_PINS = [5, 6, 13, 19, 26, 21, 20, 16]

# --- LED path for ACT LED control ---
LED_PATH = "/sys/class/leds/ACT/brightness"

# --- BME280 Setup ---
BME280_ADDRESS = 0x76
bus = smbus2.SMBus(1)
calibration_params = bme280.load_calibration_params(bus, BME280_ADDRESS)

# --- GPIO Initialization ---
def init_gpio():
    if not GPIO.getmode():
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(PINLED, GPIO.OUT)
        GPIO.setup(TRIG, GPIO.OUT)
        GPIO.setup(ECHO, GPIO.IN)
        GPIO.setup(CLK_PIN, GPIO.OUT)
        GPIO.setup(WR_PIN, GPIO.OUT)
        GPIO.setup(RD_PIN, GPIO.OUT)
        GPIO.setup(INTR_PIN, GPIO.IN)
        for pin in DATA_PINS:
            GPIO.setup(pin, GPIO.IN)

        GPIO.output(WR_PIN, GPIO.HIGH)
        GPIO.output(RD_PIN, GPIO.HIGH)

        global pwm
        pwm = GPIO.PWM(CLK_PIN, 640000)
        pwm.start(50)
        print("✅ GPIO initialized")

init_gpio()

# --- Camera ---
picam2 = Picamera2()
picam2.start()

# --- Utility Functions ---
def led_on():
    try:
        with open(LED_PATH, "w") as f:
            f.write("1")
        return True
    except Exception:
        GPIO.output(PINLED, GPIO.HIGH)
        return True

def led_off():
    try:
        with open(LED_PATH, "w") as f:
            f.write("0")
        return True
    except Exception:
        GPIO.output(PINLED, GPIO.LOW)
        return True

def led_status():
    try:
        with open(LED_PATH, "r") as f:
            return "on" if f.read().strip() == "1" else "off"
    except Exception:
        return "unknown"

def distance():
    init_gpio()
    GPIO.output(TRIG, True)
    sleep(0.00001)
    GPIO.output(TRIG, False)

    start_time = time()
    stop_time = time()

    while GPIO.input(ECHO) == 0:
        start_time = time()
    while GPIO.input(ECHO) == 1:
        stop_time = time()

    elapsed = stop_time - start_time
    dist = (elapsed * 34300) / 2
    return round(dist, 2)

def read_adc():
    init_gpio()
    GPIO.output(WR_PIN, GPIO.LOW)
    sleep(0.000001)
    GPIO.output(WR_PIN, GPIO.HIGH)

    timeout = time() + 0.001
    while GPIO.input(INTR_PIN) == GPIO.HIGH:
        if time() > timeout:
            return 0

    GPIO.output(RD_PIN, GPIO.LOW)
    sleep(0.000001)

    value = 0
    for i, pin in enumerate(DATA_PINS):
        if GPIO.input(pin):
            value |= (1 << i)

    GPIO.output(RD_PIN, GPIO.HIGH)
    return value

def get_gas_reading():
    samples = 5
    total = 0
    for _ in range(samples):
        total += read_adc()
        sleep(0.01)
    avg_value = total / samples
    voltage = (avg_value / 255.0) * 5.0
    percentage = (avg_value / 255.0) * 100
    return round(avg_value, 2), round(voltage, 2), round(percentage, 1)

def get_bme280_data():
    data = bme280.sample(bus, BME280_ADDRESS, calibration_params)
    temperature_c = data.temperature
    temperature_f = (temperature_c * 9 / 5) + 32
    pressure = data.pressure
    humidity = data.humidity
    return {
        "temperature_c": round(temperature_c, 2),
        "temperature_f": round(temperature_f, 2),
        "pressure_hpa": round(pressure, 2),
        "humidity_percent": round(humidity, 2),
    }

# --- API Routes ---
@app.route("/api/distance")
def api_distance():
    return jsonify({"distance_cm": distance()})

@app.route("/api/gas")
def api_gas():
    raw, voltage, pct = get_gas_reading()
    return jsonify({
        "raw": raw,
        "voltage": voltage,
        "level_percent": pct
    })

@app.route("/api/bme280")
def api_bme280():
    return jsonify(get_bme280_data())

@app.route("/api/status")
def api_status():
    d = distance()
    raw, voltage, pct = get_gas_reading()
    bme = get_bme280_data()
    return jsonify({
        "door_distance_cm": d,
        "gas_raw": raw,
        "gas_voltage": voltage,
        "gas_level_percent": pct,
        "temperature_c": bme["temperature_c"],
        "humidity_percent": bme["humidity_percent"],
        "pressure_hpa": bme["pressure_hpa"],
    })

@app.route("/api/capture", methods=["POST"])
def api_capture():
    now = datetime.now()
    filename = f"manual_capture_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
    picam2.capture_file(filename)
    return jsonify({"message": "Image captured", "file": filename})

@app.route("/api/led", methods=["GET"])
def api_led_status():
    return jsonify({"status": led_status()})

@app.route("/api/led/on", methods=["POST"])
def api_led_on():
    led_on()
    return jsonify({"message": "LED turned ON"})

@app.route("/api/led/off", methods=["POST"])
def api_led_off():
    led_off()
    return jsonify({"message": "LED turned OFF"})

@app.route("/")
def index():
    return jsonify({
        "message": "Raspberry Pi IoT API",
        "endpoints": [
            "/api/distance",
            "/api/gas",
            "/api/bme280",
            "/api/status",
            "/api/capture",
            "/api/led",
            "/api/led/on",
            "/api/led/off"
        ]
    })

# --- Cleanup Route (optional) ---
@app.route("/api/cleanup", methods=["POST"])
def api_cleanup():
    pwm.stop()
    GPIO.cleanup()
    return jsonify({"message": "GPIO cleaned up"})

if __name__ == "__main__":
    print("✅ Starting Flask REST API on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

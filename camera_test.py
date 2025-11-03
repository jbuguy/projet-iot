from picamera2 import Picamera2
import RPi.GPIO as GPIO
from time import sleep, time
from datetime import datetime

# Pins
PINLED = 4
TRIG = 18
ECHO = 24

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PINLED, GPIO.OUT)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Distance function
def distance():
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
    dist = (elapsed * 34300) / 2  # cm
    return dist

# Initialize camera once
picam2 = Picamera2()
picam2.start()

door_was_open = False  # event flag
daily_capture_done = False  # daily scheduled capture flag

# Set the scheduled capture time (24h format)
SCHEDULE_HOUR = 11
SCHEDULE_MINUTE = 43

try:
    while True:
        d = distance()
        now = datetime.now()

        # --- Door-triggered capture ---
        if d > 50. and not door_was_open:
            # Door just opened
            door_was_open = True
            GPIO.output(PINLED, GPIO.HIGH)
            print("Door opened! Taking picture...")
            sleep(0.5)
            picam2.capture_file(f"door_open_{now.strftime('%Y%m%d_%H%M%S')}.jpg")
            print("✅ Image saved!",d)
            GPIO.output(PINLED, GPIO.LOW)

        elif d <= 50. and door_was_open:
            # Door just closed
            door_was_open = False
            GPIO.output(PINLED, GPIO.HIGH)
            print("Door closed! Taking picture...")
            sleep(0.5)
            picam2.capture_file(f"door_close_{now.strftime('%Y%m%d_%H%M%S')}.jpg")
            print("✅ Image saved!",d)
            GPIO.output(PINLED, GPIO.LOW)

        # --- Scheduled daily capture ---
        if (now.hour == SCHEDULE_HOUR and now.minute == SCHEDULE_MINUTE and not daily_capture_done):
            print("Scheduled capture!")
            GPIO.output(PINLED, GPIO.HIGH)
            picam2.capture_file(f"scheduled_{now.strftime('%Y%m%d_%H%M%S')}.jpg")
            print("✅ Scheduled image saved!")
            GPIO.output(PINLED, GPIO.LOW)
            daily_capture_done = True

        # Reset daily flag after the scheduled minute passes
        if now.hour != SCHEDULE_HOUR or now.minute != SCHEDULE_MINUTE:
            daily_capture_done = False

        sleep(0.2)

except KeyboardInterrupt:
    print("Exiting program")

finally:
    GPIO.output(PINLED, GPIO.LOW)
    GPIO.cleanup()

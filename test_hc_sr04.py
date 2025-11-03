import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

TRIG = 18
ECHO = 24

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def distance():
    # Send 10us pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start_time = time.time()
    stop_time = time.time()

    # Save start time
    while GPIO.input(ECHO) == 0:
        start_time = time.time()

    # Save arrival time
    while GPIO.input(ECHO) == 1:
        stop_time = time.time()

    # Calculate distance
    elapsed = stop_time - start_time
    dist = (elapsed * 34300) / 2  # Speed of sound 343 m/s
    return dist

try:
    while True:
        d = distance()
        print(f"Distance: {d:.2f} cm")
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()

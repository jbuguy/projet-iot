import time

# Path to onboard LED
LED_PATH = "/sys/class/leds/ACT/brightness"

def led_on():
    with open(LED_PATH, "w") as f:
        f.write("1")

def led_off():
    with open(LED_PATH, "w") as f:
        f.write("0")

print("Blinking the onboard LED... (Press Ctrl+C to stop)")

try:
    while True:
        led_on()
        time.sleep(0.5)
        led_off()
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Stopped.")

import RPi.GPIO as GPIO
import time

# Pin Configuration
CLK_PIN = 12    # Clock output (change to 12 or 13 if needed)
WR_PIN = 27     # Write (start conversion)
RD_PIN = 17     # Read
INTR_PIN = 22   # Interrupt

# Data pins D0-D7
DATA_PINS = [5, 6, 13, 19, 26, 21, 20, 16]

def setup():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Setup clock (640kHz PWM)
    GPIO.setup(CLK_PIN, GPIO.OUT)
    pwm = GPIO.PWM(CLK_PIN, 640000)
    pwm.start(50)
    
    # Setup control pins
    GPIO.setup(WR_PIN, GPIO.OUT)
    GPIO.setup(RD_PIN, GPIO.OUT)
    GPIO.setup(INTR_PIN, GPIO.IN)
    
    # Setup data pins as inputs
    for pin in DATA_PINS:
        GPIO.setup(pin, GPIO.IN)
    
    # Initialize control pins to HIGH
    GPIO.output(WR_PIN, GPIO.HIGH)
    GPIO.output(RD_PIN, GPIO.HIGH)
    
    return pwm

def read_adc():
    """Read 8-bit value from ADC0804"""
    # Start conversion - WR pulse
    GPIO.output(WR_PIN, GPIO.LOW)
    time.sleep(0.000001)  # 1 microsecond
    GPIO.output(WR_PIN, GPIO.HIGH)
    
    # Wait for conversion complete (check INTR pin)
    timeout = time.time() + 0.001  # 1ms timeout
    while GPIO.input(INTR_PIN) == GPIO.HIGH:
        if time.time() > timeout:
            break
        time.sleep(0.000001)
    
    # Read data - RD pulse
    GPIO.output(RD_PIN, GPIO.LOW)
    time.sleep(0.000001)
    
    # Read 8-bit value from data pins
    value = 0
    for i, pin in enumerate(DATA_PINS):
        if GPIO.input(pin):
            value |= (1 << i)
    
    GPIO.output(RD_PIN, GPIO.HIGH)
    
    return value

def get_gas_reading():
    """Get gas sensor reading with multiple samples"""
    samples = 5
    total = 0
    
    for _ in range(samples):
        total += read_adc()
        time.sleep(0.01)
    
    avg_value = total / samples
    voltage = (avg_value / 255.0) * 5.0
    percentage = (avg_value / 255.0) * 100
    
    return avg_value, voltage, percentage

def main():
    print("=" * 50)
    print("  GAS SENSOR TEST - ADC0804")
    print("=" * 50)
    print()
    
    # Setup GPIO
    pwm = setup()
    print("✓ GPIO initialized")
    print("✓ Clock running at 640kHz")
    print()
    
    # Sensor warm-up
    print("Warming up sensor...")
    print("(For accurate readings, wait 2-3 minutes)")
    print("(First time use: wait 24-48 hours)")
    
    for i in range(10, 0, -1):
        print(f"  Starting in {i} seconds...", end='\r')
        time.sleep(1)
    print()
    print()
    
    try:
        print("Reading gas sensor... (Press Ctrl+C to stop)")
        print()
        print(f"{'Time':<12} {'Raw':<8} {'Voltage':<10} {'Level':<10} {'Status'}")
        print("-" * 60)
        
        while True:
            # Get reading
            raw, voltage, level = get_gas_reading()
            
            # Determine status
            if level < 30:
                status = "✓ Clean Air"
            elif level < 50:
                status = "○ Normal"
            elif level < 70:
                status = "△ Elevated"
            else:
                status = "⚠ HIGH!"
            
            # Display reading
            timestamp = time.strftime("%H:%M:%S")
            print(f"{timestamp:<12} {raw:>3.0f}      {voltage:>4.2f}V     {level:>5.1f}%     {status}")
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print()
        print()
        print("Stopping sensor reading...")
    
    finally:
        pwm.stop()
        GPIO.cleanup()
        print("✓ GPIO cleaned up")
        print()
        print("Test complete!")

if __name__ == "__main__":
    main()
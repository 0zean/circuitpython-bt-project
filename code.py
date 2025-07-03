import time

import adafruit_ble
import board
import digitalio
import rotaryio  # type: ignore
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.standard.hid import HIDService
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# Rotary encoder setup
encoder = rotaryio.IncrementalEncoder(board.P0_11, board.P0_17)  # type: ignore
last_position = encoder.position

# Encoder button (play/pause)
button = digitalio.DigitalInOut(board.P0_20)  # type: ignore
button.switch_to_input(pull=digitalio.Pull.UP)
button_last = True
button_debounce_time = 0

# Toggle switch (prev/next track)
prev_button = digitalio.DigitalInOut(board.P0_22)  # type: ignore
prev_button.switch_to_input(pull=digitalio.Pull.UP)
prev_button_last = True
prev_debounce_time = 0

next_button = digitalio.DigitalInOut(board.P0_24)  # type: ignore
next_button.switch_to_input(pull=digitalio.Pull.UP)
next_button_last = True
next_debounce_time = 0

# BLE HID setup
hid = HIDService()

advertisement = ProvideServicesAdvertisement(hid)
# Set appearance to "HID Generic" (960)
advertisement.appearance = 960
advertisement.complete_name = "Media Controller"

scan_response = Advertisement()
scan_response.complete_name = "CircuitPython Media Remote"

# BLE instance
ble = adafruit_ble.BLERadio()
ble.name = "Media Controller"

# Consumer Control HID setup
cc = ConsumerControl(hid.devices)

print("Starting BLE Media Controller...")


def start_advertising() -> None:
    print("Advertising...")
    ble.start_advertising(advertisement=advertisement, scan_response=scan_response)


# Initial advertising
if not ble.connected:
    start_advertising()
else:
    print("Already connected")
    print(ble.connections)

while True:
    # Wait for connection
    while not ble.connected:
        time.sleep(0.1)

    print("Connected to device!")

    # Main control loop - only runs when connected
    try:
        while ble.connected:
            current_time = time.monotonic()

            # Rotary encoder for volume
            position = encoder.position
            if position != last_position:
                if position > last_position:
                    print("Volume Up")
                    cc.send(ConsumerControlCode.VOLUME_INCREMENT)
                else:
                    print("Volume Down")
                    cc.send(ConsumerControlCode.VOLUME_DECREMENT)
                last_position = position
                time.sleep(0.1)  # Prevent too rapid firing

            # Encoder button = play/pause (with proper debouncing)
            current_button = button.value
            if not current_button and button_last and (current_time - button_debounce_time > 0.2):
                print("Play/Pause")
                cc.send(ConsumerControlCode.PLAY_PAUSE)
                button_debounce_time = current_time
            button_last = current_button

            # Previous track button (with proper debouncing)
            current_prev = prev_button.value
            if not current_prev and prev_button_last and (current_time - prev_debounce_time > 0.3):
                print("Previous Track")
                cc.send(ConsumerControlCode.SCAN_PREVIOUS_TRACK)
                prev_debounce_time = current_time
            prev_button_last = current_prev

            # Next track button (with proper debouncing)
            current_next = next_button.value
            if not current_next and next_button_last and (current_time - next_debounce_time > 0.3):
                print("Next Track")
                cc.send(ConsumerControlCode.SCAN_NEXT_TRACK)
                next_debounce_time = current_time
            next_button_last = current_next

            time.sleep(0.01)  # Small delay to prevent overwhelming the system

    except Exception as e:
        print("Connection error:", e)

    print("Disconnected, restarting advertising...")
    start_advertising()

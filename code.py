#replace the code.py file in the "CIRCUITPY" directory with this!
#make sure to install adafruit_hid and kmk libraries
import time
import board
import analogio
import json
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners.keypad import KeysScanner
from kmk.modules import Module

#this helper function map string names from json config file to kmk/hidkeycodes
def parse_key(key_str):
    return getattr(KC, key_str.upper(), KC.NO), getattr(Keycode, key_str.upper(), Keycode.A)

#load configs
try:
    with open("/config.json", "r") as f:
        config = json.load(f)
except Exception as e:
    print(f"[ERROR] failed to load config.json: {e}")
    config = {
        "mechanical_keys": ["RIGHT", "DOWN", "LEFT"],
        "hall_effect": {
            "GP27": {"key": "A", "actuation": 0.00},
            "GP28": {"key": "B", "actuation": 0.00},
            "GP29": {"key": "C", "actuation": 0.00}
        },
        "other_settings": {
            "reject_val": 1.5,
            "debounce": 0.1,
            "confirm_samples": 2
        }
    }

#this class reads the hall effect sensors and injects the key presses into KMK's hid report alongside with the mechanical key matrux
class hallEffectModule(Module):
    #initialize properties, full explanation in README.md
    def __init__(self, sensor_pins, keymap, actu_V, reject_val=1.5, debounce=0.1, confirm_samples=2):
        self.sensors = {name: analogio.AnalogIn(pin) for name, pin in sensor_pins.items()}
        self.keys = keymap
        self.actu_V = actu_V
        self.reject_val = reject_val
        self.debounce = debounce
        self.confirm_samples = confirm_samples

        #bypass kmk's internal hid state and inits it as a hid keyboard object directly
        self.hid_keyboard = Keyboard(usb_hid.devices)
        self.was_below = {name: 0 for name in self.sensors}
        self.consecutive_low = {name: 0 for name in self.sensors}
        self.last_trigger_time = {name: 0 for name in self.sensors}
    
    #gets sensor voltage
    def get_V(self, analog_in):
        return (analog_in.value * 3.3) / 65535
    
    #Doesnt return anything while booting up
    def during_bootup(self, keyboard):
        return
    
    #main logic function
    def before_matrix_scan(self, keyboard):
        now = time.monotonic()

        for name, sensor in self.sensors.items():
            V = self.get_V(sensor)
            #debug function, see README.md for more detail on this
            print(f"[DEBUG] {name}: {V:.3f}V (actu_V {self.actu_V[name]}V)")
            #rejects garbage value key presses(in case the sensor voltage and returns garbage values, which can aggresively spam key presses
            if V < self.reject_val:
                self.was_below[name] = False
                self.consecutive_low[name] = 0
                continue
            
            is_below = V < self.actu_V[name]
            if is_below:
                self.consecutive_low[name] += 1
            else:
                self.consecutive_low[name] = 0
            confirmed = self.consecutive_low[name] >= self.confirm_samples

            #key press
            if confirmed and not self.was_below[name] and (now - self.last_trigger_time[name]) > self.debounce:
                key = self.keys[name]
                #debug function, see README.md for more detail on this
                print(f"[DEBUG] {name} PRESS key {key}")
                self.hid_keyboard.press(key)
                self.last_trigger_time[name] = now
            #release
            elif not confirmed and self.was_below[name]:
                key = self.keys[name]
                print(f"[DEBUG] {name} RELEASE key {key}")
                self.hid_keyboard.release(key)
            self.was_below[name] = confirmed
        return

    #other functions of kmk
    def after_matrix_scan(self, keyboard):
        return

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return
    
    def on_powersave_enable(self, keyboard):
        return
    
    def on_powersave_disable(self, keyboard):
        return

#initialize kmk keyboard
keyboard = KMKKeyboard()

#mechanical switch setup
m_keys = [getattr(KC, k.upper(), KC.NO) for k in config["mechanical_keys"]]
keyboard.matrix = KeysScanner(
    pins=[board.GP0, board.GP1, board.GP2], #set your mechanical pins here, i do 0, 1 and 2
    value_when_pressed=False, 
)
keyboard.keymap = [m_keys]

#hall effect switches setup
sensor_pins = {
    "GP27": board.GP27, 
    "GP28": board.GP28, 
    "GP29": board.GP29
}
he_keymap = {}
actu_V = {}

for name, data in config["hall_effect"].items():
    _, hid_key = parse_key(data["key"])
    he_keymap[name] = hid_key
    actu_V[name] = data["actuation"]

hall_module = hallEffectModule(
    sensor_pins=sensor_pins,
    keymap=he_keymap,
    actu_V=actu_V,
    reject_val=config["other_settings"]["reject_val"],
    debounce=config["other_settings"]["debounce"],
    confirm_samples=config["other_settings"]["confirm_samples"],
)
keyboard.modules.append(hall_module)

if __name__ == '__main__':
    keyboard.go()

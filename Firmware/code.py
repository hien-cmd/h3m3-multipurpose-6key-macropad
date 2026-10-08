#replace the code.py file in the "CIRCUITPY" directory with this!
#make sure to install adafruit_hid and kmk libraries, and put config.json in the same folder
import time
import board
import analogio
import json
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners.keypad import KeysScanner
from kmk.modules import Module

ADC_MAX = 65535
VREF = 3.3

#converts a voltage into a raw adc count so the hot loop never has to touch floats
def v_to_raw(volts):
    return int((volts * ADC_MAX) / VREF)

#maps a string name from config.json to a kmk keycode
def parse_key(key_str):
    return getattr(KC, str(key_str).upper(), KC.NO)

DEFAULT_CONFIG = {
    "mechanical_keys": ["RIGHT", "DOWN", "LEFT"],
    "hall_effect": {
        "GP27": {"key": "Z"},
        "GP28": {"key": "X"},
        "GP29": {"key": "C"}
    },
    "tuning": {
        "debug": False,
        "auto_calibrate": True,
        "rest_v": 2.40,
        "actuation_depth": 0.15,
        "hysteresis": 0.05,
        "rapid_trigger": True,
        "rt_press_delta": 0.03,
        "rt_release_delta": 0.03,
        "filter_strength": 2,
        "reject_v": 1.00
    }
}

try:
    with open("/config.json", "r") as f:
        config = json.load(f)
except Exception as e:
    print(f"[ERROR] failed to load config.json, using defaults: {e}")
    config = DEFAULT_CONFIG

tuning = config.get("tuning", {})

#global tuning value, falls back to the built in default if config.json is missing it
def tune(name):
    return tuning.get(name, DEFAULT_CONFIG["tuning"][name])

#per switch tuning value, falls back to the global one if that switch doesnt override it
def tune_for(data, name):
    return data.get(name, tune(name))


#index constants for the per sensor state list
#a flat list is used instead of dicts because list indexing avoids a hash lookup
#per sensor per scan, which matters when this loop runs thousands of times a second
_ADC = 0        #analogio.AnalogIn object
_KEY = 1        #kmk keycode
_ACT = 2        #raw count, key is considered pressed below this
_REL = 3        #raw count, key is considered released above this
_PRESSED = 4    #current logical state
_FILT = 5       #filtered raw value
_EXTREME = 6    #deepest/shallowest point seen, used by rapid trigger
_RTP = 7        #rapid trigger press delta for this switch, raw counts
_RTR = 8        #rapid trigger release delta for this switch, raw counts
_NAME = 9       #label, only used for debug output


#reads the hall effect sensors and writes key state straight into kmk's own
#pressed key set, so there is exactly one hid report builder for the whole board
class HallEffectModule(Module):
    def __init__(self, sensor_pins, he_config):
        self.debug = bool(tune("debug"))
        self.auto_calibrate = bool(tune("auto_calibrate"))
        self.rapid_trigger = bool(tune("rapid_trigger"))
        self.filter_shift = int(tune("filter_strength"))
        self.reject_raw = v_to_raw(tune("reject_v"))

        self._sensors = []
        self._boot = []  #per switch calibration inputs, only read once at startup

        for name, pin in sensor_pins.items():
            data = he_config[name]
            adc = analogio.AnalogIn(pin)

            #every threshold is resolved per switch and converted to raw counts here,
            #so the scan loop only ever compares integers
            self._sensors.append([
                adc,
                parse_key(data.get("key", "NO")),
                0,
                0,
                False,
                adc.value,
                adc.value,
                v_to_raw(tune_for(data, "rt_press_delta")),
                v_to_raw(tune_for(data, "rt_release_delta")),
                name,
            ])

            self._boot.append((
                v_to_raw(tune_for(data, "actuation_depth")),
                v_to_raw(tune_for(data, "hysteresis")),
                v_to_raw(tune_for(data, "rest_v")),
            ))

        self._next_debug = 0.0

    #averages a handful of readings to find where this particular sensor sits at rest
    def _calibrate(self, s, samples=32):
        total = 0
        for _ in range(samples):
            total += s[_ADC].value
            time.sleep(0.002)
        return total // samples

    #kmk calls this once on startup, before the main loop begins
    def during_bootup(self, keyboard):
        for i, s in enumerate(self._sensors):
            act_depth, hyst, rest_manual = self._boot[i]

            if self.auto_calibrate:
                rest = self._calibrate(s)
            else:
                rest = rest_manual

            #thresholds are derived from this sensor's own resting point and its own
            #depth setting, so switch to switch variation stops mattering
            s[_ACT] = rest - act_depth
            s[_REL] = s[_ACT] + hyst
            s[_FILT] = rest
            s[_EXTREME] = rest

            if self.debug:
                print(f"[CAL] {s[_NAME]} rest={rest} act={s[_ACT]} rel={s[_REL]}")
        return

    def before_matrix_scan(self, keyboard):
        #bound to locals once, attribute lookups inside the loop are not free
        rt = self.rapid_trigger
        shift = self.filter_shift
        reject = self.reject_raw
        pressed_set = keyboard.keys_pressed
        pending = False

        for s in self._sensors:
            raw = s[_ADC].value

            #integer exponential moving average, smooths adc noise with no float math
            if shift:
                f = s[_FILT]
                f += (raw - f) >> shift
                s[_FILT] = f
            else:
                f = raw
                s[_FILT] = raw

            #a reading this low means the sensor is floating or disconnected,
            #not that someone slammed the key, so drop it rather than spamming
            if f < reject:
                if s[_PRESSED]:
                    pressed_set.discard(s[_KEY])
                    s[_PRESSED] = False
                    pending = True
                continue

            if rt:
                act = s[_ACT]
                if f > act:
                    #key is sitting above its actuation point, fully at rest
                    if s[_PRESSED]:
                        pressed_set.discard(s[_KEY])
                        s[_PRESSED] = False
                        pending = True
                    s[_EXTREME] = f
                elif s[_PRESSED]:
                    if f < s[_EXTREME]:
                        #still travelling further down, track the new deepest point
                        s[_EXTREME] = f
                    elif f - s[_EXTREME] > s[_RTR]:
                        #lifted a little off the bottom, release immediately
                        pressed_set.discard(s[_KEY])
                        s[_PRESSED] = False
                        s[_EXTREME] = f
                        pending = True
                else:
                    if s[_EXTREME] > act:
                        #first crossing of the actuation point, fire right away
                        pressed_set.add(s[_KEY])
                        s[_PRESSED] = True
                        s[_EXTREME] = f
                        pending = True
                    else:
                        if f > s[_EXTREME]:
                            s[_EXTREME] = f
                        if s[_EXTREME] - f > s[_RTP]:
                            #pushed back down without fully releasing, re-press
                            pressed_set.add(s[_KEY])
                            s[_PRESSED] = True
                            s[_EXTREME] = f
                            pending = True
            else:
                #plain schmitt trigger, press low and release high with a gap between
                if not s[_PRESSED]:
                    if f < s[_ACT]:
                        pressed_set.add(s[_KEY])
                        s[_PRESSED] = True
                        pending = True
                elif f > s[_REL]:
                    pressed_set.discard(s[_KEY])
                    s[_PRESSED] = False
                    pending = True

        #one flag for the whole sweep, and only when something actually changed
        if pending:
            keyboard.hid_pending = True

        #debug output is throttled hard, printing every scan is the single slowest
        #thing this loop can do and it will wreck your scan rate
        if self.debug:
            now = time.monotonic()
            if now >= self._next_debug:
                self._next_debug = now + 0.25
                for s in self._sensors:
                    v = (s[_FILT] * VREF) / ADC_MAX
                    print(f"[DBG] {s[_NAME]} raw={s[_FILT]} {v:.3f}V act={s[_ACT]} down={s[_PRESSED]}")
        return

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


keyboard = KMKKeyboard()

#mechanical switch setup
keyboard.matrix = KeysScanner(
    pins=[board.GP0, board.GP1, board.GP2],  #set your mechanical pins here
    value_when_pressed=False,
)
keyboard.keymap = [[parse_key(k) for k in config.get("mechanical_keys", [])]]

#hall effect switch setup
ALL_SENSOR_PINS = {
    "GP27": board.GP27,  #set your hall effect pins here
    "GP28": board.GP28,
    "GP29": board.GP29,
}

he_config = config.get("hall_effect", {})

#only wire up sensors that actually have an entry in the config
sensor_pins = {n: p for n, p in ALL_SENSOR_PINS.items() if n in he_config}

keyboard.modules.append(HallEffectModule(sensor_pins, he_config))

if __name__ == '__main__':
    keyboard.go()

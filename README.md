# H3M3 - THE multi-purpose 6 key macro pad
This is a 6 key macro pad with 6 programmable keys, 3 being hotswap mechanical switches for casual work and the other 3 being magnetic switches for with adjustable sensitivity for gaming.

## Features
- 3 hotswap mechanical switches
- 3 interchangable magnetic switches
- Fully programmable keys and firmware(now can all be modified in a config.json file!)
- Small form factor
- Open source hardware and firmware

## Hardware needed
- Waveshare RP2040-Zero
- 3x mechanical switches(can be 3 or 5 pin)
- 3x magnetic switches
- Surface-mount hotswap sockets or mill-max sockets(PCB currently only support Kailh hotswap surface mount sockets and mill max)
- 3x Hall Effect sesnors 
- Custom PCB
- 3D printed case

## Tools needed
- Soldering iron and a bit of solder
- Hot glue gun and a bit of glue
- 3D printer

## Firmware
- code.py, built using CircuitPython and KMK

## Pinout(PCB - RP2040-Zero)
VCC - 5V
GND - GND
D1 - GPIO00
D2 - GPIO01
D3 - GPIO02
A1 - GPIO27
A2 - GPIO28
A3 - GPIO29

## Directory structure
LICENSE(License file)
README.md(README file)
code.py(code)
h3m3-case.stl(3d printable case file)
h3m3-pcb.zip(PCB file)
h3m3.kicad_sch(Schematic file for PCB)

## Prerequisites
-Has all the hardware needed
-Has the 3d printed case and the PCB

## Assembly instructions
1. Solder hotswap sockets onto pcb
2. Solder RP2040-Zero headers in if you haven't yet, then solder RP2040-ZERO to PCB
3. Solder in Hall Effect sensors so it sits on the holes in each magnetic switch slot on the PCB
4. Put the PCB into the case
5. Fit the 3 mechanical switches through the casing and fit the pins into the hotswap sockets, so the PCB sits where it should be, then fit the magnetic switches in
6. Glue bottom casing with the body.


## Firmware installation
1. Install CircuitPython on the RP2040-Zero:
    1. Plug the RP2040-Zero into your computer, a new storage disk should appear
    2. Download the CircuitPython file here: https://circuitpython.org/board/waveshare_rp2040_zero/
    3. Drag that file into the storage disk, the disk should rename itself into "CIRCUITPY"
2. Download the full adafruit_hid library here: https://github.com/adafruit/Adafruit_CircuitPython_HID
3. Download the full kmk library here: https://github.com/KMKfw/kmk_firmware
4. Drag ONLY the "adafruit_hid" and "kmk" folders inside their corresponding folders and put it in the "lib" folder in the "CIRCUITPY" disk
5. Drag the provided "code.py" file into the "CIRCUITPY" disk and REPLACE the existing code.py file
6. Drag the config.json file into the "CIRCUITPY" disk

## Default keymap(m=mechanical switch, a=analog/magnetic/hall effect switches)
M1 - a
M2 - b
M3 - ESC
A1 - Z
A2 - x
A3 - c

## Programming and customization guide

### How the magnetic switches work
Each magnetic switch is read as an analog voltage through a Hall Effect sensor. Rather than a single fixed on/off point, the firmware measures each sensor's own resting voltage at boot, then watches for it to dip by a set amount when a magnet gets close. This means switch to switch differences in magnet strength or sensor tolerance are absorbed automatically, and every tuning value below is a depth or delta relative to that switch's own resting point rather than an absolute voltage.

### config.json structure
config.json has three top level sections:
- "mechanical_keys": a list of 3 key names for the mechanical switches, in the order M1, M2, M3
- "hall_effect": one entry per magnetic switch (GP27, GP28, GP29), each with a "key" name and, optionally, its own overrides for any of the per switch tuning values below
- "tuning": the global defaults used by any magnetic switch that doesn't set its own override, plus a few board wide settings
Per switch tuning

Inside a switch's entry under "hall_effect", any of these can be set individually for that switch. Leave one out and it falls back to the matching value in "tuning" instead:

- "actuation_depth": how far, in volts, the voltage has to drop from that switch's own resting point before it registers as pressed. This is the main sensitivity knob, lower means a lighter, earlier press
- "hysteresis": the gap, in volts, between the press point and the release point, only used when "rapid_trigger" is off. Keeps a switch sitting right at the threshold from chattering
- "rapid_trigger": turns rapid trigger on or off for this switch on its own, so you can mix and match. On means fast reset for gaming, off means the key stays held down until you physically let it back up, which is what you want for a hold to repeat key
- "rt_press_delta": with "rapid_trigger" on, how far the voltage has to push back down from the highest point reached since release before it re-presses
- "rt_release_delta": with "rapid_trigger" on, how far the voltage has to lift back up from the deepest point reached since pressing before it releases
- "rest_v": the resting voltage to use for that switch if "auto_calibrate" is turned off
-"reject_v": that switch's fault floor, see the warning under board wide tuning below

### Board wide tuning
These live only in "tuning" and apply to every magnetic switch:

- "debug": prints resting voltage at boot and live readings a few times a second when true, off by default since it does slow the board down slightly
- "auto_calibrate": measures each switch's own resting voltage at boot instead of using a fixed "rest_v". Leave this on unless you have a specific reason not to
- "rapid_trigger": the default for every switch that doesn't set its own, turns on press and release based on direction of travel rather than a single fixed point, this is what makes the switches feel fast for gaming. Turn it off for simple, predictable single actuation behavior instead
- "filter_strength": how much incoming noise gets smoothed out, higher is smoother but slightly slower to react. 2 is a good starting point
- "reject_v": a fault floor, any reading below this is treated as a disconnected or malfunctioning sensor and the key is forced off. 

### Magnetic/Hall Effect switches calibration 
As mentioned in the properties list, rapid trigger and more advanced functions need fine tuning and proper calibration:
1. Set "debug" in config.json to "true" and save the file
2. Open a serial monitor such as Thonny or Terminal(I personally use Terminal's built-in screen function) at baud 115200
3. Note the resting value of each switch at boot
4. One by one press each magnetic switch and note the voltage when it is pressed.
5. The difference between the resting voltage and the one where it's fully pressed is its full travel. A good "actuation_depth" value for each switch is about a third to half of that value, adjust to however you want it. Here's some reference ranges:
- Small actuation_depth (0.05 to 0.10) meaning the key fires almost immediately, barely touching it.
- Medium (0.15), about halfway down, good middle ground.
- Large (0.25 and up) needs deliberate, deeper presses. 
6. If the switches starts pressing on it's own, raise its "hysteresis" property value or the "filter_strength"(board-wide change though)
7. Set "debug" back to false once you're done

### Debug functions
When "debug" is set to "true" in the config.json, it prints each magnetic switch's resting voltage at boot and then its live current voltage. This can be seen with a serial monitor such as Terminal's built in screen function to calibrate actuation depth. Leave it off if you aren't calibrating it because it does make a slightly less reactive.

### Mechanical switches properties
keyboard.matrix:
    - pins: this defines the pins where the mechanical switches are placed.
    - value_when_pressed: this is the value when the key is pressed. It is determined by the microcontroller's pull up resistor, which registers a constant HIGH/True(3.3V) until the mechanical switch is pressed and join the pin with GND, which pulls it down to Low/False(0V). This can be changed(but in most cases don't).
keyboard.keymap: this defines what is typed when a keystroke is registered, can be changed at line 100

## Possible future improvements
    -RGB lighting
    -Rotary encoder slot instead of a 6th key(maybe?)

## License
MIT License

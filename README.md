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
- 3x mechanical switches(can be 5 pin or 3 pin, I personally used gateron milky yellows in my prototype)
- 3x magnetic switches(i personally use gateron jade ultras in my prototype)
- Surface-mount hotswap sockets or mill-max sockets(PCB currently only support Kailh hotswap surface mount sockets and mill max)
- 3x Hall Effect sesnors 
- Custom PCB(Version one UPLOADED!)
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
2. Solder RP2040-Zero headers in if you haven't yet, then solder RP2040-ZERO to the BOTTOM SIDE of the PCB(yes, I know it sounds wrong, but I designed it that way, the top right PCB hole from the front view of the PCB should be 5V)
3. Solder in Hall Effect sensors so it sits on the holes in each magnetic switch slot on the PCB
4. Put the PCB into the case
5. Fit the 3 mechanical switches through the casing and fit the pins into the hotswap sockets, so the PCB sits where it should be
6. Glue the PCB onto the case
7. Glue bottom casing with the body.


## Firmware installation
1. Install CircuitPython on the RP2040-Zero:
    1. Plug the RP2040-Zero into your computer, a new storage disk should appear
    2. Download the CircuitPython file here: https://circuitpython.org/board/waveshare_rp2040_zero/
    3. Drag that file into the storage disk, the disk should rename itself into "CIRCUITPY"
2. Download the full adafruit_hid library here: https://github.com/adafruit/Adafruit_CircuitPython_HID
3. Download the full kmk library here: https://github.com/KMKfw/kmk_firmware
4. Drag ONLY the "adafruit_hid" and "kmk" folders inside their corresponding folders and put it in the "lib" folder in the "CIRCUITPY" disk
5. Drag the provided "code.py" file into the "CIRCUITPY" disk and REPLACE the existing code.py file

## Default keymap(m=mechanical switch, a=analog/magnetic/hall effect switches)
M1 - a
M2 - b
M3 - c
A1 - a
A2 - z
A3 - x

## Programming and customization guide

### Magnetic/Hall Effect switches properties
The Hall Effect switch system is built as a class that has multiple propeties, and needs proper calibration to work well:
- sensor_pins: this defines the pins that the Hall Effect sensors register their output on, can be changed at line 106-108
- keymap: controls what is typed when the keystroke is registered, can be changed at line 111-113
- actu_V: the voltage at which the key is registered, needs fine tuning for rapid trigger, can be changed at line 118-120
- reject_val: the voltage where the input is rejected, this acts as a safety net so if the sensor disconnectes or malfunctions it wont spam keystrokes on the screen. This is mostly relevant for prototype versions but still good to have. Adjustable at line 122
- debounce: the minimum time, measured in seconds before another keystroke can be registered. Can be changes at line 123
- confirm_samples: the minimum amount of readings before it can be treated as a keypress, used as a guard to stop noisy, glitchy readings. Can be modified at line 124

### Magnetic/Hall Effect switches calibration 
As mentioned in the properties list, rapid trigger and more advanced functions need fine tuning and proper calibration. I will make a proper calibration file soon. Basically, you replace the code in the code.py of the RP2040-Zero with the calibration code and use a software to watch the output of the macro pad at baud 115200(I personally use Terminal's built in screen function). When you press the magnetic keys, the printed voltage dips. You will have to press each of the keys and record this dip. Then register the dips in actu_V.

### Debug functions
These are printed messages in the code that prints all of it's voltage readings and whenever a hall effect key is pressed, so you can see the problem easier if there is one. You can use any software that prints the output of the RP2040-Zero(I presonally use Terminal's built in screen function)

### Mechanical switches properties
keyboard.matrix:
    - pins: this defines the pins where the mechanical switches are placed, can be changed at line 96
    - value_when_pressed: this is the value when the key is pressed. It is determined by the microcontroller's pull up resistor, which registers a constant HIGH/True(3.3V) until the mechanical switch is pressed and join the pin with GND, which pulls it down to Low/False(0V). This can be changed(but in most cases don't) at line 97
keyboard.keymap: this defines what is typed when a keystroke is registered, can be changed at line 100

## Possible future improvements
    -RGB lighting
    -Rotary encoder slot instead of a 6th key(maybe?)

## License
MIT License

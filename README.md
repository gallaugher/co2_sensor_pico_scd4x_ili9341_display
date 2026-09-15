# CO2 Monitor: Raspberry Pi Pico 2 W + SCD-40 + 2.4" ILI9341 Display

A desk-top air-quality readout written in CircuitPython. An Adafruit SCD-40 measures true CO2 (plus temperature and humidity), and a 2.4" 320x240 ILI9341 TFT shows the results big enough to read from across the room. The screen is black with white text while CO2 is under 1,000 ppm and shows a green smiley. When CO2 reaches 1,000 ppm or more, the whole screen flips to white with black text, the smiley becomes a red frown, and a 10 mm LED lights up as an extra "open a window" nudge. A spinner runs while the sensor takes its first reading (about five seconds), and after that the display only redraws the values that change.

This is a port of the [QT Py / 1.44" ST7735R version](https://github.com/gallaugher/c02sensor-w-QTPy-and-TFT-LCD) to the Pico and a bigger display. The display wiring and fonts come from the [ILI9341 320x240 display repo](https://github.com/gallaugher/ili9341-320x240-display-circuitpython).

## Parts

- [Raspberry Pi Pico 2 W with headers](https://www.adafruit.com/product/6315) (the [headerless version](https://www.adafruit.com/product/6087) works if you don't mind soldering)
- [Adafruit SCD-40 True CO2, Temperature and Humidity Sensor (STEMMA QT)](https://www.adafruit.com/product/5187)
- [STEMMA QT to male header cable](https://www.adafruit.com/product/4209) to plug the SCD-40 into the breadboard
- 2.4" SPI ILI9341 320x240 TFT with the 14-pin header (9 display pins + 5 touch pins), e.g. [this HiLetgo listing on Amazon](https://www.amazon.com/HiLetgo-Display-ILI9341-Touch-240x320/dp/B07WNLNRDN). The touch pins are not used. The 9-pin 2.2" version of this board works with identical wiring.
- [Monk Makes Breadboard for Pico](https://www.adafruit.com/product/5422) (also at [MonkMakes](https://monkmakes.com/pico_bb)); its printed pin labels make the wiring below much easier to follow
- [Premium male/male jumper wires](https://www.adafruit.com/product/1957)
- [USB-C to micro-USB data cable](https://www.adafruit.com/product/3878). The Pico 2 W's port is micro-USB, and it must be a data cable, not a charge-only one, or CIRCUITPY will never appear.
- 10 mm LED
- 100 ohm resistor

## Wiring

Display (ILI9341 header, counting from the VCC end):

- VCC → 3V3 (red)
- GND → GND (black)
- CS → GP20 (white)
- RESET → GP15 (purple)
- DC → GP21 (yellow)
- SDI (MOSI) → GP19 (blue)
- SCK → GP18 (green)
- LED (backlight) → GP22 (orange)
- SDO (MISO), T_CLK, T_CS, T_DIN, T_DO, T_IRQ → leave unconnected

SCD-40 (STEMMA QT cable):

- Red → 3V3
- Black → GND
- Blue (SDA) → GP4
- Yellow (SCL) → GP5

Warning LED:

- GP17 → 100 ohm resistor → LED long leg (+)
- LED short leg (−) → GND (there is a GND pin right next to GP17)

Power the display from 3V3, not VBUS. Leave the J1 solder jumper on the back of the display open (that's how it ships).

## Software

- Copy `code-for-SCD40-pico-ILI9341.py` to CIRCUITPY as `code.py`.
- Copy the `fonts` folder from the [ILI9341 display repo](https://github.com/gallaugher/ili9341-320x240-display-circuitpython) to CIRCUITPY. The program uses `Collegiate-50.bdf`, `helvB24.bdf`, and `forkawesome-42.pcf`.
- Install libraries with circup: `circup install adafruit_scd4x adafruit_ili9341 adafruit_display_text adafruit_bitmap_font`
- To change the alert level, edit `CO2_THRESHOLD` at the top of the file. To use the Pico's onboard LED instead of an external one, change `board.GP17` to `board.LED`.

<img width="600" height="450" alt="Bad reading example" src="https://github.com/user-attachments/assets/2917ea38-567c-4876-99a7-604e234ebc47" />
<img width="600" height="450" alt="Good example" src="https://github.com/user-attachments/assets/fd00cde7-ea53-4e8c-9122-66e2cd6b4103" />

# code.py
# CO2 Sensor in CircuitPython — Raspberry Pi Pico 2 W + 2.4" ILI9341 (320x240) + Adafruit SCD-40
# Adapted from gallaugher/c02sensor-w-QTPy-and-TFT-LCD (128x128 ST7735R version)
#
# Wiring
#   SCD-40 (STEMMA QT):  SDA -> GP4 (blue), SCL -> GP5 (yellow), 3.3V (red), GND (black)
#   ILI9341:  SCK GP18, MOSI GP19, CS GP20, DC GP21, RESET GP15, LED (backlight) GP22, VCC 3V3, GND
#   Warning LED:  GP17 -> 220-330 ohm resistor -> LED (+)   LED (-) -> GND (the GND pin right next to GP17)
#
# Libraries (circup install ...): adafruit_scd4x adafruit_ili9341 adafruit_display_text adafruit_bitmap_font
# Fonts: uses the /fonts folder from the ili9341-320x240-display-circuitpython repo (already on the board).

import board, busio, time, digitalio, pwmio
import adafruit_scd4x
import displayio, terminalio
import adafruit_ili9341
from fourwire import FourWire
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

# ---------- Display constants (320x240 landscape) ----------
WIDTH = 320
HEIGHT = 240
LEFT_MARGIN = 12
CO2_LABEL_Y = 10        # "CO2: good" / "CO2: HIGH"
CO2_VALUE_Y = 48        # the big number
PPM_GAP, PPM_Y = 12, 98 # small "ppm": gap to the right of the big number, y puts it on the number's baseline
ICON_Y = 140            # smile / frown
RIGHT_COLUMN_X = 160    # temp & humidity
TEMP_Y = 140
HUMID_Y = 192

# ---------- Sensor constants ----------
CO2_THRESHOLD = 1000    # ppm — at or above this is "HIGH"
UPDATE_INTERVAL = 4     # seconds between display updates once data is flowing

# ---------- Colors ----------
COLOR_BLACK = 0x000000
COLOR_WHITE = 0xFFFFFF
COLOR_GREEN = 0x00FF00
COLOR_RED = 0xFF0000

# ---------- Loading animation ----------
LOADING_INTERVAL = 0.05      # how fast the spinner turns (seconds)
LOADING_PHASE_SLEEP = 0.01   # loop delay while waiting for the first reading
SPINNER_CHARS = ['|', '/', '-', '\\']

# ---------- Icons (ForkAwesome code points) ----------
ICON_SMILE = ""
ICON_FROWN = ""

# ---------- Setup CO2 sensor ----------
# The Pico has no board.STEMMA_I2C(), so build the bus by hand: busio.I2C(SCL, SDA)
i2c = busio.I2C(board.GP5, board.GP4)
scd4x = adafruit_scd4x.SCD4X(i2c)
print("Serial number:", [hex(i) for i in scd4x.serial_number])
scd4x.start_periodic_measurement()
print("Waiting for first measurement....")

# ---------- Setup display ----------
displayio.release_displays()
spi = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
display_bus = FourWire(spi, command=board.GP21, chip_select=board.GP20, reset=board.GP15)
backlight = pwmio.PWMOut(board.GP22, frequency=5000, duty_cycle=65535)  # lower duty_cycle to dim
display = adafruit_ili9341.ILI9341(display_bus, width=WIDTH, height=HEIGHT, rotation=0, backlight_pin=None)

# ---------- Setup warning LED ----------
led = digitalio.DigitalInOut(board.GP17)   # use board.LED instead for the Pico's onboard LED (no wiring)
led.direction = digitalio.Direction.OUTPUT
led.value = False

# Dictionary that holds previous values so we only redraw what changed
prev_values = {
    "co2": None,
    "temp": None,
    "humidity": None,
    "is_high": None
}

# ---------- Load fonts once (falls back to the built-in font if a file is missing) ----------
def load_font(path):
    try:
        return bitmap_font.load_font(path)
    except Exception as e:
        print(f"Could not load {path} ({e}) — using built-in font")
        return None

big_font = load_font("/fonts/Collegiate-50.bdf")     # big CO2 number, temp, humidity
text_font = load_font("/fonts/helvB24.bdf")          # "CO2: good", "ppm"
icon_font = load_font("/fonts/forkawesome-42.pcf")   # smile / frown

# ---------- Build the screen ----------
main_group = displayio.Group()

# Single full-screen background; we recolor it by changing the palette
color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = COLOR_BLACK
bg_tile = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)

# anchor_point=(0, 0) means (x, y) is the TOP-LEFT corner of the text — easy to nudge
co2_label = label.Label(
    text_font or terminalio.FONT, scale=1 if text_font else 2, color=COLOR_WHITE,
    anchor_point=(0, 0), anchored_position=(LEFT_MARGIN, CO2_LABEL_Y))
co2_value = label.Label(
    big_font or terminalio.FONT, scale=2 if big_font else 5, color=COLOR_WHITE,
    anchor_point=(0, 0), anchored_position=(LEFT_MARGIN, CO2_VALUE_Y))
ppm_label = label.Label(
    text_font or terminalio.FONT, scale=1 if text_font else 2, color=COLOR_WHITE,
    anchor_point=(0, 0), anchored_position=(LEFT_MARGIN + 200 + PPM_GAP, PPM_Y))
temp_label = label.Label(
    big_font or terminalio.FONT, scale=1 if big_font else 3, color=COLOR_WHITE,
    anchor_point=(0, 0), anchored_position=(RIGHT_COLUMN_X, TEMP_Y))
humid_label = label.Label(
    big_font or terminalio.FONT, scale=1 if big_font else 3, color=COLOR_WHITE,
    anchor_point=(0, 0), anchored_position=(RIGHT_COLUMN_X, HUMID_Y))
icon_label = label.Label(
    icon_font or terminalio.FONT, scale=2 if icon_font else 3, color=COLOR_GREEN,
    anchor_point=(0, 0), anchored_position=(LEFT_MARGIN, ICON_Y))

main_group.append(bg_tile)
for label_obj in [co2_label, co2_value, ppm_label,
                  temp_label, humid_label, icon_label]:
    main_group.append(label_obj)

display.root_group = main_group

# ---------- Loading screen ----------
def update_spinner_animation(frame):
    """Rotating line animation while the SCD-40 warms up (first reading takes ~5 s)."""
    co2_label.text = f"Loading {SPINNER_CHARS[frame]}"
    temp_label.text = f"{SPINNER_CHARS[frame]}"
    humid_label.text = f"{SPINNER_CHARS[frame]}"

def show_loading_screen():
    co2_label.text = "Loading..."
    co2_value.text = ""
    ppm_label.text = ""
    temp_label.text = "..."
    humid_label.text = "..."
    icon_label.text = ""

show_loading_screen()

# ---------- Update only what changed ----------
def update_labels(co2, temp, humidity, is_high):
    if prev_values["is_high"] != is_high:
        # Flip the whole screen: white background + black text when CO2 is HIGH
        color_palette[0] = COLOR_WHITE if is_high else COLOR_BLACK
        new_color = COLOR_BLACK if is_high else COLOR_WHITE
        for label_obj in [co2_label, co2_value, ppm_label, temp_label, humid_label]:
            label_obj.color = new_color

        icon_label.text = ICON_FROWN if is_high else ICON_SMILE
        icon_label.color = COLOR_RED if is_high else COLOR_GREEN
        led.value = is_high   # LED on while CO2 is high

    if prev_values["co2"] != co2:
        co2_label.text = f"CO2: {'HIGH' if is_high else 'good'}"
        co2_value.text = str(co2)
        ppm_label.text = "ppm"
        # Park "ppm" just to the right of the big number, however many digits it has
        number_width = co2_value.bounding_box[2] * co2_value.scale
        ppm_label.anchored_position = (LEFT_MARGIN + number_width + PPM_GAP, PPM_Y)

    if prev_values["temp"] != temp:
        temp_label.text = f"{temp}°F"

    if prev_values["humidity"] != humidity:
        humid_label.text = f"{humidity}%"

    prev_values.update({
        "co2": co2,
        "temp": temp,
        "humidity": humidity,
        "is_high": is_high
    })

# ---------- Main loop ----------
animation_frame = 0
last_animation_time = time.monotonic()

def update():
    global animation_frame, last_animation_time
    current_time = time.monotonic()
    try:
        if scd4x.data_ready:
            co2 = int(scd4x.CO2)
            temp = int((scd4x.temperature * (9 / 5)) + 32)
            humidity = int(scd4x.relative_humidity)
            is_high = co2 >= CO2_THRESHOLD

            print(f"CO2: {co2}ppm")
            print(f"Temperature: {temp}°F")
            print(f"Humidity: {humidity}%\n")

            update_labels(co2, temp, humidity, is_high)
        else:
            # Only animate until the first reading arrives
            if prev_values["co2"] is None:
                if current_time - last_animation_time >= LOADING_INTERVAL:
                    update_spinner_animation(animation_frame % len(SPINNER_CHARS))
                    animation_frame += 1
                    last_animation_time = current_time
    except Exception as e:
        print(f"Error reading sensor: {e}")

while True:
    update()
    if prev_values["co2"] is None:
        time.sleep(LOADING_PHASE_SLEEP)   # fast loop while the spinner runs
    else:
        time.sleep(UPDATE_INTERVAL)       # relaxed loop once readings are flowing
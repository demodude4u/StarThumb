# - Small simply battery icon when battery is getting low
# A bunch stolen from the battery program in the arcade

from machine import ADC

from thumbyGrayscale import display
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

try:
    import emulator
    emulated = True
except ImportError:
    emulated = False

display.setFPS(30)

# BITMAP: width: 8, height: 5
bmpLowBatt = [bytearray([224, 238, 224, 224, 224, 224, 224, 224]),
              bytearray([224, 224, 238, 238, 238, 238, 228, 224])]

batteryADC = ADC(26)

battFrame = 0
lowBatt = False
battLowest = 38000
while True:
    battFrame += 1

    if not emulated and battFrame % 600 == 0:
        battSample = adc.read_u16()
        if battSample > 38000 or battSample < battLowest:
            battLowest = battSample
        lowBatt = battLowest <= 33700

    display.fill(0)
    if battFrame % 120 < 30:
        display.blit(bmpLowBatt, 64, 0, 8, 5, 0b11, 0, 0)
    display.update()

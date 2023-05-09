
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

from STGraphics import convertBMP, fill, blit, blitRotate, display, update

import perf

# BITMAP: width: 25, height: 12
bmpShip = [bytearray([0, 0, 0, 108, 100, 150, 6, 156, 12, 154, 150, 100, 248, 240, 96, 240, 240, 12, 108, 248, 96, 96, 0, 0, 0,
           0, 0, 0, 3, 2, 6, 6, 3, 3, 5, 6, 2, 1, 0, 0, 0, 0, 3, 3, 1, 0, 0, 0, 0, 0]),
           bytearray([0, 12, 12, 104, 108, 254, 254, 240, 240, 240, 244, 244, 248, 240, 240, 144, 144, 252, 156, 252, 240, 240, 0, 0, 0,
                      0, 3, 3, 1, 3, 7, 7, 0, 0, 0, 2, 2, 1, 0, 0, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0])]
bmpShipMask = bytearray([12, 158, 158, 254, 254, 255, 255, 255, 255, 255, 255, 254, 254, 248, 248, 252, 252, 254, 254, 254, 252, 248, 248, 248, 240,
                         3, 7, 7, 7, 7, 15, 15, 15, 15, 15, 15, 7, 7, 1, 1, 3, 3, 7, 7, 7, 3, 1, 1, 1, 0])

buffer = bytearray(72*40)

impShip = convertBMP(25, 12, bmpShip, bmpShipMask)

angle = 0
pivotX = 12
pivotFwd = True
x, y = 18-(25 >> 1), 20-(12 >> 1)
while True:
    angle = (angle + 5) % 360
    # if buttonU.justPressed():
    #     angle = (angle + 5) % 360
    # if buttonD.justPressed():
    #     angle = (angle + 360 - 5) % 360
    # print(angle)

    if pivotFwd:
        pivotX += 1
        if pivotX >= 24:
            pivotFwd = False
    else:
        pivotX -= 1
        if pivotX <= 0:
            pivotFwd = True
    # if buttonL.justPressed():
    #     pivotX -= 1
    # if buttonR.justPressed():
    #     pivotX += 1
    # print(pivotX)

    if buttonU.pressed():
        y -= 1
    if buttonD.pressed():
        y += 1
    if buttonL.pressed():
        x -= 1
    if buttonR.pressed():
        x += 1

    # perf.start()
    # impShip = convertBMP(25, 12, bmpShip, bmpShipMask)
    # perf.stop()

    perf.start()
    fill(buffer, 0b10)
    perf.stop()

    perf.start()
    blit(buffer, impShip, x, y, 25, 12)
    perf.stop()

    perf.start()
    blitRotate(buffer, impShip, angle, 42, 14, 25, 12, pivotX, 6)
    perf.stop()

    perf.start()
    display(buffer)
    perf.stop()

    perf.render()

    update()

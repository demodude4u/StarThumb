import random

from thumbyGrayscale import display, Sprite
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

import perf

display.setFPS(30)

# Based on Corner-2 tiles http://www.cr31.co.uk/stagecast/wang/2corn.html
CORNER_NE = const(0b0001)
CORNER_SE = const(0b0010)
CORNER_SW = const(0b0100)
CORNER_NW = const(0b1000)

# BITMAP: width: 32, height: 32
bmpTiles = [bytearray([243, 243, 243, 227, 7, 15, 255, 255, 255, 255, 0, 0, 255, 255, 255, 255, 255, 255, 255, 255, 252, 248, 241, 243, 243, 243, 243, 243, 243, 243, 243, 243,
                       207, 143, 31, 63, 252, 248, 241, 243, 243, 241, 248, 252, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 63, 31, 143, 207,
                       255, 255, 240, 224, 199, 207, 207, 207, 207, 207, 207, 207, 207, 207, 207, 207, 207, 143, 31, 63, 255, 255, 255, 255, 255, 255, 255, 255, 0, 0, 255, 255,
                       255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 15, 7, 227, 243, 243, 243, 243, 241, 248, 252, 63, 31, 143, 207, 207, 207, 207, 199, 224, 240, 255, 255]),
            bytearray([248, 248, 248, 248, 240, 0, 0, 0, 0, 0, 0, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 254, 252, 248, 248, 248, 248, 248, 248, 248, 248, 248,
                       31, 63, 127, 255, 255, 254, 252, 248, 248, 252, 254, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 127, 63, 31,
                       0, 0, 0, 15, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 63, 127, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 240, 248, 248, 248, 248, 248, 252, 254, 255, 255, 127, 63, 31, 31, 31, 31, 31, 15, 0, 0, 0])]

sprTile = Sprite(8, 8, bmpTiles, 0, 0, 0b01, 0, 0)

colliders = [4, 3, 14, 6,
             10, 7, 15, 13,
             1, 9, 11, 12,
             0, 2, 5, 8]

# BITMAP: width: 5, height: 5
bmpO = bytearray([14, 17, 17, 17, 14])
# BITMAP: width: 5, height: 5
bmpX = bytearray([17, 10, 4, 10, 17])

map = bytearray(9*5)


def genMap():
    for row in range(5):
        for col in range(9):
            reqMask = 0b0000
            reqValue = 0b0000
            if row > 0:
                reqMask |= CORNER_NW | CORNER_NE
                adj = colliders[map[(row-1)*9+col]]
                reqValue |= (CORNER_NE if adj & CORNER_SE else 0) | (
                    CORNER_NW if adj & CORNER_SW else 0)
            if col > 0:
                reqMask |= CORNER_NW | CORNER_SW
                adj = colliders[map[row*9+(col-1)]]
                reqValue |= (CORNER_NW if adj & CORNER_NE else 0) | (
                    CORNER_SW if adj & CORNER_SE else 0)
            collider = (random.randrange(0, 16) & (15-reqMask)) | reqValue
            for i in range(16):
                if collider == colliders[i]:
                    map[row*9+col] = i
                    break


genMap()

cx, cy = 36, 20


while True:
    if buttonL.pressed() and cx > 0:
        cx -= 1
    if buttonR.pressed() and cx < 71:
        cx += 1
    if buttonU.pressed() and cy > 0:
        cy -= 1
    if buttonD.pressed() and cy < 39:
        cy += 1

    if buttonB.justPressed():
        genMap()

    display.fill(0b10)

    for row in range(5):
        for col in range(9):
            i = map[row*9+col]
            sprTile.x = col * 8
            sprTile.y = row * 8
            sprTile.setFrame(i)
            display.drawSprite(sprTile)

    perf.start()
    ccol = cx >> 3
    crow = cy >> 3
    if 0 <= ccol < 9 and 0 <= crow < 5:
        i = map[crow*9+ccol]
        collider = colliders[i]

        qx = (cx >> 2) & 0b1
        qy = (cy >> 2) & 0b1
        if qx:
            if qy:
                q = CORNER_SE
            else:
                q = CORNER_NE
        else:
            if qy:
                q = CORNER_SW
            else:
                q = CORNER_NW

        collided = collider & q
    else:
        collided = False
    perf.stop()

    display.blit(bmpX if collided else bmpO, cx-2, cy-2, 5, 5, 0, 0, 0)

    display.update()

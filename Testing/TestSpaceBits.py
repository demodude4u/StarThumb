import array
import math
import random

from thumbyGrayscale import display
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

import perf

display.setFPS(30)

# 0 = Black
# 1 = Dark Gray
# 2 = Light Gray
# 3 = White
COLORINDEX = bytes([0b00, 0b10, 0b11, 0b01])

# 16x16 cells, 6 columns, 4 rows ()
# Cell format: 4-bit x, 4-bit y
sbLayer1 = bytearray((random.randrange(0, 256) for _ in range(6*4)))
sbLayer2 = bytearray((random.randrange(0, 256) for _ in range(6*4)))


@micropython.viper
def sbRender(px: int, py: int, vx: int, vy: int):
    sb1 = ptr8(sbLayer1)
    sb2 = ptr8(sbLayer2)
    bufBW = ptr8(display.buffer)
    bufGS = ptr8(display.shading)

    if vx > 0:
        speed = vx
    else:
        speed = vx
    if vy > 0:
        speed += vy
    else:
        speed -= vy

    cShift = (px >> 4) % 6
    cPixel = px & 0b1111
    rShift = (py >> 4) % 4
    rPixel = py & 0b1111
    color = int(COLORINDEX[min(3, (speed+1) >> 1)])

    for sr in range(4):
        for sc in range(6):
            c = (sc + cShift) % 6
            r = (sr + rShift) % 4
            cell = sb1[r*6+c]
            cx = cell & 0b1111
            cy = (cell >> 4) & 0b1111
            x = sc * 16 + cx - cPixel
            y = sr * 16 + cy - rPixel
            if x < 0 or x >= 72 or y < 0 or y >= 40:
                continue
            so = (y >> 3) * 72 + x
            sm1 = 1 << (y & 7)
            sm0 = 255-sm1
            if color & 0b01:
                bufBW[so] |= sm1
            else:
                bufBW[so] &= sm0
            if color & 0b10:
                bufGS[so] |= sm1
            else:
                bufGS[so] &= sm0

    cShift = (px >> 5) % 6
    cPixel = (px >> 1) & 0b1111
    rShift = (py >> 5) % 4
    rPixel = (py >> 1) & 0b1111
    color = int(COLORINDEX[min(3, (speed+3) >> 2)])

    for sr in range(4):
        for sc in range(6):
            c = (sc + cShift) % 6
            r = (sr + rShift) % 4
            cell = sb2[r*6+c]
            cx = cell & 0b1111
            cy = (cell >> 4) & 0b1111
            x = sc * 16 + cx - cPixel
            y = sr * 16 + cy - rPixel
            if x < 0 or x >= 72 or y < 0 or y >= 40:
                continue
            so = (y >> 3) * 72 + x
            sm1 = 1 << (y & 7)
            sm0 = 255-sm1
            if color & 0b01:
                bufBW[so] |= sm1
            else:
                bufBW[so] &= sm0
            if color & 0b10:
                bufGS[so] |= sm1
            else:
                bufGS[so] &= sm0


dx = 1
dy = 0
sbPanX = 0
sbPanY = 0

while True:
    if buttonU.justPressed():
        dy -= 1
    if buttonD.justPressed():
        dy += 1
    if buttonL.justPressed():
        dx -= 1
    if buttonR.justPressed():
        dx += 1

    sbPanX = sbPanX + dx
    sbPanY = sbPanY + dy

    display.fill(0)
    perf.start()
    sbRender(sbPanX, sbPanY, dx, dy)
    perf.stop()
    display.update()

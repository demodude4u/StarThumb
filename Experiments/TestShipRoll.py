from sys import path as syspath  # NOQA
syspath.insert(0, '/Games/DemoST1Transport')  # NOQA

import math
import gc
import random

buffer = bytearray(72*40)

from TestPackReading import PackReader  # NOQA

with PackReader("/Games/TestShipRoll/TestShipRoll.pack") as pack:
    shader = pack.readShader()

    impShipSkull = pack.readIMP()
    impShipSkullTop = pack.readIMP()

pack.file = None
pack = None
gc.collect()

from thumbyGrayscale import display as GSdisplay  # NOQA
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR  # NOQA

gc.collect()

GSdisplay.setFPS(30)

BUF_W = const(72)
BUF_H = const(40)
BUF_SIZE = const(BUF_W * BUF_H)
BUF_SIZE_INT = const(BUF_SIZE >> 2)
IMP_ALPHA = const(0b10000000)


@micropython.viper
def fill(buffer: ptr32, color: int):
    c4 = (color << 24) | (color << 16) | (color << 8) | color
    for i in range(BUF_SIZE_INT):
        buffer[i] = c4


@micropython.viper
def postShading(buffer: ptr8, shader: ptr16, light: int):
    width = 72
    height = 40

    pixel_count = width * height

    df = True
    for i in range(pixel_count):
        pixel = buffer[i]

        if not pixel & 0b10000000:  # Transparent
            continue

        if not pixel & 0b01000000:  # Flat
            continue

        shading_rule = shader[pixel & 0b111]
        normal = (pixel >> 3) & 0b111

        shading_color = (shading_rule >> (
            2 * ((light - normal + 8) & 0b111))) & 0x03

        if df and (pixel & 0b111 == 0b011) and (normal == 0):
            df = False

        buffer[i] = (pixel & 0b11111100) | shading_color


@micropython.viper
def display(buffer: ptr32):
    scrBW = ptr8(GSdisplay.buffer)
    scrGS = ptr8(GSdisplay.shading)
    bi = 0
    so = 0
    for _ in range(0, 40, 8):
        for _ in range(0, 72):
            v1 = buffer[bi]
            bi += 1
            v2 = buffer[bi]
            bi += 1
            scrBW[so] = ((v1 & 0x00000001) << 0) | ((v1 & 0x00000100) >> 7) | \
                ((v1 & 0x00010000) >> 14) | ((v1 & 0x01000000) >> 21) | \
                ((v2 & 0x00000001) << 4) | ((v2 & 0x00000100) >> 3) | \
                ((v2 & 0x00010000) >> 10) | ((v2 & 0x01000000) >> 17)
            scrGS[so] = ((v1 & 0x00000002) >> 1) | ((v1 & 0x00000200) >> 8) | \
                ((v1 & 0x00020000) >> 15) | ((v1 & 0x02000000) >> 22) | \
                ((v2 & 0x00000002) << 3) | ((v2 & 0x00000200) >> 4) | \
                ((v2 & 0x00020000) >> 11) | ((v2 & 0x02000000) >> 18)
            so += 1


@micropython.viper
def blitRoll(buffer: ptr8, imp: ptr8, roll_f6: int,
             x: int, y: int, w: int, h: int, pivotX: int, pivotY: int, dir: int = 0):
    for srcY in range(h):
        for srcX in range(w):
            v = imp[((srcY >> 3)*w+srcX)*8+(srcY & 0b111)]
            if not v & IMP_ALPHA:
                continue

            dx = srcX - pivotX
            dy = srcY - pivotY

            # rx = (scale_f6 * dx) >> 6
            rx = dx
            ry = ((32-roll_f6) * dy) >> 5

            if dir == 0:
                pass
            elif dir == 1:
                rx, ry = 0-ry, rx
            elif dir == 2:
                rx, ry = 0-rx, 0-ry
            else:  # dir == 3
                rx, ry = ry, 0-rx

            rx += pivotX
            ry += pivotY

            dstX = x + rx
            dstY = y + ry

            if 0 <= dstX < 72 and 0 <= dstY < 40:
                buffer[((dstY >> 3)*72+dstX)*8+(dstY & 0b111)] = v


@micropython.viper
def blitRoll2(buffer: ptr8, imp: ptr8, roll_f6: int,
              x: int, y: int, w: int, h: int, pivotX: int, pivotY: int, dir: int = 0):
    if roll_f6 >= 32:
        roll_f6 = 64 - roll_f6
    for srcY in range(h):
        for srcX in range(w):
            v = imp[((srcY >> 3)*w+srcX)*8+(srcY & 0b111)]
            if not v & IMP_ALPHA:
                continue

            dx = srcX - pivotX
            dy = srcY - pivotY

            # rx = (scale_f6 * dx) >> 6
            rx = dx
            ry = (roll_f6 * dy) >> 5

            if dir == 0:
                pass
            elif dir == 1:
                rx, ry = 0-ry, rx
            elif dir == 2:
                rx, ry = 0-rx, 0-ry
            else:  # dir == 3
                rx, ry = ry, 0-rx

            rx += pivotX
            ry += pivotY

            dstX = x + rx
            dstY = y + ry

            if 0 <= dstX < 72 and 0 <= dstY < 40:
                buffer[((dstY >> 3)*72+dstX)*8+(dstY & 0b111)] = v


roll_f6 = 0
lightAngle = 0

while True:

    if buttonR.pressed() and roll_f6 < 61:
        roll_f6 += 4
    if buttonL.pressed() and roll_f6 > 3:
        roll_f6 -= 4

    if buttonA.justPressed():
        lightAngle = (lightAngle + 1) % 8

    fill(buffer, 0b00)

    if 10 < roll_f6 < 54:
        imp, iw, ih = impShipSkullTop
        blitRoll2(buffer, imp, roll_f6, 36-18-(iw >> 1), 20+3 -
                  (ih >> 1), iw, ih, iw >> 1, ih >> 1, 0)
        blitRoll2(buffer, imp, roll_f6, 36+18-(iw >> 1), 20+10 -
                  (ih >> 1), iw, ih, iw >> 1, ih >> 1, 0)

    imp, iw, ih = impShipSkull
    blitRoll(buffer, imp, roll_f6, 36-18-(iw >> 1), 20 -
             (ih >> 1), iw, ih, iw >> 1, (ih >> 1) + 3, 0)
    blitRoll(buffer, imp, roll_f6, 36+18-(iw >> 1), 20-10 -
             (ih >> 1), iw, ih, iw >> 1, (ih >> 1) + 3, 0)

    postShading(buffer, shader, lightAngle)
    display(buffer)
    GSdisplay.update()

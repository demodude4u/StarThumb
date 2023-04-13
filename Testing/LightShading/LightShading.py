from sys import path as syspath  # NOQA
syspath.insert(0, '/Games/LightShading')  # NOQA

import array

from thumbyGrayscale import display
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

import perf

# 0 = Black
# 1 = Dark Gray
# 2 = Light Gray
# 3 = White
ColorIndex = [0b00, 0b10, 0b11, 0b01]


def S(a0, a45, a90, a135, a180):
    return (ColorIndex[a180] << 8) | (ColorIndex[a135] << 6) | (ColorIndex[a90] << 4) | (ColorIndex[a45] << 2) | ColorIndex[a0]


# Shading angles [0, 45, 90, 135, 180] of color -> 10 bits of 2-bit grayscale
shading = array.array("H", [
    S(3, 3, 3, 3, 3),  # 0 Unlit White
    S(2, 2, 2, 2, 2),  # 1 Unlit Light
    S(1, 1, 1, 1, 1),  # 2 Unlit Dark
    S(0, 0, 0, 0, 0),  # 3 Unlit Black
    S(3, 3, 2, 1, 1),  # 4 Matte Light
    S(2, 2, 1, 0, 0),  # 5 Matte Dark
    S(3, 2, 2, 1, 1),  # 6 Shiny Light
    S(3, 1, 1, 0, 0),  # 7 Shiny Dark
    S(3, 0, 0, 0, 0),  # 8 Shiny Black
])


def M(shadingIndex, rotation=0):
    return (shadingIndex << 4) | rotation


# Materials
material = bytearray([
    M(0),  # 0
    M(1),  # 1
    M(2),  # 2
    M(3),  # 3
    M(4, 0), M(4, 1), M(4, 2), M(4, 3),  # 4 5 6 7
    M(4, 4), M(4, 5), M(4, 6), M(4, 7),  # 8 9 10 11
    M(5, 0), M(5, 1), M(5, 2), M(5, 3),  # 12 13 14 15
    M(5, 4), M(5, 5), M(5, 6), M(5, 7),  # 16 17 18 19
    M(6, 0), M(6, 1), M(6, 2), M(6, 3),  # 20 21 22 23
    M(6, 4), M(6, 5), M(6, 6), M(6, 7),  # 24 25 26 27
    M(7, 0), M(7, 1), M(7, 2), M(7, 3),  # 28 29 30 31
    M(7, 4), M(7, 5), M(7, 6), M(7, 7),  # 32 33 34 35
    M(8, 0), M(8, 1), M(8, 2), M(8, 3),  # 36 37 38 39
    M(8, 4), M(8, 5), M(8, 6), M(8, 7),  # 40 41 42 43
])
materialName = [
    "UNLIT W",
    "UNLIT L",
    "UNLIT D",
    "UNLIT B",
    "MATTE L E", "MATTE L SE", "MATTE L S", "MATTE L SW",
    "MATTE L W", "MATTE L NW", "MATTE L N", "MATTE L NE",
    "MATTE D E", "MATTE D SE", "MATTE D S", "MATTE D SW",
    "MATTE D W", "MATTE D NW", "MATTE D N", "MATTE D NE",
    "SHINY L E", "SHINY L SE", "SHINY L S", "SHINY L SW",
    "SHINY L W", "SHINY L NW", "SHINY L N", "SHINY L NE",
    "SHINY D E", "SHINY D SE", "SHINY D S", "SHINY D SW",
    "SHINY D W", "SHINY D NW", "SHINY D N", "SHINY D NE",
    "SHINY B E", "SHINY B SE", "SHINY B S", "SHINY B SW",
    "SHINY B W", "SHINY B NW", "SHINY B N", "SHINY B NE",
]
materialLightAngles = array.array("H")
for i in range(len(material)):
    v = 0
    m = material[i]
    si, r = (m >> 4) & 0b1111, m & 0b1111
    s = shading[si]
    sa0 = s & 0b11
    sa45 = (s >> 2) & 0b11
    sa90 = (s >> 4) & 0b11
    sa135 = (s >> 6) & 0b11
    sa180 = (s >> 8) & 0b11
    mla = (sa45 << 14) | (sa90 << 12) | (sa135 << 10) | (
        sa180 << 8) | (sa135 << 6) | (sa90 << 4) | (sa45 << 2) | sa0
    materialLightAngles.append((mla << (r*2)) | (mla >> (16-(r*2))))


class LSBitmap:
    def __init__(self, width: int, height: int, palette, pixels):
        self.width = width
        self.height = height
        self.palette = palette
        if isinstance(pixels, str):
            pixels = pixels.replace(" ", "")
            self.pixels = bytes([int(pixels[i:i+2], 16)
                                for i in range(0, len(pixels), 2)])
        else:
            self.pixels = pixels

    @micropython.viper
    def blit(self, x: int, y: int, lightAngle: int):
        bw, bh = int(self.width), int(self.height)
        if x + bw < 0 or x >= 72 or y + bh < 0 or y >= 40:
            return

        bufBW = ptr8(display.buffer)
        bufGS = ptr8(display.shading)
        pal = ptr8(self.palette)
        pix = ptr8(self.pixels)
        mla = ptr16(materialLightAngles)

        sx1, sx2 = int(max(0, x)), int(min(72, x+bw))
        sy1, sy2 = int(max(0, y)), int(min(40, y+bh))

        by = sy1 - y
        for sy in range(sy1, sy2):
            bx = sx1 - x
            byi = by * (bw//2)
            for sx in range(sx1, sx2):
                if bx & 0b1:
                    pali = pix[byi+(bx//2)] & 0b1111
                else:
                    pali = (pix[byi+(bx//2)] >> 4) & 0b1111
                if not pali:
                    bx += 1
                    continue
                palv = pal[pali-1]
                mlav = mla[palv]
                c = (mlav >> (lightAngle*2)) & 0b11
                so = (sy >> 3) * 72 + sx
                sm1 = 1 << (sy & 7)
                sm0 = 255-sm1
                # print(pali, palv, mlav, c, so, sm1, sm0)
                if c & 0b01:
                    bufBW[so] |= sm1
                else:
                    bufBW[so] &= sm0
                if c & 0b10:
                    bufGS[so] |= sm1
                else:
                    bufGS[so] &= sm0
                bx += 1
            by += 1


def P(px1, px2):
    return (px1 << 4) | px2


buttonPixels = "\
    00077000\
    00677800\
    06699880\
    55999911\
    55999911\
    04499220\
    00433200\
    00033000"

bmpMatteLButton = LSBitmap(8, 8, bytearray(
    [4, 5, 6, 7, 8, 9, 10, 11, 1]), buttonPixels)
bmpMatteDButton = LSBitmap(8, 8, bytearray(
    [12, 13, 14, 15, 16, 17, 18, 19, 2]), buttonPixels)
bmpShinyLButton = LSBitmap(8, 8, bytearray(
    [20, 21, 22, 23, 24, 25, 26, 27, 1]), buttonPixels)
bmpShinyDButton = LSBitmap(8, 8, bytearray(
    [28, 29, 30, 31, 32, 33, 34, 35, 2]), buttonPixels)
bmpShinyBButton = LSBitmap(8, 8, bytearray(
    [36, 37, 38, 39, 40, 41, 42, 43, 3]), buttonPixels)

bmpShipN = LSBitmap(6, 6, bytearray([4, 8]), "\
    002100\
    002100\
    022110\
    022110\
    220011\
    200001")
bmpShip2N = LSBitmap(6, 6, bytearray([4, 8, 1, 6, 9, 11, 7, 5]), "\
    005600\
    002100\
    052160\
    027810\
    570086\
    200001")

bmpShip3W = LSBitmap(14, 8, bytearray([4, 5, 6, 7, 8, 9, 10, 11, 1, 2, 41, 40, 39]), "\
    00677800677778\
    06BB7880433332\
    6BB9988800AA00\
    5CC99111AAAA00\
    5CC99111AAAA00\
    4DD9922200AA00\
    04DD3220677778\
    00433200433332")

bmpShip4W = LSBitmap(16, 12, bytearray([4, 5, 6, 7, 8, 9, 10, 11, 1, 2, 41, 40, 39, 3]), "\
    0000000009999990\
    0000000000678000\
    0000000066780000\
    0000009997780000\
    0600000999900000\
    59E677E99E680000\
    59E433E99E420000\
    0400000999900000\
    0000009993320000\
    0000000044320000\
    0000000000432000\
    0000000009999990\
    ")

lightAngle = 0
bgColor = 0

# BITMAP: width: 5, height: 5
bmpArrowN = bytearray([4, 2, 31, 2, 4])
bmpArrowNE = bytearray([17, 9, 5, 3, 31])
bmpArrowE = bytearray([4, 4, 21, 14, 4])
debugArrow = [
    (bmpArrowE, 1, 0),
    (bmpArrowNE, 1, 0),
    (bmpArrowN, 0, 0),
    (bmpArrowNE, 0, 0),
    (bmpArrowE, 0, 0),
    (bmpArrowNE, 0, 1),
    (bmpArrowN, 0, 1),
    (bmpArrowNE, 1, 1)
]

while True:
    if buttonR.justPressed():
        lightAngle = (lightAngle + 1) % 8
    if buttonL.justPressed():
        lightAngle = (lightAngle + 7) % 8
    if buttonD.justPressed():
        bgColor = (bgColor + 1) % 4
    if buttonU.justPressed():
        bgColor = (bgColor + 3) % 4

    display.fill(ColorIndex[bgColor])

    dbBmp, dbMirX, dbMirY = debugArrow[lightAngle]
    display.blit(dbBmp, 0, 35, 5, 5, 0, dbMirX, dbMirY)

    perf.start()

    # bmpMatteLButton.blit(28, 12, lightAngle)
    # bmpMatteDButton.blit(38, 12, lightAngle)
    # bmpShinyLButton.blit(22, 22, lightAngle)
    # bmpShinyDButton.blit(32, 22, lightAngle)
    # bmpShinyBButton.blit(42, 22, lightAngle)

    # bmpShipN.blit(29, 17, lightAngle)
    # bmpShip2N.blit(37, 17, lightAngle)

    # bmpShip3W.blit(31, 16, lightAngle)

    bmpShip4W.blit(30, 14, lightAngle)

    perf.stop()

    display.update()

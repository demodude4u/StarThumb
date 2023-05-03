import array

from thumbyGrayscale import display
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

import perf

display.setFPS(30)


@micropython.viper
def blitDirect(bmp, x: int, y: int, w: int, h: int):
    scrBW = ptr8(display.buffer)
    scrGS = ptr8(display.shading)

    bmpBW = ptr8(bmp[0])
    bmpGS = ptr8(bmp[1])

    sx1, sx2 = int(max(0, x)), int(min(72, x+w))
    sy1, sy2 = int(max(0, y)), int(min(40, y+h))

    by = sy1 - y
    for sy in range(sy1, sy2):
        bx = sx1 - x
        for sx in range(sx1, sx2):
            bo = (by >> 3) * w + bx
            bm = 1 << (by & 7)
            so = (sy >> 3) * 72 + sx
            sm1 = 1 << (sy & 7)
            sm0 = 255-sm1
            if bmpBW[bo] & bm:
                scrBW[so] |= sm1
            else:
                scrBW[so] &= sm0
            if bmpGS[bo] & bm:
                scrGS[so] |= sm1
            else:
                scrGS[so] &= sm0
            bx += 1
        by += 1


@micropython.viper
def blitBuffered(buffer: ptr8, imp: ptr8, x: int, y: int, w: int, h: int):
    sx1, sx2 = int(max(0, x)), int(min(72, x+w))
    sy1, sy2 = int(max(0, y)), int(min(40, y+h))

    w = sx2 - sx1
    h = sy2 - sy1

    sx = sx1
    for ix in range(w):
        sy = sy1
        for iy in range(h):
            buffer[((sy >> 3)*72+sx)*8+(sy & 0b111)
                   ] = imp[((iy >> 3)*w+ix)*8+(iy & 0b111)]
            sy += 1
        sx += 1


@micropython.viper
def bufferToScreen(buffer: ptr32):
    scrBW = ptr8(display.buffer)
    scrGS = ptr8(display.shading)

    bi = 0
    so = 0
    for rowY in range(0, 40, 8):
        for x in range(0, 72):
            vBW = 0
            vGS = 0
            vm = 1
            for _ in range(2):
                v = buffer[bi]
                bi += 1
                if v & 0x00000001:
                    vBW |= vm
                if v & 0x00000002:
                    vGS |= vm
                vm <<= 1
                if v & 0x00000100:
                    vBW |= vm
                if v & 0x00000200:
                    vGS |= vm
                vm <<= 1
                if v & 0x00010000:
                    vBW |= vm
                if v & 0x00020000:
                    vGS |= vm
                vm <<= 1
                if v & 0x01000000:
                    vBW |= vm
                if v & 0x02000000:
                    vGS |= vm
                vm <<= 1
            scrBW[so] = vBW
            scrGS[so] = vGS
            so += 1


@micropython.viper
def bufferFill(buffer: ptr32, color: int):
    c4 = (color << 24) | (color << 16) | (color << 8) | color
    for i in range(720):
        buffer[i] = c4


# BITMAP: width: 49, height: 23
bmpShip = [bytearray([0, 0, 128, 128, 160, 224, 208, 192, 144, 56, 56, 60, 60, 60, 90, 90, 90, 86, 78, 30, 190, 62, 28, 216, 216, 192, 128, 128, 128, 128, 128, 128, 0, 136, 216, 216, 208, 64, 72, 80, 128, 128, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 128, 128, 128, 156, 182, 182, 156, 73, 107, 42, 42, 42, 107, 42, 8, 73, 107, 107, 235, 107, 28, 156, 213, 255, 255, 255, 182, 182, 247, 182, 85, 190, 128, 170, 190, 127, 127, 127, 190, 190, 62, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 2, 3, 5, 1, 4, 14, 14, 30, 30, 30, 45, 45, 45, 53, 57, 60, 62, 62, 28, 13, 13, 1, 0, 0, 0, 0, 0, 0, 0, 8, 13, 13, 5, 1, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
           bytearray([199, 23, 195, 227, 243, 251, 235, 123, 123, 89, 93, 92, 92, 76, 40, 40, 40, 34, 40, 152, 184, 184, 144, 209, 211, 195, 223, 191, 63, 15, 175, 167, 179, 187, 211, 219, 219, 219, 219, 211, 135, 159, 31, 159, 63, 191, 63, 127, 255,
                      255, 62, 190, 128, 190, 190, 190, 62, 62, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 255, 255, 255, 255, 227, 255, 235, 213, 182, 127, 107, 235, 235, 235, 247, 255, 255, 235, 255, 255, 255, 247, 247, 85, 128, 127, 162, 99, 62, 128,
                      113, 116, 97, 99, 103, 111, 107, 111, 111, 77, 93, 29, 29, 25, 10, 10, 10, 34, 10, 12, 14, 14, 4, 69, 101, 97, 125, 124, 126, 120, 122, 114, 102, 110, 101, 109, 109, 109, 109, 101, 112, 124, 124, 124, 126, 126, 126, 127, 127])]


# 8-bit indexed, VLSB pixel order
def convertBMPtoIMP(width, height, bmp):
    paddedHeight = 8 * ((height + 7) // 8)
    ret = bytearray(width * paddedHeight)
    i = 0
    for rowY in range(0, height, 8):
        for x in range(width):
            o = (rowY >> 3) * width + x
            m = 1
            for _ in range(8):
                ret[i] = (0b10 if (bmp[1][o] & m) else 0) | (
                    0b01 if (bmp[0][o] & m) else 0)
                m <<= 1
                i += 1
    return ret


impShip = convertBMPtoIMP(49, 23, bmpShip)

buffer = bytearray(72*40)

rmode = 0
while True:
    if buttonA.justPressed():
        rmode = (rmode + 1) % 2

    if rmode == 0:
        display.fill(0b10)
        perf.start()
        blitDirect(bmpShip, 36-49//2, 20-23//2, 49, 23)
        perf.stop()

    else:
        bufferFill(buffer, 0b11)
        perf.start()
        blitBuffered(buffer, impShip, 36-49//2, 20-23//2, 49, 23)
        bufferToScreen(buffer)
        perf.stop()

    display.update()

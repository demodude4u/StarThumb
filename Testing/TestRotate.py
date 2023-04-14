# - Based on the shear rotation algorithm used back when blit /w shear was a fast operation

import math
from array import array
import utime

from thumbyGrayscale import display
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

import perf

display.setFPS(30)

# Precompute fixed-point tan and sin values for angles between -90 and 90 degrees
tan_values = array('i', [int(math.tan(math.radians(x / 2))
                   * 1024) for x in range(-90, 91)])
sin_values = array('i', [int(math.sin(math.radians(x))
                   * 1024) for x in range(-90, 91)])
cos_values = array('i', [int(math.cos(math.radians(x))
                   * 1024) for x in range(-90, 91)])


# BITMAP: width: 32, height: 32
bmpShip = [bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
           0, 0, 0, 0, 0, 0, 176, 144, 88, 24, 112, 48, 104, 88, 144, 224, 192, 128, 192, 192, 48, 176, 224, 128, 128, 0, 0, 0, 0, 0, 0, 0,
           0, 0, 0, 0, 0, 0, 13, 9, 26, 24, 14, 12, 22, 26, 9, 7, 3, 1, 3, 3, 12, 13, 7, 1, 1, 0, 0, 0, 0, 0, 0, 0,
           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
           bytearray([255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255,
                      255, 255, 255, 135, 183, 183, 167, 179, 251, 251, 195, 195, 195, 211, 211, 231, 207, 223, 79, 71, 247, 119, 247, 199, 223, 31, 31, 63, 255, 255, 255, 255,
                      255, 255, 255, 225, 237, 237, 229, 205, 223, 223, 195, 195, 195, 203, 203, 231, 243, 251, 242, 226, 239, 238, 239, 227, 251, 248, 248, 252, 255, 255, 255, 255,
                      255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255])]


def convertBMPtoIMP(width, height, bmp):
    ret = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            o = (y >> 3) * width + x
            m = 1 << (y & 7)
            ret[y * width + x] = (0b10 if (bmp[1][o] & m)
                                  else 0) | (0b01 if (bmp[0][o] & m) else 0)
    return (ret, width, height)

# impShip = convertBMPtoIMP(25, 12, [bytearray([0,0,0,108,100,150,6,156,12,154,150,100,248,240,96,240,240,12,108,248,96,96,0,0,0,
#           0,0,0,3,2,6,6,3,3,5,6,2,1,0,0,0,0,3,3,1,0,0,0,0,0]),
#             bytearray([243,109,109,105,109,254,254,240,240,240,244,245,249,247,247,147,147,253,157,253,243,247,7,7,15,
#           12,11,11,9,11,7,7,0,0,0,2,10,9,14,14,12,12,11,11,11,12,14,14,14,15])])


impShip = convertBMPtoIMP(49, 23, [bytearray([0, 0, 128, 128, 160, 224, 208, 192, 144, 56, 56, 60, 60, 60, 90, 90, 90, 86, 78, 30, 190, 62, 28, 216, 216, 192, 128, 128, 128, 128, 128, 128, 0, 136, 216, 216, 208, 64, 72, 80, 128, 128, 0, 0, 0, 0, 0, 0, 0,
                                              0, 0, 128, 128, 128, 156, 182, 182, 156, 73, 107, 42, 42, 42, 107, 42, 8, 73, 107, 107, 235, 107, 28, 156, 213, 255, 255, 255, 182, 182, 247, 182, 85, 190, 128, 170, 190, 127, 127, 127, 190, 190, 62, 0, 0, 0, 0, 0, 0,
                                              0, 0, 0, 0, 2, 3, 5, 1, 4, 14, 14, 30, 30, 30, 45, 45, 45, 53, 57, 60, 62, 62, 28, 13, 13, 1, 0, 0, 0, 0, 0, 0, 0, 8, 13, 13, 5, 1, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0]), bytearray([199, 23, 195, 227, 243, 251, 235, 123, 123, 89, 93, 92, 92, 76, 40, 40, 40, 34, 40, 152, 184, 184, 144, 209, 211, 195, 223, 191, 63, 15, 175, 167, 179, 187, 211, 219, 219, 219, 219, 211, 135, 159, 31, 159, 63, 191, 63, 127, 255,
                                                                                                                                                                                                                                255, 62, 190, 128, 190, 190, 190, 62, 62, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 255, 255, 255, 255, 227, 255, 235, 213, 182, 127, 107, 235, 235, 235, 247, 255, 255, 235, 255, 255, 255, 247, 247, 85, 128, 127, 162, 99, 62, 128,
                                                                                                                                                                                                                                113, 116, 97, 99, 103, 111, 107, 111, 111, 77, 93, 29, 29, 25, 10, 10, 10, 34, 10, 12, 14, 14, 4, 69, 101, 97, 125, 124, 126, 120, 122, 114, 102, 110, 101, 109, 109, 109, 109, 101, 112, 124, 124, 124, 126, 126, 126, 127, 127])])


@micropython.viper
def blitRotated(imp: ptr8, angle: int, x: int, y: int, width: int, height: int, px: int, py: int):
    bufBW = ptr8(display.buffer)
    bufGS = ptr8(display.shading)

    if angle <= 90:
        ra, mx = angle, 0
    elif angle <= 270:
        ra, mx = 180 - angle, 1
    else:
        ra, mx = angle - 360, 0

    cw = width // 2
    ch = height // 2

    # Determine rendering mode
    if 10 < ra < 80 or -80 < ra < -10:
        rmode = 0
        shx = int(-tan_values[ra + 90])
        shy = int(sin_values[ra + 90])
    elif ra == 0:
        rmode = 1
    elif ra == 90:
        rmode = 2
    elif ra == -90:
        rmode = 3
    else:
        rmode = 4
        cos = int(cos_values[ra + 90])
        sin = int(sin_values[ra + 90])

    for sy in range(height):
        for sx in range(width):
            if rmode == 0:  # Shear-based rotation for larger angles
                dx = sx - px
                dy = sy - py

                h_shear_x = dx + (dy * shx) // 1024
                ry = dy + (h_shear_x * shy) // 1024
                rx = h_shear_x + (ry * shx) // 1024

                rx += px
                ry += py

            elif rmode == 1:  # No rotation
                rx = sx
                ry = sy

            elif rmode == 2:  # Quick rotate 90
                rx = px + sy - py
                ry = py + sx - px

            elif rmode == 3:  # Quick rotate -90
                rx = px + sy - py
                ry = py - sx + px

            elif rmode == 4:  # Nearest-neighbor rotation for smaller angles
                dx = sx - cw
                dy = sy - ch

                rx = (cos * dx - sin * dy) // 1024
                ry = (cos * dy + sin * dx) // 1024

                rx += cw
                ry += ch

            if mx:
                dstX = x + (width - rx)
            else:
                dstX = x + rx
            dstY = y + ry

            if 0 <= dstX < 72 and 0 <= dstY < 40:
                c = imp[sy*width+sx]
                o = (dstY >> 3) * 72 + dstX
                m1 = 1 << (dstY & 7)
                m0 = 255-m1
                if c & 0b01:
                    bufBW[o] |= m1
                else:
                    bufBW[o] &= m0
                if c & 0b10:
                    bufGS[o] |= m1
                else:
                    bufGS[o] &= m0


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

target = 0
rotateSpeed = 5
angle = 0
arrow = 4
while True:

    if buttonR.pressed():
        target = 0
        arrow = 4
    if buttonD.pressed():
        target = 90
        arrow = 6
    if buttonL.pressed():
        target = 180
        arrow = 0
    if buttonU.pressed():
        target = 270
        arrow = 2

    diff = target - angle
    diff = (diff + 180) % 360 - 180
    diff = max(-rotateSpeed, min(rotateSpeed, diff))
    angle = (angle + diff + 360) % 360

    display.fill(0b10)

    dbBmp, dbMirX, dbMirY = debugArrow[arrow]
    display.blit(dbBmp, 0, 35, 5, 5, 0, dbMirX, dbMirY)

    perf.start()
    imp, iw, ih = impShip
    blitRotated(imp, angle, 36-iw//2, 20-ih//2, iw, ih, iw//2, ih//2)
    perf.stop()

    display.update()

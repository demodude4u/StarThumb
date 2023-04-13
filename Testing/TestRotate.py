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


# Convert VLSB-GS format to 8-bit indexed
impShip = bytearray(32*32)
impRotated = bytearray(32*32)
for y in range(32):
    for x in range(32):
        o = (y >> 3) * 32 + x
        m = 1 << (y & 7)
        impShip[y*32+x] = (0b10 if (bmpShip[1][o] & m)
                           else 0) | (0b01 if (bmpShip[0][o] & m) else 0)

# Angle: [-90 to 90]
# TODO automatic mirroring for >90 degrees


@micropython.viper
def rotate_sprite(src: ptr8, dst: ptr8, angle: int, size: int):

    # Calculate the center of the sprite
    cs = size // 2

    if 10 < angle < 80 or -80 < angle < -10:  # Use shear-based rotation for larger angles

        # Get the fixed-point tan and sin values from the precomputed lookup table
        shx = int(-tan_values[angle + 90])
        shy = int(sin_values[angle + 90])

        for y in range(size):
            for x in range(size):
                # Translate the coordinates to the origin
                dx = x - cs
                dy = y - cs

                # Compute the horizontal shear
                h_shear_x = dx + (dy * shx) // 1024

                # Compute the vertical shear
                new_y = dy + (h_shear_x * shy) // 1024

                # Compute the final horizontal shear
                new_x = h_shear_x + (new_y * shx) // 1024

                # Translate back to the original position
                new_x += cs
                new_y += cs

                # If new_x and new_y are within bounds, copy pixel to rotated sprite
                if 0 <= new_x < size and 0 <= new_y < size:
                    dst[new_y * size + new_x] = src[y * size + x]

    elif angle == 0:  # Copy if there is no rotation
        for i in range(size*size):
            dst[i] = src[i]

    elif angle == 90:  # Quick rotate
        for y in range(size):
            for x in range(size):
                dst[x * size + y] = src[y * size + x]

    elif angle == -90:  # Quick rotate
        for y in range(size):
            for x in range(size):
                dst[x * size + y] = src[y * size + (31-x)]

    else:  # Use nearest-neighbor rotation for smaller angles
        # Get the fixed-point cos value from the precomputed lookup table
        c = int(cos_values[angle + 90])
        s = int(sin_values[angle + 90])

        for y in range(size):
            for x in range(size):
                # Translate the coordinates to the origin
                dx = x - cs
                dy = y - cs

                # Compute the rotated coordinates using the nearest-neighbor rotation
                new_x = (c * dx - s * dy) // 1024
                new_y = (c * dy + s * dx) // 1024

                # Translate back to the original position
                new_x += cs
                new_y += cs

                # If new_x and new_y are within bounds, copy pixel to rotated sprite
                if 0 <= new_x < size and 0 <= new_y < size:
                    dst[new_y * size + new_x] = src[y * size + x]


@micropython.viper
def blitIndexed(imp: ptr8, x: int, y: int, width: int, height: int, mirrorX: int, mirrorY: int):
    bufBW = ptr8(display.buffer)
    bufGS = ptr8(display.shading)

    sx1, sx2 = int(max(0, x)), int(min(72, x+width))
    sy1, sy2 = int(max(0, y)), int(min(40, y+height))

    bdx = -1 if mirrorX else 1
    bdy = -1 if mirrorY else 1

    bsx = (sx2 - x - 1) if mirrorX else sx1 - x
    by = (sy2 - y - 1) if mirrorY else sy1 - y
    for sy in range(sy1, sy2):
        bx = bsx
        for sx in range(sx1, sx2):
            c = imp[by*width+bx]
            so = (sy >> 3) * 72 + sx
            sm1 = 1 << (sy & 7)
            sm0 = 255-sm1
            if c & 0b01:
                bufBW[so] |= sm1
            else:
                bufBW[so] &= sm0
            if c & 0b10:
                bufGS[so] |= sm1
            else:
                bufGS[so] &= sm0
            bx += bdx
        by += bdy


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

    if angle <= 90:
        ra, mx = angle, 0
    elif angle <= 270:
        ra, mx = 180 - angle, 1
    else:
        ra, mx = angle - 360, 0

    display.fill(0b10)

    dbBmp, dbMirX, dbMirY = debugArrow[arrow]
    display.blit(dbBmp, 0, 35, 5, 5, 0, dbMirX, dbMirY)

    perf.start()
    rotate_sprite(impShip, impRotated, ra, 32)
    blitIndexed(impRotated, 36-16, 20-16, 32, 32, mx, 0)
    perf.stop()

    display.update()

import math
from array import array

from thumbyGrayscale import display as GSdisplay

GSdisplay.setFPS(30)

BUF_W = const(72)
BUF_H = const(40)
BUF_SIZE = const(BUF_W * BUF_H)
BUF_SIZE_INT = const(BUF_SIZE >> 2)

# Image format (IMP) is a special 8-bit indexed buffer, VLSB pixel ordered (with padding)
# Index format:
#   ASDNNNCC
#   A: Alpha        0=Transparent 1=Opaque
#   S: Shading      0=Matte 1=Shiny
#   D: Directional  0=Flat 1=Sloped
#   N: Normal*      0=E 1=SE 2=S 3=SW 4=W 5=NW 6=N 7=NE
#       *Only applies if Directional is Sloped
#   C: Color        0=Black 1=White 2=DarkGray 3=LightGray

IMP_ALPHA = const(0b10000000)
IMP_SHADING = const(0b01000000)
IMP_DIR = const(0b00100000)
IMP_NORMAL = const(0b00011100)
IMP_COLOR = const(0b00000011)

IMP_ALPHA_INV = const(255-IMP_ALPHA)
IMP_SHADING_INV = const(255-IMP_SHADING)
IMP_DIR_INV = const(255-IMP_DIR)
IMP_NORMAL_INV = const(255-IMP_NORMAL)
IMP_COLOR_INV = const(255-IMP_COLOR)

IMP_D_E = const(0 << 2)
IMP_D_SE = const(1 << 2)
IMP_D_S = const(2 << 2)
IMP_D_SW = const(3 << 2)
IMP_D_W = const(4 << 2)
IMP_D_NW = const(5 << 2)
IMP_D_N = const(6 << 2)
IMP_D_NE = const(7 << 2)

IMP_C_BLACK = const(0b00)
IMP_C_WHITE = const(0b01)
IMP_C_DARK = const(0b10)
IMP_C_LIGHT = const(0b11)

tan_values_f10 = array('i', [int(math.tan(math.radians(x / 2))
                                 * 1024) for x in range(-90, 91)])
sin_values_f10 = array('i', [int(math.sin(math.radians(x))
                                 * 1024) for x in range(-90, 91)])
cos_values_f10 = array('i', [int(math.cos(math.radians(x))
                                 * 1024) for x in range(-90, 91)])


def convertBMP(width, height, bmp, mask=None):
    # 2-buffer VLSB grayscale ==> 8-bit indexed VLSB pixel order

    paddedHeight = 8 * ((height + 7) // 8)
    ret = bytearray(width * paddedHeight)
    i = 0
    for rowY in range(0, height, 8):
        for x in range(width):
            o = (rowY >> 3) * width + x
            m = 1
            for _ in range(8):
                ret[i] = (IMP_ALPHA if mask is None or mask[o] & m else 0) | (
                    0b10 if (bmp[1][o] & m) else 0) | (
                    0b01 if (bmp[0][o] & m) else 0)
                m <<= 1
                i += 1
    return ret


@micropython.viper
def blit(buffer: ptr8, imp: ptr8, x: int, y: int, w: int, h: int):
    x1, x2 = int(max(0, x)), int(min(BUF_W, x+w))
    y1, y2 = int(max(0, y)), int(min(BUF_H, y+h))

    w = x2 - x1
    h = y2 - y1

    dstX = x1
    for srcX in range(w):
        dstY = y1
        for srcY in range(h):
            v = imp[((srcY >> 3)*w+srcX)*8+(srcY & 0b111)]
            if v & IMP_ALPHA:
                buffer[((dstY >> 3)*72+dstX)*8+(dstY & 0b111)] = v
            dstY += 1
        dstX += 1


@micropython.viper
def blitRotate(buffer: ptr8, imp: ptr8, angle: int, x: int, y: int, w: int, h: int, pivotX: int, pivotY: int):
    if angle <= 90:
        ra, mx = angle, 0
    elif angle <= 270:
        ra, mx = 180 - angle, 1
        x -= 2 * ((w >> 1) - pivotX)
    else:
        ra, mx = angle - 360, 0

    # Determine rendering mode
    if 10 < ra < 80 or -80 < ra < -10:
        rmode = 0
        shx_f10 = int(-tan_values_f10[ra + 90])
        shy_f10 = int(sin_values_f10[ra + 90])
    elif ra == 0:
        rmode = 1
    elif ra == 90:
        rmode = 2
    elif ra == -90:
        rmode = 3
    else:
        rmode = 4
        cos_f10 = int(cos_values_f10[ra + 90])
        sin_f10 = int(sin_values_f10[ra + 90])

    for srcY in range(h):
        for srcX in range(w):
            v = imp[((srcY >> 3)*w+srcX)*8+(srcY & 0b111)]
            if not v & IMP_ALPHA:
                continue

            # TODO rotate directionals

            if rmode == 0:  # Shear-based rotation for larger angles
                dx = srcX - pivotX
                dy = srcY - pivotY

                h_shear_x = dx + ((dy * shx_f10) >> 10)
                ry = dy + ((h_shear_x * shy_f10) >> 10)
                rx = h_shear_x + ((ry * shx_f10) >> 10)

                rx += pivotX
                ry += pivotY

            elif rmode == 1:  # No rotation
                rx = srcX
                ry = srcY

            elif rmode == 2:  # Quick rotate 90
                rx = pivotX + srcY - pivotY
                ry = pivotY + srcX - pivotX

            elif rmode == 3:  # Quick rotate -90
                rx = pivotX + srcY - pivotY
                ry = pivotY - srcX + pivotX

            elif rmode == 4:  # Nearest-neighbor rotation for smaller angles
                dx = srcX - pivotX
                dy = srcY - pivotY

                rx = (cos_f10 * dx - sin_f10 * dy) >> 10
                ry = (cos_f10 * dy + sin_f10 * dx) >> 10

                rx += pivotX
                ry += pivotY

            if mx:
                dstX = x + (w - rx)
            else:
                dstX = x + rx
            dstY = y + ry

            if 0 <= dstX < 72 and 0 <= dstY < 40:
                buffer[((dstY >> 3)*72+dstX)*8+(dstY & 0b111)] = v


@micropython.viper
def fill(buffer: ptr32, color: int):
    c4 = (color << 24) | (color << 16) | (color << 8) | color
    for i in range(BUF_SIZE_INT):
        buffer[i] = c4


@micropython.viper
def display(buffer: ptr32):
    scrBW = ptr8(GSdisplay.buffer)
    scrGS = ptr8(GSdisplay.shading)

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
def update():
    GSdisplay.update()

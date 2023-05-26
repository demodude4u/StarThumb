import math
from utime import ticks_us, ticks_diff
from array import array

from thumbyGrayscale import display as GSdisplay

GSdisplay.setFPS(30)

BUF_W = const(72)
BUF_H = const(40)
BUF_SIZE = const(BUF_W * BUF_H)
BUF_SIZE_INT = const(BUF_SIZE >> 2)

# Image format (IMP) is a special 8-bit indexed buffer, VLSB pixel ordered (with padding)
# Index format:
#   ADNNNSCC
#   A: Alpha        0=Transparent 1=Opaque
#   D: Directional  0=Flat 1=Sloped
#   N: Normal*      0=E 1=SE 2=S 3=SW 4=W 5=NW 6=N 7=NE
#       *Only applies if Directional is Sloped
#   S: Surface      0=Matte 1=Shiny
#   C: Color        0=Black 1=White 2=DarkGray 3=LightGray

IMP_ALPHA = const(0b10000000)
IMP_DIR = const(0b01000000)
IMP_NORMAL = const(0b00111000)
IMP_SURFACE = const(0b00000100)
IMP_COLOR = const(0b00000011)

IMP_ALPHA_INV = const(255-IMP_ALPHA)
IMP_DIR_INV = const(255-IMP_DIR)
IMP_NORMAL_INV = const(255-IMP_NORMAL)
IMP_SURFACE_INV = const(255-IMP_SURFACE)
IMP_COLOR_INV = const(255-IMP_COLOR)

IMP_D_E = const(0 << 3)
IMP_D_SE = const(1 << 3)
IMP_D_S = const(2 << 3)
IMP_D_SW = const(3 << 3)
IMP_D_W = const(4 << 3)
IMP_D_NW = const(5 << 3)
IMP_D_N = const(6 << 3)
IMP_D_NE = const(7 << 3)

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

dir_x_flip = bytearray([4, 3, 2, 1, 0, 7, 6, 5])


class Font:
    def __init__(self, charW, charH, imp):
        self.charW = charW
        self.charH = charH
        self.span = imp[1]
        self.imp = imp[0]


# def loadFontPPM(w, h, color_filename, shading_filename=None):
#     imp, iw, _ = loadImpPPM(color_filename, shading_filename)
#     return Font(w, h, iw, imp)


@micropython.viper
def blitText(buffer: ptr8, font, text, x: int, y: int, vertical=False):
    cw = int(font.charW)
    ch = int(font.charH)
    span = int(font.span)
    imp = ptr8(font.imp)

    count = int(len(text))

    if vertical:
        dx, dy = 0, ch + 1
        w, h = cw, dy * count - 1
    else:
        dx, dy = cw + 1, 0
        w, h = dx * count - 1, ch

    if x > 71 or x+w < 0 or y > 39 or y+h < 0:
        return

    # TODO this is slow
    cx, cy = x, y
    for ti in range(count):
        fi = int(ord(text[ti])) - 65
        fx = (fi * cw) % span
        fy = ch * ((fi * cw) // span)
        for py in range(cw):
            for px in range(ch):
                srcX = fx + px
                srcY = fy + py
                v = imp[((srcY >> 3)*span+srcX)*8+(srcY & 0b111)]
                if not (v & IMP_ALPHA):
                    continue
                dstX = cx + px
                dstY = cy + py
                if 0 <= dstX < 72 and 0 <= dstY < 40:
                    buffer[((dstY >> 3)*72+dstX)*8+(dstY & 0b111)] = v
        cx += dx
        cy += dy


# def _readPPMHeader(file):
#     if file.readline().rstrip() != b'P6':
#         raise ValueError("Invalid PPM format")
#     ret = []
#     while True:
#         line = file.readline().lstrip()
#         if not line.startswith(b'#'):
#             for s in line.rstrip().split():
#                 ret.append(int(s))
#             if len(ret) >= 3:
#                 return ret[0], ret[1], ret[2]


# def loadImpPPM(color_filename, shading_filename=None):
#     # ppm binary file format

#     print("Loading", color_filename)
#     if shading_filename:
#         print("Loading", shading_filename)

#     color_map = {0: 0, 255: 1, 162: 3, 78: 2}
#     shading_map = {
#         0x4040da: (0, 1, 5),
#         0x8025da: (0, 1, 6),
#         0xc040da: (0, 1, 7),
#         0x2580da: (0, 1, 4),
#         0x8080ff: (0, 0, 0),
#         0xda80da: (0, 1, 0),
#         0x40c0da: (0, 1, 3),
#         0x80dada: (0, 1, 2),
#         0xc0c0da: (0, 1, 1),
#         0x1e1e74: (1, 1, 5),
#         0x420f74: (1, 1, 6),
#         0x661e74: (1, 1, 7),
#         0x0f4274: (1, 1, 4),
#         0x424289: (0, 0, 0),
#         0x744274: (1, 1, 0),
#         0x1e6674: (1, 1, 3),
#         0x427474: (1, 1, 2),
#         0x666674: (1, 1, 1),
#         0xffffff: (1, 0, 0),
#         0xa2a2a2: (1, 0, 0),
#         0x4e4e4e: (1, 0, 0),
#         0x000000: (1, 0, 0)
#     }

#     with open(color_filename, 'rb') as color_file:
#         width, height = _readPPMHeader(color_file)[:2]

#         shading_file = None
#         if shading_filename is not None:
#             shading_file = open(shading_filename, 'rb')
#             _ = _readPPMHeader(shading_file)

#         paddedHeight = 8 * ((height + 7) // 8)
#         buffer = bytearray(width * paddedHeight)
#         for y in range(height):
#             for x in range(width):
#                 cr, cg, cb = color_file.read(3)

#                 sr, sg, sb = (shading_file.read(
#                     3) if shading_file else (cr, cg, cb))

#                 is_transparent = (cr, cg, cb) not in (
#                     (0, 0, 0), (78, 78, 78), (162, 162, 162), (255, 255, 255))
#                 if is_transparent:
#                     continue

#                 color = color_map.get(cg, 0)
#                 shiny, directional, normal = shading_map.get(
#                     (sr << 16) | (sg << 8) | sb, (0, 0, 0))

#                 i = ((y >> 3)*width+x)*8+(y & 0b111)
#                 buffer[i] = color | (shiny << 2) | (
#                     normal << 3) | (directional << 6) | 0b10000000

#         if shading_file:
#             shading_file.close()

#         return (buffer, width, height)


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
    dx1, dx2 = int(max(0, x)), int(min(BUF_W, x+w))
    dy1, dy2 = int(max(0, y)), int(min(BUF_H, y+h))

    sx1 = dx1 - x
    sx2 = sx1 + dx2 - dx1
    sy1 = dy1 - y
    sy2 = sy1 + dy2 - dy1

    dstX = dx1
    for srcX in range(sx1, sx2):
        dstY = dy1
        for srcY in range(sy1, sy2):
            v = imp[((srcY >> 3)*w+srcX)*8+(srcY & 0b111)]
            if v & IMP_ALPHA:
                buffer[((dstY >> 3)*72+dstX)*8+(dstY & 0b111)] = v
            dstY += 1
        dstX += 1


@micropython.viper
def blitRotate(buffer: ptr8, imp: ptr8, angle: int, x: int, y: int, w: int, h: int, pivotX: int, pivotY: int):
    dirFlip = ptr8(dir_x_flip)

    dirDelta = ((angle + 22) // 45) & 0b111

    if angle < 90:
        ra, mx = angle, 0
    elif angle <= 270:
        ra, mx = 180 - angle, 1
        x -= 2 * ((w >> 1) - pivotX)
        dirDelta = dirFlip[dirDelta]
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

            if v & IMP_DIR:
                d1 = ((v & IMP_NORMAL) >> 3)
                d2 = (d1 + dirDelta) & 0b111
                if mx:
                    d3 = dirFlip[d2]
                else:
                    d3 = d2
                v = (v & IMP_NORMAL_INV) | (d3 << 3)

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
                rx = pivotX - srcY + pivotY
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
def blitScale(buffer: ptr8, imp: ptr8, scale_f6: int, x: int, y: int, w: int, h: int, pivotX: int, pivotY: int, dir: int = 0):
    for srcY in range(h):
        for srcX in range(w):
            v = imp[((srcY >> 3)*w+srcX)*8+(srcY & 0b111)]
            if not v & IMP_ALPHA:
                continue

            dx = srcX - pivotX
            dy = srcY - pivotY

            rx = (scale_f6 * dx) >> 6
            ry = (scale_f6 * dy) >> 6

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
def blitContainerMap(buffer: ptr8, container, x: int, y: int):
    columns = int(container.columns)
    rows = int(container.rows)
    map = ptr8(container.map)
    impTiles = ptr8(container.impTiles[0])

    x += int(container.x)
    y += int(container.y)

    w, h = (columns*8), (rows*8)

    dx1, dx2 = int(max(0, x)), int(min(72, x+w))
    dy1, dy2 = int(max(0, y)), int(min(40, y+h))

    sx1 = dx1 - x
    sx2 = sx1 + dx2 - dx1
    sy1 = dy1 - y
    sy2 = sy1 + dy2 - dy1

    sc1 = sx1 >> 3
    dxt1 = dx1 - (sx1 & 0b111)
    sc2 = (sx2 + 7) >> 3
    sr1 = sy1 >> 3
    dyt1 = dy1 - (sy1 & 0b111)
    sr2 = (sy2 + 7) >> 3

    dxt = dxt1
    for c in range(sc1, sc2):
        dyt = dyt1
        for r in range(sr1, sr2):
            ti = map[r * columns + c]
            if ti == -1:
                dyt += 8
                continue
            to = 64 * ti

            if dxt < 0:
                tx1 = 0 - dxt
                tx2 = 8
            elif dxt > 64:
                tx1 = 0
                tx2 = 8 - (dxt-64)
            else:
                tx1 = 0
                tx2 = 8

            if dyt < 0:
                ty1 = 0 - dyt
                ty2 = 8
            elif dyt > 32:
                ty1 = 0
                ty2 = 8 - (dyt-32)
            else:
                ty1 = 0
                ty2 = 8

            for tx in range(tx1, tx2):
                dstX = dxt + tx
                txo = to + tx * 8
                for ty in range(ty1, ty2):
                    dstY = dyt + ty
                    v = impTiles[txo + ty]
                    if v & 0b10000000:
                        buffer[((dstY >> 3)*72+dstX)*8+(dstY & 0b111)] = v
            dyt += 8
        dxt += 8

# def _readPPMHeader(file):
#     if file.readline().rstrip() != b'P6':
#         raise ValueError("Invalid PPM format")
#     ret = []
#     while True:
#         line = file.readline().lstrip()
#         if not line.startswith(b'#'):
#             for s in line.rstrip().split():
#                 ret.append(int(s))
#             if len(ret) >= 3:
#                 return ret[0], ret[1], ret[2]


# def loadShaderPPM(shader_filename):
#     # ppm binary file format

#     color_map = {0: 0, 255: 1, 162: 3, 78: 2}
#     row_map = [3, 0, 2, 1, 7, 4, 6, 5]
#     column_map = [0, 1, 2, 3, 4, 3, 2, 1]

#     with open(shader_filename, 'rb') as shader_file:
#         width, height = _readPPMHeader(shader_file)[:2]

#         if width != 5 or height != 8:
#             raise ValueError("Invalid shader image dimensions")

#         colorData = bytearray(5*8)
#         for i in range(5*8):
#             cr, cg, cb = shader_file.read(3)
#             colorData[i] = color_map.get(cg, 0)

#         shader_array = array('H', [0] * 8)  # 8 16-bit values
#         for sy in range(8):
#             shader_value = 0
#             cy = row_map[sy]
#             for sx in range(8):
#                 cx = column_map[sx]
#                 color = colorData[cy*5+cx]
#                 shader_value |= color << (2 * sx)
#             shader_array[sy] = shader_value

#     return shader_array


@micropython.viper
def postShading(buffer: ptr8, shader: ptr16, light: int):
    width = 72
    height = 40

    pixel_count = width * height

    df = True
    for i in range(pixel_count):
        pixel = buffer[i]

        if not (pixel & 0b10000000):  # Transparent
            continue

        if not (pixel & 0b01000000):  # Flat
            continue

        shading_rule = shader[pixel & 0b111]
        normal = (pixel >> 3) & 0b111

        shading_color = (shading_rule >> (
            2 * ((light - normal + 8) & 0b111))) & 0x03

        if df and (pixel & 0b111 == 0b011) and (normal == 0):
            df = False

        buffer[i] = (pixel & 0b11111100) | shading_color


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
def update():
    GSdisplay.update()


def setFPS(fps):
    GSdisplay.setFPS(fps)


# BITMAP: width: 30, height: 5
perfBmpDigits = bytearray([31, 17, 31, 0, 31, 0, 29, 21, 23, 21, 21, 31,
                          7, 4, 31, 23, 21, 29, 31, 21, 29, 1, 1, 31, 31, 21, 31, 23, 21, 31])

_perfStart = 0
_perfTimes = array("L", [0, 0, 0, 0, 0])
_perfCount = 0


@micropython.native
def perfStart():
    global _perfStart
    _perfStart = ticks_us()


@micropython.native
def perfStop():
    end = ticks_us()
    global _perfStart, _perfTimes, _perfCount
    if _perfCount < 5:
        _perfTimes[_perfCount] = ticks_diff(end, _perfStart)
        _perfCount += 1


@micropython.viper
def perfRender():
    global _perfTimes, _perfCount
    bufBW = ptr8(GSdisplay.buffer)
    bufGS = ptr8(GSdisplay.shading)
    bd = ptr8(perfBmpDigits)
    so = 0
    for i in range(int(_perfCount)):
        num = int(_perfTimes[i])
        ndc = num
        num_digits = 1
        while ndc >= 10:
            ndc //= 10
            num_digits += 1
        o = so + (num_digits * 4) - 1
        while True:
            bufBW[o] &= 0b11000000
            bufGS[o] &= 0b11000000
            o -= 1
            digit = num % 10
            d = digit * 3 + 2
            for _ in range(3):
                bufBW[o] = (bufBW[o] & 0b11000000) | bd[d]
                bufGS[o] &= 0b11000000
                o -= 1
                d -= 1
            num //= 10
            if num == 0:
                break
        so += 72
    _perfCount = 0

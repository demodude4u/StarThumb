from utime import ticks_us, ticks_diff
from array import array

from thumbyGrayscale import display

# BITMAP: width: 30, height: 5
bmpDigits = bytearray([31, 17, 31, 0, 31, 0, 29, 21, 23, 21, 21, 31,
                      7, 4, 31, 23, 21, 29, 31, 21, 29, 1, 1, 31, 31, 21, 31, 23, 21, 31])

_start = 0
_times = array("L", [0, 0, 0, 0, 0])
_count = 0


@micropython.native
def start():
    global _start
    _start = ticks_us()


@micropython.native
def stop():
    end = ticks_us()
    global _start, _times, _count
    if _count < 5:
        _times[_count] = ticks_diff(end, _start)
        _count += 1


# @micropython.viper
# def render():
#     global _times, _count
#     bufBW = ptr8(display.buffer)
#     bufGS = ptr8(display.shading)
#     bd = ptr8(bmpDigits)
#     so = 0
#     for i in range(int(_count)):
#         text = str(_times[i])
#         o = so
#         for c in text:
#             d = (int(ord(c)) - 48) * 3
#             for _ in range(3):
#                 bufBW[o] = (bufBW[o] & 0b11000000) | bd[d]
#                 bufGS[o] &= 0b11000000
#                 o += 1
#                 d += 1
#             bufBW[o] &= 0b11000000
#             bufGS[o] &= 0b11000000
#             o += 1
#         so += 72
#     _count = 0

@micropython.viper
def render():
    global _times, _count
    bufBW = ptr8(display.buffer)
    bufGS = ptr8(display.shading)
    bd = ptr8(bmpDigits)
    so = 0
    for i in range(int(_count)):
        num = int(_times[i])
        num_digits = 1
        while num >= 10:
            num //= 10
            num_digits += 1
        o = so + (num_digits * 9) - 1
        while True:
            digit = num % 10
            d = digit * 3
            for _ in range(3):
                bufBW[o] = (bufBW[o] & 0b11000000) | bd[d]
                bufGS[o] &= 0b11000000
                o -= 1
                d += 1
            bufBW[o] &= 0b11000000
            bufGS[o] &= 0b11000000
            o -= 1
            if num == 0:
                break
            num //= 10
        so += num_digits * 9
    _count = 0

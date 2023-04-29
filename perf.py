from utime import ticks_us, ticks_diff

from thumbyGrayscale import display

# BITMAP: width: 30, height: 5
bmpDigits = bytearray([31, 17, 31, 0, 31, 0, 29, 21, 23, 21, 21, 31,
                      7, 4, 31, 23, 21, 29, 31, 21, 29, 1, 1, 31, 31, 21, 31, 23, 21, 31])

_startTime = 0
_endTime = 0


@micropython.native
def start():
    global _startTime
    _startTime = ticks_us()


@micropython.native
def stop(render=True):
    global _endTime
    _endTime = ticks_us()
    if render:
        render()


@micropython.viper
def render():
    global _startTime, _endTime
    bufBW = ptr8(display.buffer)
    bufGS = ptr8(display.shading)
    bd = ptr8(bmpDigits)
    text = str(ticks_diff(_endTime, _startTime))
    o = 0
    for c in text:
        d = (int(ord(c)) - 48) * 3
        for _ in range(3):
            bufBW[o] = (bufBW[o] & 0b11000000) | bd[d]
            bufGS[o] &= 0b11000000
            o += 1
            d += 1
        bufBW[o] &= 0b11000000
        bufGS[o] &= 0b11000000
        o += 1

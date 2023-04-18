import array
from utime import ticks_us, ticks_diff

from thumbyGraphics import display
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR


display.setFPS(30)


@micropython.viper
def blitViper(bmp: ptr8, x: int, y: int, w: int, h: int):
    scr = ptr8(display.display.buffer)

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
            if bmp[bo] & bm:
                scr[so] |= sm1
            else:
                scr[so] &= sm0
            bx += 1
        by += 1


@micropython.viper
def blitHybrid(bmp: ptr8, x: int, y: int, w: int, h: int):
    scr = ptr8(display.display.buffer)

    sx1, sx2 = int(max(0, x)), int(min(72, x+w))
    sy1, sy2 = int(max(0, y)), int(min(40, y+h))

    by = sy1 - y
    for sy in range(sy1, sy2):
        bx = sx1 - x
        for sx in range(sx1, sx2):
            v = blitHybrid_readPixel(bmp, bx, by, w)
            blitHybrid_writeScreenPixel(scr, sx, sy, v)
            bx += 1
        by += 1


@micropython.asm_thumb
def blitHybrid_readPixel(r0, r1, r2, r3) -> uint:
    # Arguments:
    #   r0 : ptr8   buffer
    #   r1 : int    x
    #   r2 : int    y
    #   r3 : int    span
    # Returns:
    #   r0 : int    value

    # Bitmap index (y >> 3) * span + x
    add(r0, r0, r1)     # r0 += r1
    push({r2})
    mov(r1, 3)          # r1 = 3
    asr(r2, r1)         # r2 >>= r1
    mul(r2, r3)         # r2 = r2 * r3
    add(r0, r0, r2)     # r0 += r2
    pop({r2})

    # Bitmap bit mask 1 << (y & 7)
    mov(r1, 0b111)      # r1 = 0b111
    and_(r2, r1)        # r2 &= r1
    mov(r1, 1)          # r1 = 1
    lsl(r1, r2)         # r1 <<= r2

    # Read Masked Value
    ldrb(r0, [r0, 0])   # r0 = *r0
    and_(r0, r1)        # r0 &= r1


@micropython.asm_thumb
def blitHybrid_writeScreenPixel(r0, r1, r2, r3):
    # Arguments:
    #   r0 : ptr8   buffer
    #   r1 : int    x
    #   r2 : int    y
    #   r3 : int    value

    # Screen index (y >> 3) * 72 + x
    add(r0, r0, r1)     # r0 += r1
    push({r2})
    mov(r1, 3)          # r1 = 3
    asr(r2, r1)         # r2 >>= r1
    mov(r1, 72)         # r1 = 72
    mul(r2, r1)         # r2 = r2 * r1
    add(r0, r0, r2)     # r0 += r2
    pop({r2})

    # Screen bit mask 1 << (y & 7)
    mov(r1, 0b111)      # r1 = 0b111
    and_(r2, r1)        # r2 &= r1
    mov(r1, 1)          # r1 = 1
    lsl(r1, r2)         # r1 <<= r2

    # Set/Clear Screen bit
    cmp(r3, 0)
    beq(CLEAR_BIT)      # r3 == 0
    ldrb(r3, [r0, 0])   # r3 = *r0
    orr(r3, r1)         # r3 |= r1
    b(STORE_SCR)
    label(CLEAR_BIT)
    ldrb(r3, [r0, 0])   # r3 = *r0
    bic(r3, r1)         # r2 &= ~r1

    # Store Updated Screen Value
    label(STORE_SCR)
    strb(r3, [r0, 0])   # *r0 = r2


# BITMAP: width: 30, height: 5
bmpDigits = bytearray([31, 17, 31, 0, 31, 0, 29, 21, 23, 21, 21, 31,
                      7, 4, 31, 23, 21, 29, 31, 21, 29, 1, 1, 31, 31, 21, 31, 23, 21, 31])

_startTime = 0


@micropython.viper
def perf_start():
    global _startTime
    _startTime = ticks_us()


@micropython.viper
def perf_stop():
    endTime = ticks_us()
    global _startTime
    buf = ptr8(display.display.buffer)
    bd = ptr8(bmpDigits)
    text = str(ticks_diff(endTime, _startTime))
    o = 0
    for c in text:
        d = (int(ord(c)) - 48) * 3
        for _ in range(3):
            buf[o] = (buf[o] & 0b11000000) | bd[d]
            o += 1
            d += 1
        buf[o] &= 0b11000000
        o += 1


# BITMAP: width: 49, height: 23
bmpShip = bytearray([0, 0, 128, 128, 160, 224, 208, 192, 144, 56, 56, 60, 60, 60, 90, 90, 90, 86, 78, 30, 190, 62, 28, 216, 216, 192, 128, 128, 128, 128, 128, 128, 0, 136, 216, 216, 208, 64, 72, 80, 128, 128, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 128, 128, 128, 156, 182, 182, 156, 73, 107, 42, 42, 42, 107, 42, 8, 73, 107, 107, 235, 107, 28, 156, 213, 255, 255, 255, 182, 182, 247, 182, 85, 190, 128, 170, 190, 127, 127, 127, 190, 190, 62, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 2, 3, 5, 1, 4, 14, 14, 30, 30, 30, 45, 45, 45, 53, 57, 60, 62, 62, 28, 13, 13, 1, 0, 0, 0, 0, 0, 0, 0, 8, 13, 13, 5, 1, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0])

rmode = 0
while True:
    if buttonA.justPressed():
        rmode = (rmode + 1) % 2

    display.fill(0b1 if rmode else 0b0)
    if rmode == 0:
        perf_start()
        blitViper(bmpShip, 36-49//2, 20-23//2, 49, 23)
        perf_stop()

    else:
        perf_start()
        # Why is this function 10x slower than the other one?
        blitHybrid(bmpShip, 36-49//2, 20-23//2, 49, 23)
        perf_stop()

    display.update()

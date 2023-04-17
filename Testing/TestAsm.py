import array

from thumbyGrayscale import display
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

import perf

display.setFPS(30)


@micropython.viper
def blitViper(bmp, x: int, y: int, w: int, h: int):
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


bhasmBitmapParams = array.array("b", (0, 0, 0))
bhasmScreenParams = array.array("b", (0, 0))


@micropython.viper
def blitHybrid(bmp, x: int, y: int, w: int, h: int):
    scrBW = ptr8(display.buffer)
    scrGS = ptr8(display.shading)

    bmpBW = ptr8(bmp[0])
    bmpGS = ptr8(bmp[1])

    global bhasmBitmapParams, bhasmScreenParams
    bp = ptr8(bhasmBitmapParams)
    sp = ptr8(bhasmScreenParams)

    bp[2] = w

    sx1, sx2 = int(max(0, x)), int(min(72, x+w))
    sy1, sy2 = int(max(0, y)), int(min(40, y+h))

    by = sy1 - y
    for sy in range(sy1, sy2):
        bx = sx1 - x
        for sx in range(sx1, sx2):
            bp[0] = bx
            bp[1] = by
            sp[0] = sx
            sp[1] = sy
            blitHybrid_copyHalfPixel(bmpBW, scrBW, bp, sp)
            blitHybrid_copyHalfPixel(bmpGS, scrGS, bp, sp)
            bx += 1
        by += 1


# Arguments:
#   r0 : ptr8   Bitmap Buffer
#   r1 : ptr8   Screen Buffer
#   r2 : ptr8   Bitmap Params [bx,by,w]
#   r3 : ptr8   Screen Params [sx,sy]
@micropython.asm_thumb
def blitHybrid_copyHalfPixel(r0, r1, r2, r3):
    push({r4, r5, r6, r7})

    # (r4) Bitmap index (by >> 3) * w + bx
    ldrb(r4, [r2, 1])   # r4 = by
    mov(r5, r4)         # r5 = r4
    mov(r6, 3)          # r6 = 3
    asr(r4, r6)         # r4 >>= r6
    ldrb(r6, [r2, 2])   # r6 = w
    mul(r4, r6)         # r4 = r4 * r6
    ldrb(r6, [r2, 0])   # r6 = bx
    add(r4, r4, r6)     # r4 += r6

    # (r2) Bitmap bit mask 1 << (by & 7)
    mov(r7, 0b111)      # r7 = 0b111
    and_(r5, r7)        # r5 &= r7
    mov(r2, 1)          # r2 = 1
    lsl(r2, r5)         # r2 <<= r5

    # (r5) Screen index (sy >> 3) * 72 + sx
    ldrb(r5, [r3, 1])   # r5 = sy
    mov(r7, r5)         # r7 = r5
    mov(r6, 3)          # r6 = 3
    asr(r7, r6)         # r7 >>= r6
    mov(r6, 72)         # r6 = 72
    mul(r5, r6)         # r5 = r5 * r6
    ldrb(r6, [r3, 0])   # r6 = sx
    add(r5, r5, r6)     # r5 += r6

    # (r3) Screen bit mask 1 << (sy & 7)
    mov(r6, 0b111)      # r6 = 0b111
    and_(r7, r6)        # r7 &= r6
    mov(r3, 1)          # r3 = 1
    lsl(r3, r7)         # r3 <<= r7

    # (r0) Bitmap bit bmp[bo] & bm
    add(r0, r0, r4)     # r0 += r4
    ldrb(r0, [r0, 0])   # r0 = *r0
    and_(r0, r2)        # r0 &= r2

    # (r2) Screen value scr[so]
    add(r1, r1, r5)     # r1 += r5
    ldrb(r2, [r1, 0])   # r2 = *r1

    # (r2) Set/Clear Screen bit
    cmp(r0, 0)
    beq(CLEAR_BIT)      # r0 == 0
    orr(r2, r3)         # r2 |= r3
    b(STORE_SCR)
    label(CLEAR_BIT)
    bic(r2, r3)         # r2 &= ~r3

    # Store Updated Screen Value
    label(STORE_SCR)
    strb(r2, [r1, 0])   # *r1 = r2

    pop({r7, r6, r5, r4})


# BITMAP: width: 49, height: 23
bmpShip = [bytearray([0, 0, 128, 128, 160, 224, 208, 192, 144, 56, 56, 60, 60, 60, 90, 90, 90, 86, 78, 30, 190, 62, 28, 216, 216, 192, 128, 128, 128, 128, 128, 128, 0, 136, 216, 216, 208, 64, 72, 80, 128, 128, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 128, 128, 128, 156, 182, 182, 156, 73, 107, 42, 42, 42, 107, 42, 8, 73, 107, 107, 235, 107, 28, 156, 213, 255, 255, 255, 182, 182, 247, 182, 85, 190, 128, 170, 190, 127, 127, 127, 190, 190, 62, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 2, 3, 5, 1, 4, 14, 14, 30, 30, 30, 45, 45, 45, 53, 57, 60, 62, 62, 28, 13, 13, 1, 0, 0, 0, 0, 0, 0, 0, 8, 13, 13, 5, 1, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
           bytearray([199, 23, 195, 227, 243, 251, 235, 123, 123, 89, 93, 92, 92, 76, 40, 40, 40, 34, 40, 152, 184, 184, 144, 209, 211, 195, 223, 191, 63, 15, 175, 167, 179, 187, 211, 219, 219, 219, 219, 211, 135, 159, 31, 159, 63, 191, 63, 127, 255,
                      255, 62, 190, 128, 190, 190, 190, 62, 62, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 255, 255, 255, 255, 227, 255, 235, 213, 182, 127, 107, 235, 235, 235, 247, 255, 255, 235, 255, 255, 255, 247, 247, 85, 128, 127, 162, 99, 62, 128,
                      113, 116, 97, 99, 103, 111, 107, 111, 111, 77, 93, 29, 29, 25, 10, 10, 10, 34, 10, 12, 14, 14, 4, 69, 101, 97, 125, 124, 126, 120, 122, 114, 102, 110, 101, 109, 109, 109, 109, 101, 112, 124, 124, 124, 126, 126, 126, 127, 127])]

rmode = 0
while True:
    if buttonA.justPressed():
        rmode = (rmode + 1) % 2

    display.fill(0b11 if rmode else 0b10)
    if rmode == 0:
        perf.start()
        blitViper(bmpShip, 36-49//2, 20-23//2, 49, 23)
        perf.stop()

    else:
        perf.start()
        blitHybrid(bmpShip, 36-49//2, 20-23//2, 49, 23)
        perf.stop()

    display.update()

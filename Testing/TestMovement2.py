from thumbyGrayscale import display, Sprite
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

try:
    import perf
except ImportError:
    class perf:
        def start():
            pass

        def stop():
            pass

display.setFPS(30)

# BITMAP: width: 11, height: 64
bmpShip = [bytearray([32, 249, 39, 174, 116, 32, 80, 80, 112, 32, 32,
           0, 4, 7, 3, 1, 0, 0, 0, 0, 0, 0,
           6, 12, 28, 10, 210, 63, 210, 10, 28, 12, 6,
           0, 0, 0, 0, 1, 7, 1, 0, 0, 0, 0,
           32, 32, 112, 80, 80, 32, 116, 174, 39, 249, 32,
           0, 0, 0, 0, 0, 0, 1, 3, 7, 4, 0,
           0, 128, 192, 128, 92, 231, 92, 128, 192, 128, 0,
           3, 1, 1, 2, 2, 7, 2, 2, 1, 1, 3]),
           bytearray([169, 170, 254, 254, 252, 216, 216, 80, 80, 32, 32,
                      4, 2, 3, 3, 1, 0, 0, 0, 0, 0, 0,
                      1, 14, 28, 127, 252, 31, 252, 127, 28, 14, 1,
                      0, 0, 0, 0, 1, 6, 1, 0, 0, 0, 0,
                      32, 32, 80, 80, 216, 216, 252, 254, 254, 170, 169,
                      0, 0, 0, 0, 0, 0, 1, 3, 3, 2, 4,
                      0, 128, 192, 240, 252, 195, 252, 240, 192, 128, 0,
                      4, 3, 1, 7, 1, 7, 1, 7, 1, 3, 4])]

sprShip = Sprite(11, 11, bmpShip, 0, 0, 0, 0, 0)

camX, camY = 0, 0

# fixed-point 3-bit (_f8)
px_f8, py_f8 = 0, 0

vx_f8, vy_f8 = 0, 0
speedMax_f8 = 4 << 3

accel_f8 = 6
dampening_f8 = 7  # out of 8

rotation = 0


@micropython.native
def shipMove(inputX_f8: int, inputY_f8: int):
    global px_f8, py_f8, vx_f8, vy_f8
    global speedMax_f8, accel_f8, dampening_f8

    if inputX_f8 > 0:
        vx_f8 += (accel_f8 * inputX_f8) >> 3
    elif inputX_f8 < 0:
        vx_f8 -= (accel_f8 * -inputX_f8) >> 3

    if inputY_f8 > 0:
        vy_f8 += (accel_f8 * inputY_f8) >> 3
    elif inputY_f8 < 0:
        vy_f8 -= (accel_f8 * -inputY_f8) >> 3

    if vx_f8 >= 0:
        vx_f8 = (vx_f8 * dampening_f8) >> 3
    else:
        vx_f8 = -((-vx_f8 * dampening_f8) >> 3)

    if vy_f8 >= 0:
        vy_f8 = (vy_f8 * dampening_f8) >> 3
    else:
        vy_f8 = -((-vy_f8 * dampening_f8) >> 3)

    if vx_f8 < -speedMax_f8:
        vx_f8 = -speedMax_f8
    elif vx_f8 > speedMax_f8:
        vx_f8 = speedMax_f8

    if vy_f8 < -speedMax_f8:
        vy_f8 = -speedMax_f8
    elif vy_f8 > speedMax_f8:
        vy_f8 = speedMax_f8

    px_f8 += vx_f8
    py_f8 += vy_f8


@micropython.viper
def drawGridPoints(camX: int, camY: int):
    bufBW = ptr8(display.buffer)
    bufGS = ptr8(display.shading)

    color = 0b10
    for y in range((0-camY) & 0xF, 40, 16):
        for x in range((0-camX) & 0xF, 72, 16):
            if x < 0 or x >= 72 or y < 0 or y >= 40:
                continue
            so = (y >> 3) * 72 + x
            sm1 = 1 << (y & 7)
            sm0 = 255-sm1
            if color & 0b01:
                bufBW[so] |= sm1
            else:
                bufBW[so] &= sm0
            if color & 0b10:
                bufGS[so] |= sm1
            else:
                bufGS[so] &= sm0


while True:

    inputX_f8, inputY_f8 = 0, 0
    if buttonR.pressed():
        rotation = 0
        inputX_f8 = 8
    if buttonD.pressed():
        rotation = 1
        inputY_f8 = 8
    if buttonL.pressed():
        rotation = 2
        inputX_f8 = -8
    if buttonU.pressed():
        rotation = 3
        inputY_f8 = -8

    # roughly simulate sqrt(2)/2 for diagonal inputs
    if inputX_f8 and inputY_f8:
        if inputX_f8 > 0:
            inputX_f8 = 5
        else:
            inputX_f8 = -5
        if inputY_f8 > 0:
            inputY_f8 = 5
        else:
            inputY_f8 = -5

    display.fill(0b00)

    drawGridPoints(camX, camY)

    perf.start()
    shipMove(inputX_f8, inputY_f8)
    perf.stop()

    camX, camY = (px_f8 >> 3) - 36, (py_f8 >> 3) - 20

    sprShip.x = 36 - 6 - (vx_f8 >> 3)
    sprShip.y = 20 - 6 - (vy_f8 >> 3)

    sprShip.setFrame(rotation)
    display.drawSprite(sprShip)

    display.update()

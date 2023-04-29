from thumbyGrayscale import display, Sprite
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

try:
    import perf
except ImportError:
    class perf:
        def start():
            pass

        def stop(render=True):
            pass

        def render():
            pass

display.setFPS(30)

# BITMAP: width: 11, height: 64
bmpShip1 = [bytearray([32, 249, 39, 174, 116, 32, 80, 80, 112, 32, 32,
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
# BITMAP: width: 5, height: 32
bmpShipTiny1 = [bytearray([31, 10, 4, 4, 4,
                           1, 3, 29, 3, 1,
                           4, 4, 4, 10, 31,
                           16, 24, 23, 24, 16]),
                bytearray([21, 31, 10, 4, 4,
                           3, 6, 27, 6, 3,
                           4, 4, 10, 31, 21,
                           24, 12, 27, 12, 24])]

# BITMAP: width: 24, height: 96
bmpShip2 = [bytearray([0, 0, 0, 0, 128, 128, 0, 0, 128, 128, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 219, 153, 165, 129, 231, 195, 102, 165, 153, 126, 60, 24, 60, 60, 195, 219, 126, 24, 24, 0, 0, 0,
                       0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 48, 252, 196, 80, 12, 12, 80, 196, 252, 48, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 3, 6, 9, 219, 252, 252, 219, 9, 6, 3, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 3, 7, 4, 30, 30, 4, 7, 3, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128, 128, 0, 0, 128, 128, 0, 0, 0, 0,
                       0, 0, 0, 24, 24, 126, 219, 195, 60, 60, 24, 60, 126, 153, 165, 102, 195, 231, 129, 165, 153, 219, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 192, 224, 32, 120, 120, 32, 224, 192, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 192, 96, 144, 219, 63, 63, 219, 144, 96, 192, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 12, 63, 35, 10, 48, 48, 10, 35, 63, 12, 0, 0, 0, 0, 0, 0, 0]),
            bytearray([0, 0, 0, 0, 128, 128, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       195, 195, 90, 219, 255, 255, 60, 60, 60, 189, 189, 126, 60, 60, 36, 36, 255, 231, 255, 60, 60, 0, 0, 0,
                       0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 48, 59, 63, 240, 252, 252, 240, 63, 59, 48, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 6, 8, 255, 63, 63, 255, 8, 6, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 31, 29, 29, 31, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128, 128, 0, 0, 0, 0,
                       0, 0, 0, 60, 60, 255, 231, 255, 36, 36, 60, 60, 126, 189, 189, 60, 60, 60, 255, 255, 219, 90, 195, 195,
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 224, 224, 248, 184, 184, 248, 224, 224, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 0, 96, 16, 255, 252, 252, 255, 16, 96, 0, 0, 0, 0, 0, 0, 0, 0,
                       0, 0, 0, 0, 0, 0, 0, 12, 220, 252, 15, 63, 63, 15, 252, 220, 12, 0, 0, 0, 0, 0, 0, 0])]
# BITMAP: width: 12, height: 64
bmpShipTiny2 = [bytearray([0, 240, 0, 144, 144, 240, 96, 96, 144, 240, 96, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 58, 226, 226, 58, 0, 0, 0, 0,
                           0, 0, 0, 0, 3, 6, 6, 3, 0, 0, 0, 0,
                           0, 96, 240, 144, 96, 96, 240, 144, 144, 0, 240, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 204, 118, 118, 204, 0, 0, 0, 0,
                           0, 0, 0, 0, 5, 4, 4, 5, 0, 0, 0, 0]),
                bytearray([144, 240, 240, 96, 96, 240, 96, 0, 240, 240, 96, 0,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 39, 126, 126, 39, 0, 0, 0, 0,
                           0, 0, 0, 0, 3, 7, 7, 3, 0, 0, 0, 0,
                           0, 96, 240, 240, 0, 96, 240, 96, 96, 240, 240, 144,
                           0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0, 0, 0, 0, 76, 238, 238, 76, 0, 0, 0, 0,
                           0, 0, 0, 0, 14, 7, 7, 14, 0, 0, 0, 0])]


# BITMAP: width: 5, height: 5
bmpMarker = [bytearray([0, 4, 14, 4, 0]), bytearray([4, 4, 27, 4, 4])]

# fixed-point 3-bit (_f8)
# fixed-point 4-bit (_f16)


class Ship:
    def __init__(self, w, h, bmpShip, speedMax_f8, accel_f8, dampening_f64, boost_f8, boostDelay):
        self.sprShip = [Sprite(w[i], h[i], bmpShip[i], 0, 0, 0, 0, 0)
                        for i in range(2)]
        self.speedMax_f8 = speedMax_f8
        self.accel_f8 = accel_f8
        self.dampening_f64 = dampening_f64
        self.boost_f8 = boost_f8
        self.boostDelay = boostDelay

        self.px_f8, self.py_f8 = 0, 0
        self.vx_f8, self.vy_f8 = 0, 0
        self.rotation = 0
        self.boostFrames = 0

    @micropython.native
    def moveFrame(self, inputX_f8: int, inputY_f8: int):
        speedMax_f8 = self.speedMax_f8
        accel_f8 = self.accel_f8
        dampening_f64 = self.dampening_f64
        boost_f8 = self.boost_f8
        boostDelay = self.boostDelay

        vx_f8 = self.vx_f8
        vy_f8 = self.vy_f8
        boostFrames = self.boostFrames

        if inputX_f8 > 0:
            vx_f8 += (accel_f8 * inputX_f8) >> 3
        elif inputX_f8 < 0:
            vx_f8 -= (accel_f8 * -inputX_f8) >> 3
        elif vx_f8 >= 0:
            vx_f8 = (vx_f8 * dampening_f64) >> 6
        else:
            vx_f8 = -((-vx_f8 * dampening_f64) >> 6)

        if inputY_f8 > 0:
            vy_f8 += (accel_f8 * inputY_f8) >> 3
        elif inputY_f8 < 0:
            vy_f8 -= (accel_f8 * -inputY_f8) >> 3
        elif vy_f8 >= 0:
            vy_f8 = (vy_f8 * dampening_f64) >> 6
        else:
            vy_f8 = -((-vy_f8 * dampening_f64) >> 6)

        if not inputX_f8 and not inputY_f8:
            boostFrames = 0
        if inputX_f8 and inputY_f8:
            boostFrames = 0

        if vx_f8 < -speedMax_f8:
            boostFrames += 1
            vx_f8 = -speedMax_f8 if boostFrames < boostDelay else -boost_f8
        elif vx_f8 > speedMax_f8:
            boostFrames += 1
            vx_f8 = speedMax_f8 if boostFrames < boostDelay else boost_f8

        if vy_f8 < -speedMax_f8:
            boostFrames += 1
            vy_f8 = -speedMax_f8 if boostFrames < boostDelay else -boost_f8
        elif vy_f8 > speedMax_f8:
            boostFrames += 1
            vy_f8 = speedMax_f8 if boostFrames < boostDelay else boost_f8

        self.px_f8 += vx_f8
        self.py_f8 += vy_f8
        self.vx_f8 = vx_f8
        self.vy_f8 = vy_f8
        self.boostFrames = boostFrames

    @micropython.native
    def render(self, camX: int, camY: int, zoomLevel: int):
        sprShip = self.sprShip[zoomLevel]
        f8Scr = 3 + zoomLevel
        sprShip.x = (self.px_f8 >> f8Scr) - camX - (sprShip.width >> 1)
        sprShip.y = (self.py_f8 >> f8Scr) - camY - (sprShip.height >> 1)
        sprShip.setFrame(self.rotation)
        display.drawSprite(sprShip)


@micropython.viper
def drawGridPoints(camX: int, camY: int, zoomLevel: int):
    bufBW = ptr8(display.buffer)
    bufGS = ptr8(display.shading)

    color = 0b10
    mask = 0xF >> zoomLevel
    spacing = 16 >> zoomLevel
    y = (0-camY) & mask
    while y < 40:
        x = (0-camX) & mask
        while x < 72:
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
            x += spacing
        y += spacing


ship1 = Ship([11, 5], [11, 5], [bmpShip1, bmpShipTiny1], speedMax_f8=4 <<
             3, accel_f8=6, dampening_f64=56, boost_f8=6 << 3, boostDelay=30)
ship2 = Ship([24, 12], [24, 12], [bmpShip2, bmpShipTiny2], speedMax_f8=4 <<
             3, accel_f8=2, dampening_f64=62, boost_f8=6 << 3, boostDelay=60)

ships = [ship1, ship2]

camX, camY = 0, 0
refX, refY = 0, 0
inputHolding = False

shipIndex = 0
zoomLevel = 0

while True:

    inputX_f8, inputY_f8 = 0, 0

    if buttonB.pressed():
        if buttonR.justPressed():
            shipIndex = (shipIndex + 1) % 2
        if buttonD.justPressed():
            zoomLevel = (zoomLevel + 1) % 2
    else:
        buttonR.justPressed()
        if buttonR.pressed():
            ship.rotation = 0
            inputX_f8 = 8
        buttonD.justPressed()
        if buttonD.pressed():
            ship.rotation = 1
            inputY_f8 = 8
        buttonL.justPressed()
        if buttonL.pressed():
            ship.rotation = 2
            inputX_f8 = -8
        buttonU.justPressed()
        if buttonU.pressed():
            ship.rotation = 3
            inputY_f8 = -8

    ship = ships[shipIndex]

    f8Scr = 3 + zoomLevel

    if inputX_f8 or inputY_f8:
        if not inputHolding:
            inputHolding = True
            refX, refY = ship.px_f8 >> f8Scr, ship.py_f8 >> f8Scr
    else:
        if inputHolding:
            inputHolding = False
            refX, refY = ship.px_f8 >> f8Scr, ship.py_f8 >> f8Scr

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

    perf.start()
    ship.moveFrame(inputX_f8, inputY_f8)
    perf.stop(render=False)

    display.fill(0b00)

    camX = (ship.px_f8 >> f8Scr) - 36 + (ship.vx_f8 >> f8Scr)
    camY = (ship.py_f8 >> f8Scr) - 20 + (ship.vy_f8 >> f8Scr)

    if ship.boostDelay <= ship.boostFrames <= ship.boostDelay + 5:
        if ship.vx_f8:
            camX += 1 if ship.vx_f8 > 0 else -1
        if ship.vy_f8:
            camY += 1 if ship.vy_f8 > 0 else -1

    drawGridPoints(camX, camY, zoomLevel)

    display.blit(bmpMarker, refX-camX-2, refY-camY-2, 5, 5, 0, 0, 0)

    ship.render(camX, camY, zoomLevel)

    perf.render()

    display.update()

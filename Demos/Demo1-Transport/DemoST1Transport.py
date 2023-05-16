import math
import gc
import random

from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

from STGraphics import loadImpPPM, fill, blit, blitRotate, display, update
from STContainer import Container, loadMapCSV, blitContainerMap, loadObjectsCSV
from STShading import loadShaderPPM, postShading
from STFont import loadFontPPM, blitText

import perf

gc.collect()

buffer = bytearray(72*40)

shader = loadShaderPPM("/Games/DemoST1Transport/Shader.ppm")

impTiles = loadImpPPM("/Games/DemoST1Transport/TilesColor.ppm",
                      "/Games/DemoST1Transport/TilesShading.ppm")
map, mw, mh = loadMapCSV("/Games/DemoST1Transport/Map.csv")
station = Container(mw, mh, map, impTiles[0])
loadObjectsCSV(station, "/Games/DemoST1Transport/Objects.csv")

impShipSmall = loadImpPPM("/Games/DemoST1Transport/ShipSmColor.ppm",
                          "/Games/DemoST1Transport/ShipSmShading.ppm")
impShip = loadImpPPM("/Games/DemoST1Transport/ShipColor.ppm",
                     "/Games/DemoST1Transport/ShipShading.ppm")
impShipLarge = loadImpPPM("/Games/DemoST1Transport/ShipLgColor.ppm",
                          "/Games/DemoST1Transport/ShipLgShading.ppm")

impGateSmall = loadImpPPM("/Games/DemoST1Transport/GateSmColor.ppm",
                          "/Games/DemoST1Transport/GateSmShading.ppm")
impGateH = loadImpPPM("/Games/DemoST1Transport/GateHColor.ppm",
                      "/Games/DemoST1Transport/GateHShading.ppm")
impGateV = loadImpPPM("/Games/DemoST1Transport/GateVColor.ppm",
                      "/Games/DemoST1Transport/GateVShading.ppm")

font3x3 = loadFontPPM(3, 3, "/Games/DemoST1Transport/Font3x3.ppm")
font4x4 = loadFontPPM(4, 4, "/Games/DemoST1Transport/Font4x4.ppm")

gc.collect()

# Features Not Experimented:
# - Thruster particles/animation
# - Scanner Shading
# - Control Zones (slow, scan, rotate lock)
# - Triggers
# - Gate Sequence
# - Docking Camera
# - Container Entities
# - Smooth Turning Controls (non-combat mode)
# - Glimmer
# - Signage
# - Trails

# Experiments To Implement:
# - TestAnimate
# - TestParticles


class Ship:
    def __init__(self, impShip, speedMax_f3, accel_f3, dampening_f6, boost_f3, boostDelay, rotateSpeed):
        self.impShip = impShip
        self.speedMax_f3 = speedMax_f3
        self.accel_f3 = accel_f3
        self.dampening_f6 = dampening_f6
        self.boost_f3 = boost_f3
        self.boostDelay = boostDelay
        self.px_f3, self.py_f3 = 0, 0
        self.vx_f3, self.vy_f3 = 0, 0
        self.angleTarget = 0
        self.angle = 0
        self.boostFrames = 0
        self.rotateSpeed = rotateSpeed
        self.inputX_f3 = 0
        self.inputY_f3 = 0
        self.speedLimited = False
        self.speedLimit_f3 = 0
        self.angleLocked = False
        self.angleLock = 0

    def inputButtons(self):
        inputX_f3, inputY_f3 = 0, 0
        if buttonR.pressed():
            inputX_f3 = 8
        if buttonD.pressed():
            inputY_f3 = 8
        if buttonL.pressed():
            inputX_f3 = -8
        if buttonU.pressed():
            inputY_f3 = -8
        if inputX_f3 and inputY_f3:
            if inputX_f3 > 0:
                inputX_f3 = 5
            else:
                inputX_f3 = -5
            if inputY_f3 > 0:
                inputY_f3 = 5
            else:
                inputY_f3 = -5
        self.inputX_f3 = inputX_f3
        self.inputY_f3 = inputY_f3

    @micropython.native
    def moveFrame(self):
        speedMax_f3 = self.speedMax_f3
        accel_f3 = self.accel_f3
        dampening_f6 = self.dampening_f6
        boost_f3 = self.boost_f3
        boostDelay = self.boostDelay
        vx_f3 = self.vx_f3
        vy_f3 = self.vy_f3
        boostFrames = self.boostFrames
        angle = self.angle
        rotateSpeed = self.rotateSpeed
        inputX_f3 = self.inputX_f3
        inputY_f3 = self.inputY_f3
        speedLimited = self.speedLimited
        speedLimit_f3 = self.speedLimit_f3
        angleLocked = self.angleLocked
        angleLock = self.angleLock

        if inputX_f3 > 0:
            vx_f3 += (accel_f3 * inputX_f3) >> 3
        elif inputX_f3 < 0:
            vx_f3 -= (accel_f3 * -inputX_f3) >> 3
        elif vx_f3 >= 0:
            vx_f3 = (vx_f3 * dampening_f6) >> 6
        else:
            vx_f3 = -((-vx_f3 * dampening_f6) >> 6)

        if inputY_f3 > 0:
            vy_f3 += (accel_f3 * inputY_f3) >> 3
        elif inputY_f3 < 0:
            vy_f3 -= (accel_f3 * -inputY_f3) >> 3
        elif vy_f3 >= 0:
            vy_f3 = (vy_f3 * dampening_f6) >> 6
        else:
            vy_f3 = -((-vy_f3 * dampening_f6) >> 6)

        if not inputX_f3 and not inputY_f3:
            boostFrames = 0
        if inputX_f3 and inputY_f3:
            boostFrames = 0

        if speedLimited:
            if speedMax_f3 > speedLimit_f3:
                speedMax_f3 = speedLimit_f3
            if boost_f3 > speedLimit_f3:
                boost_f3 = speedLimit_f3

        if vx_f3 < -speedMax_f3:
            boostFrames += 1
            vx_f3 = -speedMax_f3 if boostFrames < boostDelay else -boost_f3
        elif vx_f3 > speedMax_f3:
            boostFrames += 1
            vx_f3 = speedMax_f3 if boostFrames < boostDelay else boost_f3

        if vy_f3 < -speedMax_f3:
            boostFrames += 1
            vy_f3 = -speedMax_f3 if boostFrames < boostDelay else -boost_f3
        elif vy_f3 > speedMax_f3:
            boostFrames += 1
            vy_f3 = speedMax_f3 if boostFrames < boostDelay else boost_f3

        # TODO get rid of floats
        if abs(ship.vx_f3) >= speedMax_f3 or abs(ship.vy_f3) >= speedMax_f3:
            self.angleTarget = int(
                180*(math.atan2(ship.vy_f3, ship.vx_f3)/3.14159))

        if angleLocked:
            self.angleTarget = angleLock

        angleDiff = self.angleTarget - angle
        angleDiff = (angleDiff + 180) % 360 - 180
        angleDiff = max(-rotateSpeed, min(rotateSpeed, angleDiff))
        angle = (angle + angleDiff + 360) % 360

        self.px_f3 += vx_f3
        self.py_f3 += vy_f3
        self.vx_f3 = vx_f3
        self.vy_f3 = vy_f3
        self.boostFrames = boostFrames
        self.angle = angle

    @micropython.native
    def render(self, camX: int, camY: int):
        global buffer

        impShip = self.impShip
        w = impShip[1]
        h = impShip[2]
        hw = w >> 1
        hh = h >> 1
        x = (self.px_f3 >> 3) - camX - hw
        y = (self.py_f3 >> 3) - camY - hh
        blitRotate(buffer, impShip[0], self.angle, x, y, w, h, hw, hh)


class SpaceBits:
    # 16x16 cells, 6 columns, 4 rows ()
    # Cell format: 4-bit x, 4-bit y
    layer1 = bytearray((random.randrange(0, 256) for _ in range(6*4)))
    layer2 = bytearray((random.randrange(0, 256) for _ in range(6*4)))
    speedColors = bytes([0b10, 0b11, 0b01])

    @micropython.viper
    def render(px: int, py: int, vx: int, vy: int):
        global buffer

        sb1 = ptr8(SpaceBits.layer1)
        sb2 = ptr8(SpaceBits.layer2)
        speedColors = ptr8(SpaceBits.speedColors)

        speed = 0
        if vx > 0:
            speed += vx
        else:
            speed -= vx
        if vy > 0:
            speed += vy
        else:
            speed -= vy

        cShift = (px >> 5) % 6
        cPixel = (px >> 1) & 0b1111
        rShift = (py >> 5) % 4
        rPixel = (py >> 1) & 0b1111
        color = speedColors[int(min(2, (speed+1) >> 1))]

        for sr in range(4):
            for sc in range(6):
                c = (sc + cShift) % 6
                r = (sr + rShift) % 4
                cell = sb1[r*6+c]
                cx = cell & 0b1111
                cy = (cell >> 4) & 0b1111
                x = sc * 16 + cx - cPixel
                y = sr * 16 + cy - rPixel
                if x < 0 or x >= 72 or y < 0 or y >= 40:
                    continue
                buffer[((y >> 3)*72+x)*8+(y & 0b111)] = color

        cShift = (px >> 6) % 6
        cPixel = (px >> 2) & 0b1111
        rShift = (py >> 6) % 4
        rPixel = (py >> 2) & 0b1111
        color = speedColors[int(min(2, (speed+3) >> 2))]

        for sr in range(4):
            for sc in range(6):
                c = (sc + cShift) % 6
                r = (sr + rShift) % 4
                cell = sb2[r*6+c]
                cx = cell & 0b1111
                cy = (cell >> 4) & 0b1111
                x = sc * 16 + cx - cPixel
                y = sr * 16 + cy - rPixel
                if x < 0 or x >= 72 or y < 0 or y >= 40:
                    continue
                buffer[((y >> 3)*72+x)*8+(y & 0b111)] = color


class Scanner:
    frame = 0
    randomPattern = 0
    randomOffset = 0

    def update():
        Scanner.frame += 1
        Scanner.randomPattern = random.getrandbits(32)

    @micropython.viper
    def render(x: int, y: int, w: int, h: int):
        global buffer
        buf = ptr8(buffer)
        frame = int(Scanner.frame)
        randomPattern = int(Scanner.randomPattern)

        dx1, dx2 = int(max(0, x)), int(min(72, x+w))
        dy1, dy2 = int(max(0, y)), int(min(40, y+h))

        if dx1 == dx2 or dy1 == dy2:
            return

        sx1 = dx1 - x
        sx2 = sx1 + dx2 - dx1
        sy1 = dy1 - y
        sy2 = sy1 + dy2 - dy1

        dstX = dx1
        for srcX in range(sx1, sx2):
            dstY = dy1
            rpo = srcX & 0b11111
            for srcY in range(sy1, sy2):
                i = ((dstY >> 3)*72+dstX)*8+(dstY & 0b111)
                v = buf[i]
                if (v & 0b10000000) and (randomPattern & (0b1 << rpo)):
                    buf[i] = 0b01  # White Flat
                dstY += 1
                rpo = (rpo + 1) & 0b11111
            dstX += 1


class Zones:
    def speedLimit(ship, speed_f3: int, x: int, y: int, w: int, h: int):
        px = int(ship.px_f3) >> 3
        py = int(ship.py_f3) >> 3
        if (x <= px <= x + w) and (y <= py <= y + h):
            if not ship.speedLimited or ship.speedLimit_f3 > speed_f3:
                ship.speedLimited = True
                ship.speedLimit_f3 = speed_f3

    def angleLock(ship, angle: int, x: int, y: int, w: int, h: int):
        px = int(ship.px_f3) >> 3
        py = int(ship.py_f3) >> 3
        if (x <= px <= x + w) and (y <= py <= y + h):
            ship.angleLocked = True
            ship.angleLock = angle


ship = Ship(impShip, speedMax_f3=2 << 3, accel_f3=1,
            dampening_f6=62, boost_f3=3 << 3, boostDelay=60, rotateSpeed=5)

camX, camY = 268, 30
lastCamX, lastCamY = camX, camY
ship.px_f3 = camX << 3
ship.py_f3 = camY << 3
ship.angle = 180
ship.angleTarget = ship.angle
lightAngle = 0

while True:
    perf.start()

    if buttonA.justPressed():
        lightAngle = (lightAngle + 1) % 8
    if buttonB.justPressed():
        lightAngle = (lightAngle + 7) % 8

    ship.speedLimited = False
    for objSlowZone in station.slowZones:
        x, y, w, h = objSlowZone
        Zones.speedLimit(ship, 6, x, y, w, h)
    for objScanner in station.scanners:
        x, y, w, h = objScanner
        Zones.speedLimit(ship, 4, x-5, y-5, w+10, h+10)

    ship.angleLocked = False
    for objDock in station.docks:
        x, y, dir = objDock
        Zones.angleLock(ship, ((dir+1) & 0b11)*90, x-20, y-10, 40, 20)

    ship.inputButtons()
    ship.moveFrame()

    camX = (ship.px_f3 >> 3) - 36 + (ship.vx_f3 >> 3)
    camY = (ship.py_f3 >> 3) - 20 + (ship.vy_f3 >> 3)
    camDX = camX - lastCamX
    camDY = camY - lastCamY
    lastCamX = camX
    lastCamY = camY

    fill(buffer, 0b00)

    SpaceBits.render(camX, camY, camDX, camDY)

    blitContainerMap(buffer, station, -camX, -camY)

    for objText in station.smallTexts:
        text, x, y, dir, color = objText
        blitText(buffer, font3x3, text, x-camX, y-camY, dir)

    for objText in station.largeTexts:
        text, x, y, dir, color = objText
        blitText(buffer, font4x4, text, x-camX, y-camY, dir)

    ship.render(camX, camY)

    Scanner.update()
    for objScanner in station.scanners:
        x, y, w, h = objScanner
        Scanner.render(x-camX, y-camY, w, h)

    for objGate in station.gates:
        x, y, dir = objGate
        if dir & 0b1:
            imp, iw, ih = impGateH
        else:
            imp, iw, ih = impGateV
        blit(buffer, imp, x-camX-(iw >> 1), y-camY-(ih >> 1), iw, ih)

    postShading(buffer, shader, lightAngle)
    display(buffer)
    perf.stop()

    perf.render()
    update()

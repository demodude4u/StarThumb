from sys import path as syspath  # NOQA
syspath.insert(0, '/Games/DemoST1Transport')  # NOQA

import math
import gc
import random

from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

from STGraphics import fill, blit, blitRotate, blitScale, display, update, setFPS, postShading, blitText, perfStart, perfStop, perfRender, blitContainerMap, Font
from STData import PackReader

gc.collect()

buffer = bytearray(72*40)

with PackReader("/Games/DemoST1Transport/Demo1.pack") as pack:
    shader = pack.readShader()

    impTiles = pack.readIMP()

    font3x3 = Font(3, 3, pack.readIMP())
    font4x4 = Font(4, 4, pack.readIMP())

    impGateH = pack.readIMP()
    impGateV = pack.readIMP()

    impGateSmall = pack.readIMP()
    impGateSmallBlur1 = pack.readIMP()
    impGateSmallBlur2 = pack.readIMP()

    impShipSmall = pack.readIMP()
    impShip = pack.readIMP()

    impShip2Small = pack.readIMP()
    impShip2 = pack.readIMP()

    pack.loadContainers(2, impTiles)
    areaAlpha = pack.readArea()

    pack.loadContainers(3, impTiles)
    areaBeta = pack.readArea()

    pack.loadContainers(2, impTiles)
    areaGamma = pack.readArea()

gc.collect()

# Features Not Experimented:
# - Thruster particles/animation
# - Gate Sequence
# - Docking Camera
# - Glimmer
# - Trails

# Experiments To Implement:
# - TestAnimate
# - TestParticles


class Ship:
    def __init__(self, impShip, impTinyShip, speedMax_f3, accel_f3, dampening_f6, boost_f3, boostDelay, rotateSpeed):
        self.impShip = impShip
        self.impTinyShip = impTinyShip
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
        self.dirSpeedLimited = False
        self.speedLimit_f3 = 0
        self.speedLimitDir = 0
        self.angleLocked = False
        self.angleLock = 0
        self.gateLocked = False
        self.gate = None
        self.gateEnter = False
        self.gateSpeed_f3 = 0
        self.gateDistance_f3 = 0

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
        dirSpeedLimited = self.dirSpeedLimited
        speedLimit_f3 = self.speedLimit_f3
        speedLimitDir = self.speedLimitDir
        angleLocked = self.angleLocked
        angleLock = self.angleLock
        gateLocked = self.gateLocked
        gate = self.gate
        gateEnter = self.gateEnter
        gateSpeed_f3 = self.gateSpeed_f3
        gateDistance_f3 = self.gateDistance_f3

        if gateLocked:
            gx, gy, gdir = gate
            if gateEnter:
                gdir = (gdir + 2) & 0b11
            speedMax_f3 = gateSpeed_f3
            boost_f3 = gateSpeed_f3
            if gdir == 0:
                inputX_f3, inputY_f3 = 8, 0
                vx_f3, vy_f3 = gateSpeed_f3, 0
                self.px_f3 = (gx << 3) + gateDistance_f3
                self.py_f3 += ((gy << 3) - self.py_f3) >> 1
            elif gdir == 1:
                inputX_f3, inputY_f3 = 0, 8
                vx_f3, vy_f3 = 0, gateSpeed_f3
                self.px_f3 += ((gx << 3) - self.px_f3) >> 1
                self.py_f3 = (gy << 3) + gateDistance_f3
            elif gdir == 2:
                inputX_f3, inputY_f3 = -8, 0
                vx_f3, vy_f3 = -gateSpeed_f3, 0
                self.px_f3 = (gx << 3) - gateDistance_f3
                self.py_f3 += ((gy << 3) - self.py_f3) >> 1
            else:
                inputX_f3, inputY_f3 = 0, -8
                vx_f3, vy_f3 = 0, -gateSpeed_f3
                self.px_f3 += ((gx << 3) - self.px_f3) >> 1
                self.py_f3 = (gy << 3) - gateDistance_f3

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

        if dirSpeedLimited:
            speedLimited = False
            if speedLimitDir == 0 and vx_f3 > 0:
                speedLimited = True
            elif speedLimitDir == 1 and vy_f3 > 0:
                speedLimited = True
            elif speedLimitDir == 2 and vx_f3 < 0:
                speedLimited = True
            elif speedLimitDir == 3 and vy_f3 < 0:
                speedLimited = True

        if speedLimited:
            if speedMax_f3 > speedLimit_f3:
                speedMax_f3 = speedLimit_f3
            if boost_f3 > speedLimit_f3:
                boost_f3 = speedLimit_f3

        if inputX_f3 and vx_f3 < -speedMax_f3:
            boostFrames += 1
            vx_f3 = -speedMax_f3 if boostFrames < boostDelay else -boost_f3
        elif inputX_f3 and vx_f3 > speedMax_f3:
            boostFrames += 1
            vx_f3 = speedMax_f3 if boostFrames < boostDelay else boost_f3

        if inputY_f3 and vy_f3 < -speedMax_f3:
            boostFrames += 1
            vy_f3 = -speedMax_f3 if boostFrames < boostDelay else -boost_f3
        elif inputY_f3 and vy_f3 > speedMax_f3:
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

        if gateLocked:
            gx, gy, gdir = gate
            if gateEnter:
                gdir = (gdir + 2) & 0b11
            if gdir == 0:
                self.gateDistance_f3 = self.px_f3 - (gx << 3)
            elif gdir == 1:
                self.gateDistance_f3 = self.py_f3 - (gy << 3)
            elif gdir == 2:
                self.gateDistance_f3 = (gx << 3) - self.px_f3
            else:
                self.gateDistance_f3 = (gy << 3) - self.py_f3

            if gateEnter and self.gateDistance_f3 >= 8:
                self.gateEnter = False
                self.gateLocked = False

        self.boostFrames = boostFrames
        self.angle = angle

    @micropython.native
    def moveGateTravelFrame(self):
        vx_f3 = self.vx_f3
        vy_f3 = self.vy_f3

        self.px_f3 += vx_f3
        self.py_f3 += vy_f3

    @micropython.native
    def render(self, camX: int, camY: int):
        global buffer

        imp, iw, ih = self.impShip
        hw = iw >> 1
        hh = ih >> 1
        x = (self.px_f3 >> 3) - camX - hw
        y = (self.py_f3 >> 3) - camY - hh
        blitRotate(buffer, imp, self.angle, x, y, iw, ih, hw, hh)

    @micropython.native
    def renderTiny(self, camX: int, camY: int):
        global buffer

        imp, iw, ih = self.impTinyShip
        hw = iw >> 1
        hh = ih >> 1
        x = (((self.px_f3 >> 3) - camX) >> 1) - hw
        y = (((self.py_f3 >> 3) - camY) >> 1) - hh
        blitRotate(buffer, imp, self.angle, x, y, iw, ih, hw, hh)

    @micropython.native
    def renderZoomed(self, camX: int, camY: int, zoom_f6: int):
        global buffer

        imp, iw, ih = self.impShip
        hw = iw >> 1
        hh = ih >> 1
        x = ((zoom_f6 * ((self.px_f3 >> 3) - camX)) >> 6) - hw
        y = ((zoom_f6 * ((self.py_f3 >> 3) - camY)) >> 6) - hh
        dir = self.angle // 90
        blitScale(buffer, imp, zoom_f6, x, y, iw, ih, hw, hh, dir)


class SpaceBits:
    # 16x16 cells, 12 columns, 8 rows
    # Cell format: 4-bit x, 4-bit y
    layer1 = bytearray((random.randrange(0, 256) for _ in range(12*8)))
    layer2 = bytearray((random.randrange(0, 256) for _ in range(12*8)))
    speedColors = bytes([0b10, 0b11, 0b01])

    @micropython.viper
    def render(px: int, py: int, vx: int, vy: int):
        global buffer

        sb1 = ptr8(SpaceBits.layer1)
        sb2 = ptr8(SpaceBits.layer2)
        speedColors = ptr8(SpaceBits.speedColors)

        # speed = 0
        # if vx > 0:
        #     speed += vx
        # else:
        #     speed -= vx
        # if vy > 0:
        #     speed += vy
        # else:
        #     speed -= vy

        cShift = (px >> 5) % 12
        cPixel = (px >> 1) & 0b1111
        rShift = (py >> 5) % 8
        rPixel = (py >> 1) & 0b1111
        # color = speedColors[int(min(2, (speed+1) >> 1))]
        color = 0b10

        for sr in range(4):
            for sc in range(6):
                c = (sc + cShift) % 12
                r = (sr + rShift) % 8
                cell = sb1[r*12+c]
                cx = cell & 0b1111
                cy = (cell >> 4) & 0b1111
                x = sc * 16 + cx - cPixel
                y = sr * 16 + cy - rPixel
                if x < 0 or x >= 72 or y < 0 or y >= 40:
                    continue
                buffer[((y >> 3)*72+x)*8+(y & 0b111)] = color

        cShift = (px >> 6) % 12
        cPixel = (px >> 2) & 0b1111
        rShift = (py >> 6) % 8
        rPixel = (py >> 2) & 0b1111
        # color = speedColors[int(min(2, (speed+3) >> 2))]

        for sr in range(4):
            for sc in range(6):
                c = (sc + cShift) % 12
                r = (sr + rShift) % 8
                cell = sb2[r*12+c]
                cx = cell & 0b1111
                cy = (cell >> 4) & 0b1111
                x = sc * 16 + cx - cPixel
                y = sr * 16 + cy - rPixel
                if x < 0 or x >= 72 or y < 0 or y >= 40:
                    continue
                buffer[((y >> 3)*72+x)*8+(y & 0b111)] = color

    @micropython.viper
    def renderZoomed(px: int, py: int, vx: int, vy: int, zoom_f6: int):
        global buffer

        sb1 = ptr8(SpaceBits.layer1)
        sb2 = ptr8(SpaceBits.layer2)
        speedColors = ptr8(SpaceBits.speedColors)

        # maxSize = (zoom_f6 >> 3) - 4

        # speed = 0
        # if vx > 0:
        #     speed += vx
        # else:
        #     speed -= vx
        # if vy > 0:
        #     speed += vy
        # else:
        #     speed -= vy

        # speed = (zoom_f6 * speed) >> 6
        cellSize_f2 = (zoom_f6 * 16) >> 4

        xo_f2 = 144 - 6 * cellSize_f2
        yo_f2 = 80 - 4 * cellSize_f2
        color = 0b10

        for layer in range(2):
            cShift = (px // cellSize_f2) % 12
            cPixel_f2 = px % cellSize_f2
            rShift = (py // cellSize_f2) % 8
            rPixel_f2 = py % cellSize_f2
            # color = speedColors[int(min(2, (speed+1) >> 1))]

            for sr in range(8):
                for sc in range(12):
                    c = (sc + cShift) % 12
                    r = (sr + rShift) % 8
                    cell = sb1[r*12+c]
                    # size = ((cell & 0b10000) >> 3) | (cell & 0b1)
                    # if size > maxSize:
                    #     continue
                    px_f2 = (zoom_f6 * (cell & 0b1111)) >> 4
                    py_f2 = (zoom_f6 * (((cell >> 4) & 0b1111))) >> 4
                    x = (sc * cellSize_f2 + px_f2 - cPixel_f2 + xo_f2) >> 2
                    y = (sr * cellSize_f2 + py_f2 - rPixel_f2 + yo_f2) >> 2
                    if x < 0 or x >= 72 or y < 0 or y >= 40:
                        continue
                    buffer[((y >> 3)*72+x)*8+(y & 0b111)] = color
            px >>= 1
            py >>= 1
            # speed >>= 1


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
    def dirSpeedLimit(ship, speed_f3: int, x: int, y: int, w: int, h: int, dir: int):
        px = int(ship.px_f3) >> 3
        py = int(ship.py_f3) >> 3
        if (x <= px <= x + w) and (y <= py <= y + h):
            if not ship.speedLimited or ship.speedLimit_f3 > speed_f3:
                ship.dirSpeedLimited = True
                ship.speedLimit_f3 = speed_f3
                ship.speedLimitDir = dir

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

    def gateLock(ship, gate, gateSpeed_f3):
        if ship.gateLocked:
            return

        px = int(ship.px_f3) >> 3
        py = int(ship.py_f3) >> 3
        gx, gy, gdir = gate
        if gdir == 0:
            x, y, w, h = gx, gy - 16, 8, 32
        elif gdir == 1:
            x, y, w, h = gx - 16, gy, 32, 8
        elif gdir == 2:
            x, y, w, h = gx - 8, gy - 16, 8, 32
        else:
            x, y, w, h = gx - 16, gy - 8, 32, 8
        if (x <= px <= x + w) and (y <= py <= y + h):
            ship.gateLocked = True
            ship.gate = gate
            ship.gateSpeed_f3 = gateSpeed_f3
            ship.gateDistance_f3 = 0
            ship.angle = gdir * 90


class GateTravel:
    def loop():
        global ship, camX, camY, lastCamX, lastCamY, lightAngle

        travelStage = 0
        stageFrames = 0

        zoomTime = 30 * 3
        turnTime = 60 * 10

        speedStart_f3 = 5 << 3
        speedTurn_f3 = 10 << 3
        speed_f3 = speedStart_f3

        gateRate = 15
        gateFrame = 0
        gateX_f3 = 0
        gateY_f3 = 0

        zoom_f6 = 64

        fps = 30

        while True:
            perfStart()

            stageFrames += 1

            if travelStage == 0:  # Stage 0 Speed up (zoom out)
                ship.angle = 0
                zoom_f6 = 64 - ((32 * stageFrames) // zoomTime)
                speed_f3 = speedStart_f3 + \
                    (((speedTurn_f3 - speedStart_f3) * stageFrames) // zoomTime)
                if stageFrames > zoomTime:
                    travelStage += 1
                    stageFrames = 0
                gateRate = 15 + ((15 * stageFrames) // zoomTime)
                fps = 30 + ((30 * stageFrames) // zoomTime)

            elif travelStage == 1:  # Stage 1 Round the corner
                ship.angle = (360 - ((90 * stageFrames) // turnTime)) % 360
                zoom_f6 = 32
                speed_f3 = speedTurn_f3
                if stageFrames > turnTime:
                    travelStage += 1
                    stageFrames = 0
                gateRate = 30
                fps = 60

            elif travelStage == 2:  # Stage 2 Slow down (zoom in)
                ship.angle = 270
                zoom_f6 = 32 + ((32 * stageFrames) // zoomTime)
                speed_f3 = speedTurn_f3 - \
                    (((speedTurn_f3 - speedStart_f3) * stageFrames) // zoomTime)
                if stageFrames > zoomTime:
                    travelStage += 1
                    stageFrames = 0
                gateRate = 30 - ((15 * stageFrames) // zoomTime)
                fps = 60 - ((30 * stageFrames) // zoomTime)

            # speed_f3 = speedStart_f3 # XXX TESTING
            # zoom_f6 = 64 # XXX TESTING

            setFPS(fps)

            angleRad = (ship.angle * 3.14159) / 180.0
            ship.vx_f3 = int(speed_f3 * math.cos(angleRad))
            ship.vy_f3 = int(speed_f3 * math.sin(angleRad))

            ship.moveGateTravelFrame()

            zhw, zhh = (64 * 36) // zoom_f6, (64 * 20) // zoom_f6

            if gateFrame >= gateRate:
                gateFrame = 0
            if gateFrame == 0:
                rad = math.atan2(ship.vy_f3, ship.vx_f3)
                dist_f3 = (zhw + 8) << 3
                gateX_f3 = int(ship.px_f3 + dist_f3 * math.cos(rad))
                gateY_f3 = int(ship.py_f3 + dist_f3 * math.sin(rad))
            gateX_f3 -= ship.vx_f3
            gateY_f3 -= ship.vy_f3
            gateFrame += 1

            camX = (ship.px_f3 >> 3) - zhw + (ship.vx_f3 >> 3)
            camY = (ship.py_f3 >> 3) - zhh + (ship.vy_f3 >> 3)
            camDX = camX + zhw - lastCamX
            camDY = camY + zhh - lastCamY
            lastCamX = camX + zhw
            lastCamY = camY + zhh

            fill(buffer, 0b00)

            SpaceBits.renderZoomed(camX, camY, camDX, camDY, zoom_f6)

            if zoom_f6 > 32:
                ship.renderZoomed(camX, camY, zoom_f6)
                GateTravel.renderGateZoomed(
                    gateX_f3, gateY_f3, camX, camY, ship.angle, zoom_f6)
            else:
                ship.renderTiny(camX, camY)
                GateTravel.renderGateTiny(
                    gateX_f3, gateY_f3, camX, camY, ship.angle)

            postShading(buffer, shader, lightAngle)
            display(buffer)
            perfStop()

            perfRender()
            update()

            if travelStage == 3:  # Exit Loop
                ship.gateLocked = True
                ship.gateEnter = True
                ship.gate = station.gates[0]
                ship.gateDistance_f3 = (0-36) << 3
                ship.gateSpeed_f3 = 5 << 3
                ship.px_f3 = ship.gate[0] << 3
                ship.py_f3 = ship.gate[1] << 3
                setFPS(30)
                break

    @micropython.native
    def renderGateTiny(px_f3: int, py_f3: int, camX: int, camY: int, angle: int):
        global buffer, impGateSmall

        imp, iw, ih = impGateSmall
        hw = iw >> 1
        hh = ih >> 1
        x = (((px_f3 >> 3) - camX) >> 1) - hw
        y = (((py_f3 >> 3) - camY) >> 1) - hh
        blitRotate(buffer, imp, angle, x, y, iw, ih, hw, hh)

    @micropython.native
    def renderGateZoomed(px_f3: int, py_f3: int, camX: int, camY: int, angle: int, zoom_f6: int):
        global buffer, impGateV

        imp, iw, ih = impGateV
        hw = iw >> 1
        hh = ih >> 1
        x = ((zoom_f6 * ((px_f3 >> 3) - camX)) >> 6) - hw
        y = ((zoom_f6 * ((py_f3 >> 3) - camY)) >> 6) - hh
        dir = angle // 90
        blitScale(buffer, imp, zoom_f6, x, y, iw, ih, hw, hh, dir)


area = areaAlpha
containers = area.containers

ship1 = Ship(impShip, impShipSmall, speedMax_f3=2 << 3, accel_f3=1,
             dampening_f6=62, boost_f3=3 << 3, boostDelay=60, rotateSpeed=5)
ship2 = Ship(impShip2, impShip2Small, speedMax_f3=3 << 3, accel_f3=2,
             dampening_f6=60, boost_f3=4 << 3, boostDelay=45, rotateSpeed=8)

ship = ship1
camLock = False
camX, camY = 92, 30
lastCamX, lastCamY = camX, camY
ship.px_f3 = camX << 3
ship.py_f3 = camY << 3
ship.angle = 180
ship.angleTarget = ship.angle
lightAngle = 0

# Teaser 1 - Pad and Scanner
# camLock = True
# camX, camY = 98, 68
# ship = ship2
# ship.px_f3 = 126 << 3
# ship.py_f3 = 92 << 3
# ship.angle = 90
# ship.angleTarget = ship.angle
# lightAngle = 5
# ship.accel_f3 = 1

while True:
    perfStart()

    if buttonA.justPressed():
        lightAngle = (lightAngle + 1) % 8
    if buttonB.justPressed():
        ship = ship2 if ship == ship1 else ship1

    ship.speedLimited = False
    ship.dirSpeedLimited = False
    for container in containers:
        for objDirSlowZone in container.dirSlowZones:
            x, y, w, h, dir = objDirSlowZone
            Zones.dirSpeedLimit(ship, 6, x, y, w, h, dir)
        for objSlowZone in container.slowZones:
            x, y, w, h = objSlowZone
            Zones.speedLimit(ship, 6, x, y, w, h)
        for objScanner in container.scanners:
            x, y, w, h = objScanner
            Zones.speedLimit(ship, 4, x-5, y-5, w+10, h+10)

    ship.angleLocked = False
    for container in containers:
        for objDock in container.docks:
            x, y, dir = objDock
            Zones.angleLock(ship, ((dir+1) & 0b11)*90, x-20, y-10, 40, 20)
        for objPad in container.pads:
            x, y, dir = objPad
            Zones.angleLock(ship, ship.angleTarget, x-8, y-8, 16, 16)

        for objGate in container.gates:
            Zones.gateLock(ship, objGate, 5 << 3)

    ship.inputButtons()
    ship.moveFrame()

    if not camLock:
        camX = (ship.px_f3 >> 3) - 36 + (ship.vx_f3 >> 3)
        camY = (ship.py_f3 >> 3) - 20 + (ship.vy_f3 >> 3)
    camDX = camX - lastCamX
    camDY = camY - lastCamY
    lastCamX = camX
    lastCamY = camY

    fill(buffer, 0b00)

    SpaceBits.render(camX, camY, camDX, camDY)

    for container in containers:
        blitContainerMap(buffer, container, -camX, -camY)

        for objText in container.smallTexts:
            text, x, y, dir = objText
            blitText(buffer, font3x3, text, x-camX, y-camY, dir)

        for objText in container.largeTexts:
            text, x, y, dir = objText
            blitText(buffer, font4x4, text, x-camX, y-camY, dir)

    ship.render(camX, camY)

    for container in containers:
        Scanner.update()
        for objScanner in container.scanners:
            x, y, w, h = objScanner
            Scanner.render(x-camX, y-camY, w, h)

        for objGate in container.gates:
            x, y, dir = objGate
            if dir & 0b1:
                imp, iw, ih = impGateH
            else:
                imp, iw, ih = impGateV
            blit(buffer, imp, x-camX-(iw >> 1), y-camY-(ih >> 1), iw, ih)

    postShading(buffer, shader, lightAngle)
    display(buffer)
    perfStop()

    perfRender()
    update()

    if ship.gateLocked and not ship.gateEnter and ship.gateDistance_f3 > (36 << 3):
        GateTravel.loop()

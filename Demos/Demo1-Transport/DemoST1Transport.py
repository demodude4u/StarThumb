from sys import path as syspath  # NOQA
syspath.insert(0, '/Games/DemoST1Transport')  # NOQA

import math
import gc
import random

buffer = bytearray(72*40)

from STData import PackReader, Font, Container, NODE_TYPE_PAD, NODE_TYPE_DOCK, NODE_TYPE_GATE  # NOQA

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

    impShipSm = pack.readIMP()
    impShip = pack.readIMP()

    impShip2Sm = pack.readIMP()
    impShip2 = pack.readIMP()

    impShipSkull = pack.readIMP()
    impShipMF = pack.readIMP()
    impShipThumb = pack.readIMP()
    impShipNyan = pack.readIMPFrames()

    impLogo32 = pack.readIMP()

    pack.loadContainers(7, impTiles)
    pack.loadAreas(3)

    starSystem = pack.readSystem()

pack.file = None
pack = None
gc.collect()
print("After pack:", gc.mem_free())

from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR  # NOQA

gc.collect()

from STGraphics import (  # NOQA
    fill,
    blit,
    blitRotate,
    blitScale,
    display,
    update,
    setFPS,
    postShading,
    blitText,
    perfStart,
    perfStop,
    perfRender,
    blitContainerMap,
)

gc.collect()

print(gc.mem_free())

# Features Not Experimented:
# - Thruster particles/animation
# - Docking Camera
# - Glimmer
# - Trails

# Experiments To Implement:
# - TestAnimate
# - TestParticles

area = None
containers = []

SHIP_SIZECLASS_SMALL = const(0)
SHIP_SIZECLASS_MEDIUM = const(1)


# TODO this is terrible and slow
STOPPING_DISTANCES = [0 for _ in range((8 << 3) + 1)]  # Max speed
STANDARD_DAMPENING_F6 = 62
for i in range(len(STOPPING_DISTANCES)):
    v_f3 = i
    p_f3 = 0
    while v_f3:
        v_f3 = (v_f3 * STANDARD_DAMPENING_F6) >> 6
        p_f3 += v_f3
    STOPPING_DISTANCES[i] = p_f3 >> 3


class Ship:
    def __init__(self, impShip, impTinyShip, sizeClass, speedMax_f3, accel_f3,
                 dampening_f6, boost_f3, boostDelay, rotateSpeed):
        self.impShip = impShip
        self.impTinyShip = impTinyShip
        self.sizeClass = sizeClass
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
        self.container = None
        self.chunk = None
        self.autopilot = False
        self.apTargetAreaCode = None
        self.apTargetDestinationCode = None
        self.apCurrentDestinationCode = None
        self.apCurrentPoint = None
        self.apSlowdown = False
        self.apNextPoint = None

        if len(impShip) < 4:
            self.anim = False
            self.frameCount = 0
            self.frameTime = 0
        else:
            frameCount = impShip[3]
            self.anim = True
            self.frameCount = frameCount
            self.frameTime = 30 // frameCount  # TODO configurable
        self.frameIndex = 0
        self.frameDuration = 0

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

    def findAutopilotDestination(self):
        if area.code == self.apTargetAreaCode:
            if self.apTargetDestinationCode:
                self.apCurrentDestinationCode = self.apTargetDestinationCode
            else:  # Find a Dock or Pad
                if self.sizeClass == SHIP_SIZECLASS_SMALL:
                    destinationCodeChoices = [
                        np.obj.code for np in area.navPoints if np.nodeType == NODE_TYPE_PAD]
                else:
                    destinationCodeChoices = [
                        np.obj.code for np in area.navPoints if np.nodeType == NODE_TYPE_DOCK]
                self.apCurrentDestinationCode = destinationCodeChoices[random.randrange(
                    len(destinationCodeChoices))]
        else:  # Find the correct Gate
            # print("Finding Gate towards", self.apTargetAreaCode)
            # for k, v in area.gateDestinations.items():
            #     print("\t", k, " ==> ", v[0], v[1].code, v[2])
            self.apCurrentDestinationCode = area.gateDestinations[self.apTargetAreaCode][0]
        # print("Target Destination", self.apCurrentDestinationCode)

    @staticmethod
    def findAutopilotNearestPoint(x, y):
        nearestPoint = None
        nearestDistance = -1
        for navPoint in area.navPoints:
            distance = abs(x - navPoint.x) + abs(y - navPoint.y)
            if not nearestPoint or distance < nearestDistance:
                nearestPoint = navPoint
                nearestDistance = distance
        return nearestPoint

    @micropython.native
    def inputAutopilot(self):
        if not self.autopilot:
            self.inputX_f3 = 0
            self.inputY_f3 = 0
            return

        sx = self.px_f3 >> 3
        sy = self.py_f3 >> 3

        # Find Current Destination (Destination Code)
        if not self.apCurrentDestinationCode:
            self.findAutopilotDestination()

        # Find Nearest Point
        if not self.apCurrentPoint:
            self.apCurrentPoint = Ship.findAutopilotNearestPoint(sx, sy)

        navPoint = self.apCurrentPoint
        nx = navPoint.x
        ny = navPoint.y

        dx = nx - sx
        dy = ny - sy
        adx = abs(dx)
        ady = abs(dy)

        slowdown = self.apSlowdown
        if slowdown:
            avx_f3 = abs(ship.vx_f3)
            avy_f3 = abs(ship.vy_f3)
            if avx_f3 or avy_f3:
                if avx_f3 > avy_f3:
                    stopDistance = (
                        STOPPING_DISTANCES[avx_f3] * STANDARD_DAMPENING_F6) // ship.dampening_f6
                    if stopDistance + 5 < adx:
                        slowdown = False
                else:
                    stopDistance = (
                        STOPPING_DISTANCES[avy_f3] * STANDARD_DAMPENING_F6) // ship.dampening_f6
                    if stopDistance + 5 < ady:
                        slowdown = False
                # print(slowdown, dx, dy,"|", avx_f3, avy_f3, "|", stopDistance)
            else:
                slowdown = False
                # print(slowdown, dx, dy,"|", avx_f3, avy_f3)

        inputX_f3, inputY_f3 = 0, 0
        if slowdown:
            pass
        elif adx < ady and adx > 4:
            inputX_f3 = 8 if dx > 0 else -8
            inputY_f3 = 0
        elif ady > 4:
            inputX_f3 = 0
            inputY_f3 = 8 if dy > 0 else -8
        elif adx:
            inputX_f3 = 8 if dx > 0 else -8
        elif ady:
            inputY_f3 = 8 if dy > 0 else -8
        self.inputX_f3 = inputX_f3
        self.inputY_f3 = inputY_f3

        # Next Point
        # print(abs(dx) + abs(dy))
        if abs(dx) <= 6 and abs(dy) <= 6:
            # print("Next Point")
            if navPoint.nodeType:  # Not Basic
                code = navPoint.obj.code
                if area.code == self.apTargetAreaCode and code == self.apCurrentDestinationCode:
                    self.apCurrentPoint = None
                    self.apCurrentDestinationCode = None
                    self.autopilot = False
            if self.autopilot:
                # TODO find a faster way instead of using string keys
                pp = navPoint
                cp = navPoint.destinations[self.apCurrentDestinationCode][0]
                self.apCurrentPoint = cp
                if not cp.nodeType:  # Is Basic
                    np = cp.destinations[self.apCurrentDestinationCode][0]
                    if np:
                        cdx = cp.x - pp.x
                        cdy = cp.y - pp.y
                        ndx = np.x - cp.x
                        ndy = np.y - cp.y
                        # Checks if heading same direction
                        if (cdx * ndx > 0 or cdy * ndy > 0) and (abs(cdx) > abs(cdy) == abs(ndx) > abs(ndy)):
                            self.apSlowdown = False
                        else:
                            self.apSlowdown = True
                    else:
                        self.apSlowdown = False
                else:
                    self.apSlowdown = False

    @micropython.native
    def updateContainer(self):
        sx = self.px_f3 >> 3
        sy = self.py_f3 >> 3
        for container in containers:
            cx1 = container.x1
            cy1 = container.y1
            cx2 = container.x2
            cy2 = container.y2
            if cx1 <= sx < cx2 and cy1 <= sy < cy2:
                self.container = container
                # print(sx, sy, "|", cx1, cy1, cx2, cy2, "|", (
                #     (sy-cy1) >> 6)*container.chunkColumns+((sx-cx1) >> 6), len(container.chunks) )
                self.chunk = container.chunks[(
                    (sy-cy1) >> 6)*container.chunkColumns+((sx-cx1) >> 6)]
                return
        self.container = None
        self.chunk = None

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
            _, gx, gy, gdir = gate
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
        if abs(vx_f3) or abs(vy_f3):
            # if abs(vx_f3) >= speedMax_f3 or abs(vy_f3) >= speedMax_f3:
            self.angleTarget = int(
                180*(math.atan2(vy_f3, vx_f3)/3.14159))

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
            _, gx, gy, gdir = gate
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

        if self.anim:
            if self.frameDuration >= self.frameTime:
                self.frameDuration = 0
                self.frameIndex = (self.frameIndex + 1) % self.frameCount
            else:
                self.frameDuration += 1

    @micropython.native
    def moveGateTravelFrame(self):
        vx_f3 = self.vx_f3
        vy_f3 = self.vy_f3

        self.px_f3 += vx_f3
        self.py_f3 += vy_f3

    @micropython.native
    def render(self, camX: int, camY: int):
        if self.anim:
            imps, iw, ih, _ = self.impShip
            imp = imps[self.frameIndex]
        else:
            imp, iw, ih = self.impShip
        hw = iw >> 1
        hh = ih >> 1
        x = (self.px_f3 >> 3) - camX - hw
        y = (self.py_f3 >> 3) - camY - hh
        blitRotate(buffer, imp, self.angle, x, y, iw, ih, hw, hh)

    @micropython.native
    def renderTiny(self, camX: int, camY: int):
        if self.anim:
            imps, iw, ih, _ = self.impTinyShip
            imp = imps[self.frameIndex]
        else:
            imp, iw, ih = self.impTinyShip
        hw = iw >> 1
        hh = ih >> 1
        x = (((self.px_f3 >> 3) - camX) >> 1) - hw
        y = (((self.py_f3 >> 3) - camY) >> 1) - hh
        blitRotate(buffer, imp, self.angle, x, y, iw, ih, hw, hh)

    @micropython.native
    def renderZoomed(self, camX: int, camY: int, zoom_f6: int):
        if self.anim:
            imps, iw, ih, _ = self.impShip
            imp = imps[self.frameIndex]
        else:
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

    @staticmethod
    @micropython.viper
    def render(px: int, py: int):
        sb1 = ptr8(SpaceBits.layer1)
        sb2 = ptr8(SpaceBits.layer2)

        cShift = (px >> 5) % 12
        cPixel = (px >> 1) & 0b1111
        rShift = (py >> 5) % 8
        rPixel = (py >> 1) & 0b1111
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

    @staticmethod
    @micropython.viper
    def renderZoomed(px: int, py: int, zoom_f6: int):
        sb1 = ptr8(SpaceBits.layer1)
        sb2 = ptr8(SpaceBits.layer2)

        cellSize_f2 = (zoom_f6 * 16) >> 4

        xo_f2 = 144 - 6 * cellSize_f2
        yo_f2 = 80 - 4 * cellSize_f2
        color = 0b10

        for layer in range(2):
            cShift = (px // cellSize_f2) % 12
            cPixel_f2 = px % cellSize_f2
            rShift = (py // cellSize_f2) % 8
            rPixel_f2 = py % cellSize_f2

            for sr in range(8):
                for sc in range(12):
                    c = (sc + cShift) % 12
                    r = (sr + rShift) % 8
                    cell = sb1[r*12+c] if layer == 1 else sb2[r*12+c]
                    px_f2 = (zoom_f6 * (cell & 0b1111)) >> 4
                    py_f2 = (zoom_f6 * (((cell >> 4) & 0b1111))) >> 4
                    x = (sc * cellSize_f2 + px_f2 - cPixel_f2 + xo_f2) >> 2
                    y = (sr * cellSize_f2 + py_f2 - rPixel_f2 + yo_f2) >> 2
                    if x < 0 or x >= 72 or y < 0 or y >= 40:
                        continue
                    buffer[((y >> 3)*72+x)*8+(y & 0b111)] = color
            px >>= 1
            py >>= 1


class Scanner:
    randomPattern = 0
    randomOffset = 0

    @staticmethod
    def update():
        Scanner.randomPattern = random.getrandbits(32)

    @staticmethod
    @micropython.viper
    def render(x: int, y: int, w: int, h: int):
        buf = ptr8(buffer)
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
            for _ in range(sy1, sy2):
                i = ((dstY >> 3)*72+dstX)*8+(dstY & 0b111)
                v = buf[i]
                if (v & 0b10000000) and (randomPattern & (0b1 << rpo)):
                    buf[i] = 0b01  # White Flat
                dstY += 1
                rpo = (rpo + 1) & 0b11111
            dstX += 1


class Zones:
    @staticmethod
    def dirSpeedLimit(ship, speed_f3: int, x: int, y: int, w: int, h: int, dir: int):
        px = int(ship.px_f3) >> 3
        py = int(ship.py_f3) >> 3
        if (x <= px <= x + w) and (y <= py <= y + h):
            if not ship.speedLimited or ship.speedLimit_f3 > speed_f3:
                ship.dirSpeedLimited = True
                ship.speedLimit_f3 = speed_f3
                ship.speedLimitDir = dir

    @staticmethod
    def speedLimit(ship, speed_f3: int, x: int, y: int, w: int, h: int):
        px = int(ship.px_f3) >> 3
        py = int(ship.py_f3) >> 3
        if (x <= px <= x + w) and (y <= py <= y + h):
            if not ship.speedLimited or ship.speedLimit_f3 > speed_f3:
                ship.speedLimited = True
                ship.speedLimit_f3 = speed_f3

    @staticmethod
    def angleLock(ship, angle: int, x: int, y: int, w: int, h: int):
        px = int(ship.px_f3) >> 3
        py = int(ship.py_f3) >> 3
        if (x <= px <= x + w) and (y <= py <= y + h):
            ship.angleLocked = True
            ship.angleLock = angle

    @staticmethod
    def gateLock(ship, gate, gateSpeed_f3):
        if ship.gateLocked:
            return

        px = int(ship.px_f3) >> 3
        py = int(ship.py_f3) >> 3
        gx, gy, gdir = gate.x, gate.y, gate.dir
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
    @staticmethod
    def loop():
        global camX, camY, area, containers

        srcGateCode, _, _, srcGateDir = myShip.gate
        dstArea, dstGateCode, totalSeconds = area.gateRouteLookup[srcGateCode]
        dstGate = dstArea.gateLookup[dstGateCode]
        _, dstGateX, dstGateY, dstGateDir = dstGate

        travelStage = 0
        stageFrames = 0

        zoomTime = 30 * 3
        turnTime = 60 * max(1, totalSeconds - 6)

        speedStart_f3 = 5 << 3
        speedTurn_f3 = 10 << 3
        speed_f3 = speedStart_f3

        startAngle = 90 * srcGateDir
        endAngle = 90 * ((dstGateDir + 2) % 4)
        rotate = endAngle - startAngle
        rotate = (rotate + 180) % 360 - 180

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
                myShip.angle = startAngle
                zoom_f6 = 64 - ((32 * stageFrames) // zoomTime)
                speed_f3 = speedStart_f3 + \
                    (((speedTurn_f3 - speedStart_f3) * stageFrames) // zoomTime)
                if stageFrames > zoomTime:
                    travelStage += 1
                    stageFrames = 0
                gateRate = 15 + ((15 * stageFrames) // zoomTime)
                fps = 30 + ((30 * stageFrames) // zoomTime)

            elif travelStage == 1:  # Stage 1 Round the corner
                myShip.angle = (startAngle + 360 +
                                ((rotate * stageFrames) // turnTime)) % 360
                zoom_f6 = 32
                speed_f3 = speedTurn_f3
                if stageFrames > turnTime:
                    travelStage += 1
                    stageFrames = 0
                gateRate = 30
                fps = 60

            elif travelStage == 2:  # Stage 2 Slow down (zoom in)
                myShip.angle = endAngle
                zoom_f6 = 32 + ((32 * stageFrames) // zoomTime)
                speed_f3 = speedTurn_f3 - \
                    (((speedTurn_f3 - speedStart_f3) * stageFrames) // zoomTime)
                if stageFrames > zoomTime:
                    travelStage += 1
                    stageFrames = 0
                gateRate = 30 - ((15 * stageFrames) // zoomTime)
                fps = 60 - ((30 * stageFrames) // zoomTime)

            setFPS(fps)

            angleRad = (myShip.angle * 3.14159) / 180.0
            myShip.vx_f3 = int(speed_f3 * math.cos(angleRad))
            myShip.vy_f3 = int(speed_f3 * math.sin(angleRad))

            myShip.moveGateTravelFrame()

            zhw, zhh = (64 * 36) // zoom_f6, (64 * 20) // zoom_f6

            if gateFrame >= gateRate:
                gateFrame = 0
            if gateFrame == 0:
                rad = math.atan2(myShip.vy_f3, myShip.vx_f3)
                dist_f3 = (zhw + 8) << 3
                gateX_f3 = int(myShip.px_f3 + dist_f3 * math.cos(rad))
                gateY_f3 = int(myShip.py_f3 + dist_f3 * math.sin(rad))
            gateX_f3 -= myShip.vx_f3
            gateY_f3 -= myShip.vy_f3
            gateFrame += 1

            camX = (myShip.px_f3 >> 3) - zhw + (myShip.vx_f3 >> 3)
            camY = (myShip.py_f3 >> 3) - zhh + (myShip.vy_f3 >> 3)

            fill(buffer, 0b00)

            Container.updateVisible(camX, camY, containers)

            SpaceBits.renderZoomed(camX, camY, zoom_f6)

            if zoom_f6 > 32:
                myShip.renderZoomed(camX, camY, zoom_f6)
                GateTravel.renderGateZoomed(
                    gateX_f3, gateY_f3, camX, camY, myShip.angle, zoom_f6)
            else:
                myShip.renderTiny(camX, camY)
                GateTravel.renderGateTiny(
                    gateX_f3, gateY_f3, camX, camY, myShip.angle)

            postShading(buffer, shader, lightAngle)
            display(buffer)
            perfStop()

            perfRender()
            update()

            if travelStage == 3:  # Exit Loop
                area = dstArea
                containers = area.containers

                myShip.apCurrentDestinationCode = None
                myShip.apCurrentPoint = None
                myShip.gateLocked = True
                myShip.gateEnter = True
                myShip.gate = dstGate
                myShip.gateDistance_f3 = (0-36) << 3
                myShip.gateSpeed_f3 = 5 << 3
                myShip.px_f3 = dstGateX << 3
                myShip.py_f3 = dstGateY << 3
                setFPS(30)
                break

    @staticmethod
    @micropython.native
    def renderGateTiny(px_f3: int, py_f3: int, camX: int, camY: int, angle: int):
        imp, iw, ih = impGateSmall
        hw = iw >> 1
        hh = ih >> 1
        x = (((px_f3 >> 3) - camX) >> 1) - hw
        y = (((py_f3 >> 3) - camY) >> 1) - hh
        blitRotate(buffer, imp, angle, x, y, iw, ih, hw, hh)

    @staticmethod
    @micropython.native
    def renderGateZoomed(px_f3: int, py_f3: int, camX: int, camY: int, angle: int, zoom_f6: int):
        imp, iw, ih = impGateV
        hw = iw >> 1
        hh = ih >> 1
        x = ((zoom_f6 * ((px_f3 >> 3) - camX)) >> 6) - hw
        y = ((zoom_f6 * ((py_f3 >> 3) - camY)) >> 6) - hh
        dir = angle // 90
        blitScale(buffer, imp, zoom_f6, x, y, iw, ih, hw, hh, dir)


area = starSystem.areaLookup["AAA"]
containers = area.containers
ships = []


def shipMedium(imp, impSm):
    return Ship(imp, impSm, sizeClass=SHIP_SIZECLASS_MEDIUM, speedMax_f3=2 << 3, accel_f3=1,
                dampening_f6=62, boost_f3=3 << 3, boostDelay=60, rotateSpeed=5)


def shipSmall(imp, impSm):
    return Ship(imp, impSm, sizeClass=SHIP_SIZECLASS_SMALL, speedMax_f3=3 << 3, accel_f3=2,
                dampening_f6=60, boost_f3=4 << 3, boostDelay=45, rotateSpeed=8)


def shipNyan(imp, impSm):
    return Ship(imp, impSm, sizeClass=SHIP_SIZECLASS_SMALL, speedMax_f3=4, accel_f3=2,
                dampening_f6=60, boost_f3=1 << 3, boostDelay=45, rotateSpeed=8)


myShip1 = shipMedium(impShip, impShipSm)
myShip2 = shipSmall(impShip2, impShip2Sm)

shipConfigs = {
    "ship2": (shipSmall, impShip2, impShip2Sm),
    "ship": (shipMedium, impShip, impShipSm),
    "skull": (shipMedium, impShipSkull, None),
    "MF": (shipMedium, impShipMF, None),
    "thumb": (shipSmall, impShipThumb, None),
    "nyan": (shipNyan, impShipNyan, None),
    "logo": (shipSmall, impLogo32, None)
}


def shipNamed(shipKey):
    sat, imp, impSm = shipConfigs[shipKey]
    return sat(imp, impSm)


myShip = myShip1
ships.append(myShip)
camLock = False
camX, camY = 92, 30
camDolly = False
camDollyX1 = 0
camDollyY1 = 0
camDollyX2 = 0
camDollyY2 = 0
camDollyTime = 0
camDollyFrame = 0
myShip.px_f3 = camX << 3
myShip.py_f3 = camY << 3
myShip.angle = 180
myShip.angleTarget = myShip.angle
lightAngle = 0
scripted = False
scriptFrame = 0
scriptIndex = 0
script = []


def scriptSpawnShip(shipList, listKey, shipKey, x, y, targetArea=None, targetDestination=None):
    ship = shipNamed(shipKey)
    ship.px_f3 = x << 3
    ship.py_f3 = y << 3
    if targetArea or targetDestination:
        ship.autopilot = True
        ship.apTargetAreaCode = targetArea
        ship.apTargetDestinationCode = targetDestination
    shipList[listKey] = ship
    ships.append(ship)


def scriptDespawnShip(shipList, listKey):
    ship = shipList.pop(listKey)
    ships.remove(ship)


def scriptCamDolly(dx, dy, speed_f3):
    global camDolly, camDollyX1, camDollyY1, camDollyX2, camDollyY2, camDollyTime, camDollyFrame
    camDolly = True
    camDollyX1 = camX
    camDollyY1 = camY
    camDollyX2 = camX + dx
    camDollyY2 = camY + dy
    distance_f3 = round(math.sqrt((dx*dx)+(dy*dy)) * 8)
    camDollyTime = (distance_f3 + speed_f3 - 1) // speed_f3
    camDollyFrame = 0


# Teaser #2: Gate Traffic
# - Wait to start sequence, when any d-pad is pressed to start
# - Start with lower right of beta gates, showing north and east paths
# - One ship goes north, next ship turns right
# - Pan slowly to show entire intersection
# - Many ships pass through intersection
camLock = True
area = starSystem.areaLookup["BBB"]
containers = area.containers
cx0, cy0 = containers[0].x1, containers[0].y1
cx1, cy1 = containers[1].x1, containers[1].y1
camX, camY = cx0-32, cy0+89
lightAngle = 6
npc = {}
script = [
    (1, scriptSpawnShip, [npc, "open1",
     "ship2", cx1+32, cy1+245, "BBB", "N1"]),
    (1, scriptSpawnShip, [npc, "eggSkull",
     "skull", cx1+24, cy1+88, "BBB", "D1"]),
    (30, scriptSpawnShip, [npc, "open2",
     "ship", cx1+32, cy1+245, "BBB", "D1"]),
    (70, scriptDespawnShip, [npc, "open1"]),
    (70, scriptSpawnShip, [npc, "pair1", "ship2", cx0+97, cy0+52, "AAA"]),
    (90, scriptCamDolly, [0, -20, 4]),
    (90, scriptSpawnShip, [npc, "pair2", "ship2", cx0+97, cy0+52, "AAA"]),
    (130, scriptCamDolly, [9, -25, 4]),
    (130, scriptSpawnShip, [npc, "eggThumb", "thumb", cx0+97, cy0+52, "GGG"]),
    (150, scriptSpawnShip, [npc, "eggMF", "MF", cx1+24, cy1+88, "BBB", "D1"]),
    (150, scriptDespawnShip, [npc, "eggSkull"]),
    (190, scriptCamDolly, [-25, -8, 4]),
    (205, scriptDespawnShip, [npc, "open2"]),
    (240, scriptDespawnShip, [npc, "pair1"]),
    (250, scriptCamDolly, [30, -80, 6]),
    (260, scriptDespawnShip, [npc, "pair2"]),
    (265, scriptDespawnShip, [npc, "eggMF"]),
    (300, scriptSpawnShip, [npc, "logo", "logo", cx0+42, cy0-27]),
    (315, scriptDespawnShip, [npc, "eggThumb"]),
    (340, scriptSpawnShip, [npc, "eggNyan",
     "nyan", cx0-56, cy0-12, "BBB", "ScriptNyan"]),
]
scripted = True

gc.collect()

while True:
    perfStart(0)

    # TODO TESTING!
    # if not myShip.autopilot:
    #     areaChoices = [a for a in starSystem.areas if a != area]
    #     myShip.apTargetAreaCode = areaChoices[random.randrange(
    #         len(areaChoices))].code
    #     myShip.autopilot = True

    if scripted:
        # while not buttonR.pressed():
        #     pass
        if scriptFrame > 0 or buttonR.justPressed():
            scriptFrame += 1
            print(scriptFrame)
        while True:
            if scriptIndex >= len(script):
                # scripted = False
                break
            frame, action, args = script[scriptIndex]
            if scriptFrame == frame:
                action(*args)
                scriptIndex += 1
                continue
            break

    if buttonA.justPressed():
        lightAngle = (lightAngle + 1) % 8
    if buttonB.justPressed() and not myShip.gateLocked:
        prevShip = myShip
        myShip = myShip2 if myShip == myShip1 else myShip1
        myShip.px_f3 = prevShip.px_f3
        myShip.py_f3 = prevShip.py_f3
        myShip.vx_f3 = prevShip.vx_f3
        myShip.vy_f3 = prevShip.vy_f3
        myShip.angle = prevShip.angle
        myShip.angleTarget = prevShip.angleTarget
        ships.remove(prevShip)
        ships.append(myShip)

    # TODO change over old tuples to the classes

    for ship in ships:
        perfStart(1)
        ship.updateContainer()
        perfStop(1)

        perfStart(2)
        ship.speedLimited = False
        ship.dirSpeedLimited = False
        if ship.chunk:
            chunk = ship.chunk
            for o in chunk.dirSlowZones:
                Zones.dirSpeedLimit(ship, 6, o.x, o.y, o.w, o.h, o.dir)
            for o in chunk.slowZones:
                Zones.speedLimit(ship, 6, o.x, o.y, o.w, o.h)
            for o in chunk.scanners:
                Zones.speedLimit(ship, 4, o.x-5, o.y-5, o.w+10, o.h+10)

            ship.angleLocked = False
            for o in chunk.docks:
                Zones.angleLock(ship, ((o.dir+1) & 0b11) *
                                90, o.x-20, o.y-10, 40, 20)
            for o in chunk.pads:
                Zones.angleLock(ship, ship.angleTarget, o.x-8, o.y-8, 16, 16)

            for o in chunk.gates:
                Zones.gateLock(ship, o, 5 << 3)
        perfStop(2)

        perfStart(3)
        if ship.autopilot:
            ship.inputAutopilot()
        elif ship == myShip:
            ship.inputButtons()
        perfStop(3)

        perfStart(4)
        ship.moveFrame()
        perfStop(4)

    if camDolly:
        camX = camDollyX1 + \
            (camDollyFrame * (camDollyX2-camDollyX1)) // camDollyTime
        camY = camDollyY1 + \
            (camDollyFrame * (camDollyY2-camDollyY1)) // camDollyTime
        camDollyFrame += 1
        if camDollyFrame > camDollyTime:
            camDolly = False
    elif not camLock:
        camX = (myShip.px_f3 >> 3) - 36 + (myShip.vx_f3 >> 3)
        camY = (myShip.py_f3 >> 3) - 20 + (myShip.vy_f3 >> 3)

    Container.updateVisible(camX, camY, containers)

    fill(buffer, 0b00)

    SpaceBits.render(camX, camY)

    for container in containers:
        if not container.visible:
            continue

        blitContainerMap(buffer, container, -camX, -camY)

        for o in container.smallTexts:
            blitText(buffer, font3x3, o.text, o.x-camX, o.y-camY, o.dir)

        for o in container.largeTexts:
            blitText(buffer, font4x4, o.text, o.x-camX, o.y-camY, o.dir)

    for ship in ships:
        ship.render(camX, camY)

    Scanner.update()
    for container in containers:
        if not container.visible:
            continue

        for o in container.scanners:
            Scanner.render(o.x-camX, o.y-camY, o.w, o.h)

        for o in container.gates:
            if o.dir & 0b1:
                imp, iw, ih = impGateH
            else:
                imp, iw, ih = impGateV
            blit(buffer, imp, o.x-camX-(iw >> 1), o.y-camY-(ih >> 1), iw, ih)
    postShading(buffer, shader, lightAngle)
    display(buffer)
    perfStop(0)

    perfRender()
    update()

    if myShip.gateLocked and not myShip.gateEnter and myShip.gateDistance_f3 > (36 << 3):
        GateTravel.loop()

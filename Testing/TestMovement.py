# - Not going for realism
# - Heavier ship => slower response
# - Feel slippery to drift tactically
# - Turning delay
# - Control cardinal directions
# - Lateral braking increased when releasing drift
# - Small ship should feel very precise and quick to circle opponents
# - Switch to faster cruise mode after heading in the same direction for a longer time

from thumbyGrayscale import display, Sprite
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

import perf

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

# Every second changes speed stage
# Release Gas -> timer starts for stage down
# (1) Gas -> Drift (keep vector and rotate)
# (2) Timeout -> Space brake (high dampening slow down)
# Stage up -> temp speed boost

speedStageMax = 2
ssSpeed = [1, 2, 4]
ssBoost = [0, 3, 5]
ssBoostTime = [0, 5, 10]
ssGasTime = [30, 60, 0]
ssIdleTime = [0, 15, 15]

camX, camY = 0, 0

px, py = 0, 0
rotation = 0

speedStageX, speedStageY = 0, 0
stageFramesX, stageFramesY = 0, 0
gasFramesX, gasFramesY = 0, 0
idleFramesX, idleFramesY = 0, 0
speedDirX, speedDirY = 0, 0


@micropython.native
def shipMoveSpeed(inputDirX: int, inputDirY: int):
    global speedStageX, stageFramesX, gasFramesX, idleFramesX, speedDirX
    global speedStageY, stageFramesY, gasFramesY, idleFramesY, speedDirY

    stageFramesX += 1
    if inputDirX and speedDirX == 0:
        speedDirX = inputDirX

    stageFramesY += 1
    if inputDirY and speedDirY == 0:
        speedDirY = inputDirY

    if inputDirX and inputDirX == speedDirX:
        gasFramesX += 1
        idleFramesX = 0
        if speedStageX < speedStageMax and gasFramesX > ssGasTime[speedStageX]:
            speedStageX += 1
            gasFramesX = 0
            stageFramesX = 0
    else:
        idleFramesX += 1
        gasFramesX = 0
        if speedStageX > 0 and idleFramesX > ssIdleTime[speedStageX]:
            speedStageX -= 1
            idleFramesX = 0
        if speedStageX == 0:
            speedDirX = 0

    if inputDirY and inputDirY == speedDirY:
        gasFramesY += 1
        idleFramesY = 0
        if speedStageY < speedStageMax and gasFramesY > ssGasTime[speedStageY]:
            speedStageY += 1
            gasFramesY = 0
            stageFramesY = 0
    else:
        idleFramesY += 1
        gasFramesY = 0
        if speedStageY > 0 and idleFramesY > ssIdleTime[speedStageY]:
            speedStageY -= 1
            idleFramesY = 0
        if speedStageY == 0:
            speedDirY = 0

    if speedDirX:
        if stageFramesX <= ssBoostTime[speedStageX]:
            vx = ssBoost[speedStageX]
        else:
            vx = ssSpeed[speedStageX]
        if speedDirX < 0:
            vx = -vx
    else:
        vx = 0

    if speedDirY:
        if stageFramesY <= ssBoostTime[speedStageY]:
            vy = ssBoost[speedStageY]
        else:
            vy = ssSpeed[speedStageY]
        if speedDirY < 0:
            vy = -vy
    else:
        vy = 0

    return vx, vy


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

    inputDirX, inputDirY = 0, 0
    if buttonR.pressed():
        rotation = 0
        inputDirX = 1
    if buttonD.pressed():
        rotation = 1
        inputDirY = 1
    if buttonL.pressed():
        rotation = 2
        inputDirX = -1
    if buttonU.pressed():
        rotation = 3
        inputDirY = -1

    display.fill(0b00)

    drawGridPoints(camX, camY)

    perf.start()
    vx, vy = shipMoveSpeed(inputDirX, inputDirY)
    perf.stop()

    px += vx
    py += vy

    camX, camY = px-36, py-20

    sprShip.x = 36 - 6 - vx
    sprShip.y = 20 - 6 - vy

    sprShip.setFrame(rotation)
    display.drawSprite(sprShip)

    display.update()

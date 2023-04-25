import random

from thumbyGrayscale import display, Sprite
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

import perf

display.setFPS(30)

# BITMAP: width: 16, height: 13 (3)
bmpShip = [bytearray([0, 0, 64, 242, 78, 92, 232, 64, 160, 160, 224, 64, 64, 0, 0, 0,
           0, 0, 0, 9, 14, 7, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0,
           0, 4, 68, 252, 232, 80, 224, 64, 160, 160, 224, 64, 64, 0, 0, 0,
           0, 4, 4, 7, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
           0, 8, 8, 248, 240, 80, 224, 64, 224, 160, 160, 64, 64, 64, 0, 0,
           0, 2, 2, 3, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
           bytearray([0, 0, 82, 84, 252, 252, 248, 176, 176, 160, 160, 64, 64, 0, 0, 0,
                      0, 0, 9, 5, 7, 7, 3, 1, 1, 0, 0, 0, 0, 0, 0, 0,
                      0, 4, 88, 88, 248, 240, 240, 176, 176, 160, 160, 64, 64, 0, 0, 0,
                      0, 4, 3, 3, 3, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 16, 88, 80, 240, 240, 240, 160, 160, 160, 0, 64, 64, 0, 0,
                      0, 0, 1, 3, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0])]

# BITMAP: width: 16, height: 13 (3)
bmpShipMask = bytearray([0, 82, 247, 255, 255, 254, 252, 248, 248, 240, 240, 224, 224, 224, 64, 0,
                         0, 9, 29, 31, 31, 15, 7, 3, 3, 1, 1, 0, 0, 0, 0, 0,
                         12, 94, 254, 254, 252, 248, 248, 248, 248, 240, 240, 224, 224, 224, 64, 0,
                         6, 15, 15, 15, 7, 3, 3, 3, 3, 1, 1, 0, 0, 0, 0, 0,
                         28, 188, 252, 252, 248, 248, 248, 248, 240, 240, 240, 224, 224, 224, 64, 64,
                         7, 7, 7, 7, 3, 3, 3, 3, 1, 1, 1, 0, 0, 0, 0, 0])

# BITMAP: width: 10, height: 24
bmpFire = bytearray([2, 5, 0, 2, 2, 2, 2, 2, 0, 0,
                     0, 0, 0, 2, 0, 0, 0, 2, 0, 2,
                     0, 0, 0, 0, 2, 0, 0, 0, 0, 2])

# BITMAP: width: 6, height: 32
bmpHit = bytearray([0, 12, 18, 26, 12, 0,
                    12, 30, 59, 63, 30, 12,
                    20, 32, 1, 32, 1, 10,
                    32, 0, 0, 0, 0, 1])

# BITMAP: width: 16, height: 40
bmpWall = [bytearray([0, 0, 0, 0, 224, 240, 240, 240, 240, 0, 0, 224, 224, 0, 0, 240,
           0, 0, 0, 0, 3, 7, 15, 31, 255, 0, 0, 255, 255, 0, 0, 255,
           0, 0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 255, 255, 60, 24, 153,
           0, 0, 0, 0, 192, 224, 240, 248, 255, 0, 0, 255, 255, 0, 0, 255,
           0, 0, 0, 0, 7, 15, 15, 15, 15, 0, 0, 7, 7, 0, 0, 15]),
           bytearray([255, 255, 7, 243, 251, 251, 251, 251, 251, 1, 252, 254, 254, 252, 1, 251,
                      255, 255, 0, 255, 63, 31, 63, 255, 255, 0, 255, 255, 255, 255, 0, 255,
                      255, 255, 0, 255, 60, 24, 60, 255, 255, 0, 255, 231, 255, 255, 126, 189,
                      255, 255, 0, 255, 252, 248, 252, 255, 255, 0, 255, 255, 255, 255, 0, 255,
                      255, 255, 240, 239, 223, 223, 223, 223, 223, 128, 63, 127, 127, 63, 128, 223])]


sprShip = Sprite(16, 13, bmpShip, 16, 20-7, -1, 0, 0)
sprShipMask = Sprite(16, 13, bmpShipMask, 36-8, 20-7, -1, 0, 0)
sprShipFire1 = Sprite(10, 3, bmpFire, sprShip.x+9, sprShip.y+2, 0b00, 0, 0)
sprShipFire2 = Sprite(10, 3, bmpFire, sprShip.x+9, sprShip.y+8, 0b00, 0, 1)
sprWallHit1 = Sprite(6, 6, bmpHit, 72-16, sprShipFire1.y+3-3, 0b00, 0, 0)
sprWallHit2 = Sprite(6, 6, bmpHit, 72-16, sprShipFire2.y+1-3, 0b00, 0, 0)

shipAnimFrame = 0
shipFiringFrame = 0
fireFrame1 = 0
fireFrame2 = 0
hitFrame1 = 0
hitFrame2 = 0
while True:

    if buttonR.pressed():
        if shipAnimFrame < 5:
            shipAnimFrame += 1
    else:
        if shipAnimFrame > 0:
            shipAnimFrame -= 1

    if buttonA.pressed():
        shipFiringFrame += 1
        trigger = shipFiringFrame % 8
        if trigger == 0:
            fireFrame1 = 3
        elif trigger == 4:
            fireFrame2 = 3
    else:
        shipFiringFrame &= 0b100

    display.fill(0b10)

    display.blit(bmpWall, 72-16, 0, 16, 40, -1, 0, 0)

    sprShip.setFrame(shipAnimFrame//2)
    sprShipMask.setFrame(shipAnimFrame//2)
    display.drawSpriteWithMask(sprShip, sprShipMask)

    if fireFrame1:
        if fireFrame1 == 2:
            hitFrame1 = 4
            sprWallHit1.x = random.randint(58, 62)
            sprWallHit1.y = random.randint(sprShipFire1.y, sprShipFire1.y+2)-3
            sprWallHit1.mirrorX = random.randint(0, 1)
            sprWallHit1.mirrorY = random.randint(0, 1)
        sprShipFire1.setFrame(3-fireFrame1)
        fireFrame1 -= 1
        display.drawSprite(sprShipFire1)

    if fireFrame2:
        if fireFrame2 == 2:
            hitFrame2 = 4
            sprWallHit2.x = random.randint(58, 62)
            sprWallHit2.y = random.randint(sprShipFire2.y, sprShipFire2.y+2)-3
            sprWallHit2.mirrorX = random.randint(0, 1)
            sprWallHit2.mirrorY = random.randint(0, 1)
        sprShipFire2.setFrame(3-fireFrame2)
        fireFrame2 -= 1
        display.drawSprite(sprShipFire2)

    if hitFrame1:
        sprWallHit1.setFrame(4-hitFrame1)
        hitFrame1 -= 1
        display.drawSprite(sprWallHit1)

    if hitFrame2:
        sprWallHit2.setFrame(4-hitFrame2)
        hitFrame2 -= 1
        display.drawSprite(sprWallHit2)

    display.update()

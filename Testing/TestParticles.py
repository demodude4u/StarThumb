# Try out a particle engine that could be used for thrusters, gates, and space bits
import array
import math
import random

from thumbyGrayscale import display
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

import perf

display.setFPS(30)

# 0 = Black
# 1 = Dark Gray
# 2 = Light Gray
# 3 = White
COLORINDEX = const((0b00, 0b10, 0b11, 0b01))

PMODE_GATE = const(0)


class ParticleSystem:
    def __init__(self, capacity, mode, posX1, posY1, posX2, posY2, velX, velY, lifetime, spawnRate, spawnCount, spawning, alphaKey):
        self.capacity = capacity
        self.particles = array.array("I", (0 for _ in range(capacity)))
        self.mode = mode
        self.posX1 = posX1
        self.posY1 = posY1
        self.posX2 = posX2
        self.posY2 = posY2
        self.velX = velX
        self.velY = velY
        self.lifetime = lifetime
        self.spawnRate = spawnRate
        self.spawnCount = spawnCount
        self.spawning = spawning
        self.alphaKey = alphaKey

        self.count = 0
        self.indexSpawn = 0
        self.indexDeath = 0
        self.nextSpawn = 0
        self.camDX = 0
        self.camDY = 0

    def reset(self):
        self.count = 0
        self.indexSpawn = self.indexDeath
        self.nextSpawn = 0

        # TODO Pre-spawn predicted particle states

    @micropython.native
    def update(self):
        pass
        particles = self.particles

        # Assuming capacity power of 2
        capacity = self.capacity
        cMask = capacity - 1

        # Simulate/Decay particles
        start = self.indexDeath
        for offset in range(self.count):
            i = (start + offset) & cMask
            p = particles[i]
            decay = (p >> 24) & 0xFF

            if decay > 1:
                px = p & 0x7F
                py = (p >> 7) & 0x7F
                vx = (p >> 14) & 0x1F
                if vx > 15:
                    vx -= 32
                vy = (p >> 19) & 0x1F
                if vy > 15:
                    vy -= 32

                if px < 72 or py < 40:
                    px = (px + vx) & 0x7F
                    py = (py + vy) & 0x7F

                decay -= 1

                particles[i] = (
                    decay << 24) | ((vy & 0x1F) << 19) | ((vx & 0x1F) << 14) | ((py & 0x7F) << 7) | (px & 0x7F)

            elif i == self.indexDeath:
                self.indexDeath = (self.indexDeath + 1) & cMask
                self.count -= 1

        # New particles
        if self.nextSpawn:
            self.nextSpawn -= 1
        if self.spawning and self.count < capacity and not self.nextSpawn:
            self.nextSpawn = self.spawnRate
            spawned = 0
            while spawned < self.spawnCount:
                # Make sure the inputs are within bit count specifications
                px = random.randint(self.posX1, self.posX2)  # 7-bit
                py = random.randint(self.posY1, self.posY2)  # 7-bit
                vx = self.velX  # 5-bit (signed)
                vy = self.velY  # 5-bit (signed)
                decay = self.lifetime
                particles[self.indexSpawn] = (
                    decay << 24) | ((vy & 0x1F) << 19) | ((vx & 0x1F) << 14) | (py << 7) | px
                self.indexSpawn = (self.indexSpawn + 1) & cMask
                self.count += 1
                spawned += 1
                if self.count == capacity:
                    break

        # Render particles
        if self.count:
            bufBW = display.buffer  # ptr8(display.buffer)
            bufGS = display.shading  # ptr8(display.shading)

            alphaKey = self.alphaKey

            for offset in range(self.count):
                i = (self.indexDeath + offset) & cMask
                p = particles[i]
                px = p & 0x7F
                py = (p >> 7) & 0x7F
                vx = (p >> 14) & 0x1F
                if vx > 15:
                    vx -= 32
                vy = (p >> 19) & 0x1F
                if vy > 15:
                    vy -= 32
                decay = (p >> 24) & 0xFF
                if px >= 0 and px < 72 and py >= 0 and py < 40:
                    # c = 0b01

                    if self.mode == PMODE_GATE:
                        c = COLORINDEX[min(
                            3, 3 - abs(2-((5 * decay) // self.lifetime)))]

                    # elif self.mode == PMODE_EXPLODE:
                    #     if not vx and not vy:
                    #         c = alphaKey
                    #     elif decay <= 1 or decay == self.lifetime:
                    #         c = 0b10  # Dark Gray
                    #     else:
                    #         c = COLORINDEX[min(
                    #             3, 1 + max(abs(vx), abs(vy)) // 2)]

                    if c == alphaKey:
                        continue
                    so = (py >> 3) * 72 + px
                    sm1 = 1 << (py & 7)
                    sm0 = 255-sm1
                    if c & 0b01:
                        bufBW[so] |= sm1
                    else:
                        bufBW[so] &= sm0
                    if c & 0b10:
                        bufGS[so] |= sm1
                    else:
                        bufGS[so] &= sm0


# BITMAP: width: 6, height: 30
bmpGate = [bytearray([6, 254, 255, 62, 6, 0,
           224, 255, 255, 63, 0, 0,
           1, 255, 255, 63, 0, 0,
           24, 15, 63, 31, 8, 0]),
           bytearray([0, 4, 62, 255, 252, 6,
                      0, 0, 63, 255, 255, 224,
                      0, 0, 63, 255, 255, 1,
                      0, 24, 31, 63, 31, 24])]

pSelect = PMODE_GATE
psDemos = [None] * 1
psDemos[PMODE_GATE] = ParticleSystem(
    64, PMODE_GATE, 36, 8, 36, 31, 1, 0, 16, 1, 2, True, 0)

gateSpeed = 0
gateX = 36
while True:

    if buttonB.justPressed():
        pSelect = (pSelect + 1) % 2
        psDemos[pSelect].reset()

    ps = psDemos[pSelect]

    if pSelect == PMODE_GATE:
        ps.camDX = 0
        if buttonU.justPressed():
            gateSpeed = min(2, gateSpeed + 1)
        if buttonD.justPressed():
            gateSpeed = max(0, gateSpeed - 1)
        if buttonL.justPressed():
            ps.camDX = -(1 << gateSpeed)
            gateX -= ps.camDX
        if buttonR.justPressed():
            ps.camDX = (1 << gateSpeed)
            gateX -= ps.camDX

        ps.velX = 1 << gateSpeed
        ps.posX1 = gateX - ps.velX * 8 - ps.velX // 2
        ps.posX2 = ps.posX1 + ps.velX
        ps.spawnCount = 1 << gateSpeed

    ps.spawning = buttonA.pressed()

    display.fill(0)
    perf.start()
    ps.update()
    perf.stop()

    if pSelect == PMODE_GATE:
        display.blit(bmpGate, gateX-3, 5, 6, 30, 0, 0, 0)

    display.update()

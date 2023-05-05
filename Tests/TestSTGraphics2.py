from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

from STGraphics import loadIMP, loadShader, fill, blit, blitRotate, postShading, display, update

import perf

buffer = bytearray(72*40)

imp, iw, ih = loadIMP("/Games/TestSTGraphics2/ShipColor.ppm",
                      "/Games/TestSTGraphics2/ShipShading.ppm")
shader = loadShader("/Games/TestSTGraphics2/Shader.ppm")

lightAngle = 0
while True:

    if buttonR.justPressed():
        lightAngle = (lightAngle + 1) % 8
    if buttonL.justPressed():
        lightAngle = (lightAngle + 7) % 8

    fill(buffer, 0b00)

    blit(buffer, imp, 36-(iw >> 1), 20-(ih >> 1), iw, ih)

    perf.start()
    postShading(buffer, shader, lightAngle)
    perf.stop()

    display(buffer)

    perf.render()

    update()

from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

from STGraphics import loadImpPPM, fill, blit, blitRotate, display, update
from STShading import loadShaderPPM, postShading

import perf

buffer = bytearray(72*40)

# imp, iw, ih = loadImpPPM("/Games/TestSTShading/ShipColor.ppm",
#                       "/Games/TestSTShading/ShipShading.ppm")

imp, iw, ih = loadImpPPM("/Games/TestSTShading/TileTestColor.ppm",
                         "/Games/TestSTShading/TileTestShading.ppm")

# imp, iw, ih = loadImpPPM("/Games/TestSTContainer/StationTilesColor.ppm",
#                               "/Games/TestSTContainer/StationTilesShading.ppm")

shader = loadShaderPPM("/Games/TestSTShading/Shader.ppm")

lightAngle = 0
shipAngle = 0
while True:

    if buttonR.justPressed():
        lightAngle = (lightAngle + 1) % 8
    if buttonL.justPressed():
        lightAngle = (lightAngle + 7) % 8

    if buttonD.justPressed():
        shipAngle = (shipAngle + 15) % 360
    if buttonU.justPressed():
        shipAngle = (shipAngle + 360-15) % 360

    # shipAngle = (shipAngle + 5) % 360

    fill(buffer, 0b00)

    blit(buffer, imp, 36-(iw >> 1), 20-(ih >> 1), iw, ih)
    # blitRotate(buffer, imp, shipAngle, 36-(iw >> 1),
    #           20-(ih >> 1), iw, ih, iw >> 1, ih >> 1)

    perf.start()
    postShading(buffer, shader, lightAngle)
    perf.stop()

    display(buffer)

    perf.render()

    update()

import perf
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

from STGraphics import loadImpPPM, fill, blit, blitRotate, display, update
from STContainer import Container, loadMapCSV, blitContainer

from STShading import loadShaderPPM, postShading
# shader = loadShaderPPM("/Games/TestSTShading/Shader.ppm")
shader = loadShaderPPM("/Games/TestSTShading/Shader2.ppm")

# import gc

buffer = bytearray(72*40)

impTiles, iw, ih = loadImpPPM("/Games/TestSTContainer/StationTilesColor.ppm",
                              "/Games/TestSTContainer/StationTilesShading.ppm")
map, mw, mh = loadMapCSV("/Games/TestSTContainer/StationMap.csv")

print(mw, mh)

con = Container(mw, mh, map, impTiles)


x, y = -mw*4+36, -mh*4+20
lightAngle = 0
shading = True
lastMem = 0
while True:

    if buttonA.justPressed():
        lightAngle = (lightAngle + 1) % 8
    if buttonB.justPressed():
        shading = not shading
        # gc.collect()

    if buttonR.pressed():
        x -= 3
    if buttonL.pressed():
        x += 3
    if buttonD.pressed():
        y -= 3
    if buttonU.pressed():
        y += 3

    fill(buffer, 0b00)

    perf.start()
    blitContainer(buffer, con, x, y)
    perf.stop()

    if shading:
        postShading(buffer, shader, lightAngle)

    display(buffer)

    perf.render()

    update()

    # mem = gc.mem_free()
    # print(mem, mem-lastMem)
    # lastMem = mem

import sys

from PackAssets import PackWriter

pack = PackWriter()

pack.cd = "../Shaded/"

pack.writeShader("Shader.png")

pack.writeSplitImage("Tiles.png")

pack.writeSplitImage("Font3x3White.png")
pack.writeSplitImage("Font4x4Black.png")

pack.writeSplitImage("GateH.png")
pack.writeSplitImage("GateV.png")

pack.writeSplitImage("GateSm.png")
pack.writeSplitImage("GateSmBlur1.png")
pack.writeSplitImage("GateSmBlur2.png")

pack.writeSplitImage("ShipSm.png")
pack.writeSplitImage("Ship.png")

pack.writeSplitImage("Ship2Sm.png")
pack.writeSplitImage("Ship2.png")

pack.cd = "../Tiled/"

pack.writeMap("Alpha Gate.tmx")
pack.writeMap("Alpha Port.tmx")
pack.writeMap("Beta Connector.tmx")
pack.writeMap("Beta Gates.tmx")
pack.writeMap("Beta Port.tmx")
pack.writeMap("Gamma Gate.tmx")
pack.writeMap("Gamma Port.tmx")

pack.writeWorld("Station Alpha.world")
pack.writeWorld("Station Beta.world")
pack.writeWorld("Station Gamma.world")

pack.writeSystem("Star System.tmx")

pack.cd = "../"

pack.save("Demo1.pack")

from TestPackWriting import PackWriter

pack = PackWriter()

pack.cd = "../Shaded/"

pack.writeShader("Shader.png")

pack.cd = "../Shaded/TestShipRoll/"

pack.writeSplitImage("ShipSkull.png")
pack.writeSplitImage("ShipSkullTop.png")

pack.cd = "../"

pack.save("TestShipRoll.pack")

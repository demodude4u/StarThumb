from machine import mem32, soft_reset
from gc import mem_free

from thumbyGraphics import display
from thumbyButton import buttonA

try:
    import emulator
    f = open("/main.py", "w")
    f.write("__import__(\"/Games/TestReset/TestReset.py\")")
    f.close()
except ImportError:
    pass

try:
    count = int(open("resettest.txt", "r").readline())
except OSError:
    count = 0

count += 1

f = open("resettest.txt", "w")
f.write(str(count))
f.close()

display.display.init_display()

display.fill(0)
display.setFont("/lib/font3x5.bin", 3, 5, 1)
display.drawText("Press A to reset!", 0, 0, 1)
display.drawText("Load Count: "+str(count), 0, 12, 1)
display.drawText("Mem Free: "+str(mem_free()), 0, 24, 1)
display.update()

while not buttonA.pressed():
    pass

display.fill(0)
display.setFont("/lib/font5x7.bin", 5, 7, 1)
display.drawText("LOADING", 16, 16, 1)
display.update()

mem32[0x4005800C] = 1
soft_reset()

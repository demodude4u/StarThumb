class Container:
    def __init__(self, columns, rows, map, impTiles):
        self.columns = columns
        self.rows = rows
        self.map = map
        self.impTiles = impTiles
        self.sprites = []
        self.slowZones = []
        self.pads = []
        self.docks = []
        self.largeTexts = []
        self.smallTexts = []
        self.scanners = []
        self.gates = []

    def initSprite(self, imp, x, y):
        self.sprites.append((imp[0], x, y, imp[1], imp[2]))

    def initSlowZone(self, x, y, w, h):
        self.slowZones.append((x, y, w, h))

    def initPad(self, x, y, dir):
        self.pads.append((x, y, dir))

    def initDock(self, x, y, dir):
        self.docks.append((x, y, dir))

    def initLargeText(self, text, x, y, dir, color):
        self.largeTexts.append((text, x, y, dir, color))

    def initSmallText(self, text, x, y, dir, color):
        self.smallTexts.append((text, x, y, dir, color))

    def initScanner(self, x, y, w, h):
        self.scanners.append((x, y, w, h))

    def initGate(self, x, y, dir):
        self.gates.append((x, y, dir))


def loadMapCSV(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
        height = len(lines)
        width = len(lines[0].split(','))
        data = []
        for line in lines:
            row = [int(cell) for cell in line.strip().split(',')]
            data.extend(row)
        return (bytearray(data), width, height)


objectDefs = {
    "SZ": lambda con, obj: con.initSlowZone(x=obj[1], y=obj[2], w=obj[3], h=obj[4]),
    "P": lambda con, obj: con.initPad(x=obj[1], y=obj[2], dir=obj[3]),
    "D": lambda con, obj: con.initDock(x=obj[1], y=obj[2], dir=obj[3]),
    "LT": lambda con, obj: con.initLargeText(text=obj[1], x=obj[2], y=obj[3], dir=obj[4], color=obj[5]),
    "ST": lambda con, obj: con.initSmallText(text=obj[1], x=obj[2], y=obj[3], dir=obj[4], color=obj[5]),
    "S": lambda con, obj: con.initScanner(x=obj[1], y=obj[2], w=obj[3], h=obj[4]),
    "G": lambda con, obj: con.initGate(x=obj[1], y=obj[2], dir=obj[3])
}


def loadObjectsCSV(container, filename):
    global objectDefs
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            obj = []
            for cell in line.strip().split(','):
                try:
                    obj.append(int(cell))
                except ValueError:
                    obj.append(cell)
            if len(obj) > 0:
                init = objectDefs.get(obj[0], None)
                if init:
                    init(container, obj)


@micropython.viper
def blitContainerMap(buffer: ptr8, container, x: int, y: int):
    columns = int(container.columns)
    rows = int(container.rows)
    map = ptr8(container.map)
    impTiles = ptr8(container.impTiles)

    w, h = (columns*8), (rows*8)

    dx1, dx2 = int(max(0, x)), int(min(72, x+w))
    dy1, dy2 = int(max(0, y)), int(min(40, y+h))

    sx1 = dx1 - x
    sx2 = sx1 + dx2 - dx1
    sy1 = dy1 - y
    sy2 = sy1 + dy2 - dy1

    # TODO reduce map and tile lookups by iterating tile by tile
    dstX = dx1
    for srcX in range(sx1, sx2):
        dstY = dy1
        c = srcX >> 3
        for srcY in range(sy1, sy2):
            r = srcY >> 3
            ti = map[r * columns + c]
            if ti == -1:
                dstY += 1
                continue
            v = impTiles[64 * ti + (srcX & 0b111) * 8 + (srcY & 0b111)]
            if v & 0b10000000:
                buffer[((dstY >> 3)*72+dstX)*8+(dstY & 0b111)] = v
            dstY += 1
        dstX += 1

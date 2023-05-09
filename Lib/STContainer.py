
TILE_SIZE = const(8)


class Container:
    def __init__(self, columns, rows, map, impTiles):
        self.columns = columns
        self.rows = rows
        self.map = map
        self.impTiles = impTiles


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


# perf 3850
@micropython.viper
def blitContainer(buffer: ptr8, container, x: int, y: int):
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

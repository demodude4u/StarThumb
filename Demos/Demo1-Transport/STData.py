import struct
from array import array


class PackReader:
    def __init__(self, filePath):
        self.filePath = filePath
        self.containerLookup = {}

    def __enter__(self):
        self.file = open(self.filePath, 'rb')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def readSection(self):
        sizeBytes = self.file.read(2)
        size = struct.unpack('H', sizeBytes)[0]

        sectionData = self.file.read(size)

        return sectionData

    def readArea(self):
        sectionData = self.readSection()
        worldData = sectionData.decode()
        worldLines = worldData.split('\n')

        name = worldLines[0]

        conData = []
        for line in worldLines[1:]:
            fields = line.split(',')
            fields = [(int(field) if field.lstrip('-').isdigit() else field)
                      for field in fields]
            conData.append(tuple(fields))

        area = Area(name)
        for cd in conData:
            cName, cx, cy, cw, ch = cd
            container = self.containerLookup[cName] if cName in self.containerLookup else None
            area.initContainer(cName, cx, cy, cw, ch, container)

        return area

    def readContainer(self, impTiles=None):
        objSectionData = self.readSection()
        objData = objSectionData.decode()
        objLines = objData.split('\n')

        name = objLines[0]

        objData = []
        for line in objLines[1:]:
            fields = line.split(',')
            fields = [(int(field) if field.lstrip('-').isdigit() else field)
                      for field in fields]
            objData.append(tuple(fields))

        csvSectionData = self.readSection()
        csvWidth, csvHeight = struct.unpack('HH', csvSectionData[:4])
        csvData = csvSectionData[4:]

        container = Container(name, csvWidth, csvHeight,
                              csvData, objData, impTiles)

        self.containerLookup[name] = container
        return container

    def loadContainers(self, count, impTiles=None):
        for _ in range(count):
            self.readContainer(impTiles)

    def readIMP(self):
        imgSectionData = self.readSection()

        imgWidth, imgHeight = struct.unpack('HH', imgSectionData[:4])
        imgBuffer = imgSectionData[4:]

        return imgBuffer, imgWidth, imgHeight

    def readShader(self):
        shaderData = self.readSection()

        shaderArray = array('H', [0] * 8)  # 8 16-bit values
        for i in range(8):
            shaderArray[i] = struct.unpack('H', shaderData[i*2:i*2+2])[0]

        return shaderArray


class Area:
    def __init__(self, name):
        self.name = name
        self.containers = []

    def initContainer(self, name, x, y, w, h, container=None):
        container.initAreaBounds(x, y, w, h)
        container.initObjectData()
        self.containers.append(container)


class Container:
    objectDefs = {
        "DSZ": lambda con, obj: con.initDirSlowZone(x=obj[1], y=obj[2], w=obj[3], h=obj[4], dir=obj[5]),
        "SZ": lambda con, obj: con.initSlowZone(x=obj[1], y=obj[2], w=obj[3], h=obj[4]),
        "P": lambda con, obj: con.initPad(x=obj[1], y=obj[2], dir=obj[3]),
        "D": lambda con, obj: con.initDock(x=obj[1], y=obj[2], dir=obj[3]),
        "LT": lambda con, obj: con.initLargeText(text=obj[1], x=obj[2], y=obj[3], dir=obj[4]),
        "ST": lambda con, obj: con.initSmallText(text=obj[1], x=obj[2], y=obj[3], dir=obj[4]),
        "S": lambda con, obj: con.initScanner(x=obj[1], y=obj[2], w=obj[3], h=obj[4]),
        "G": lambda con, obj: con.initGate(x=obj[1], y=obj[2], dir=obj[3])
    }

    def __init__(self, name, columns, rows, map, objData, impTiles=None):
        self.name = name
        self.columns = columns
        self.rows = rows
        self.map = map
        self.objData = objData
        self.impTiles = impTiles

        self.sprites = []
        self.dirSlowZones = []
        self.slowZones = []
        self.pads = []
        self.docks = []
        self.largeTexts = []
        self.smallTexts = []
        self.scanners = []
        self.gates = []

        # From area bounds
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

    def initAreaBounds(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    def initObjectData(self):
        for obj in self.objData:
            init = self.objectDefs.get(obj[0], None)
            if init:
                init(self, obj)

    def initSprite(self, imp, x, y):
        self.sprites.append((imp[0], self.x+x, self.y+y, imp[1], imp[2]))

    def initDirSlowZone(self, x, y, w, h, dir):
        self.dirSlowZones.append((self.x+x, self.y+y, w, h, dir))

    def initSlowZone(self, x, y, w, h):
        self.slowZones.append((self.x+x, self.y+y, w, h))

    def initPad(self, x, y, dir):
        self.pads.append((self.x+x, self.y+y, dir))

    def initDock(self, x, y, dir):
        self.docks.append((self.x+x, self.y+y, dir))

    def initLargeText(self, text, x, y, dir):
        self.largeTexts.append((text, self.x+x, self.y+y, dir))

    def initSmallText(self, text, x, y, dir):
        self.smallTexts.append((text, self.x+x, self.y+y, dir))

    def initScanner(self, x, y, w, h):
        self.scanners.append((self.x+x, self.y+y, w, h))

    def initGate(self, x, y, dir):
        self.gates.append((self.x+x, self.y+y, dir))


# def loadMapCSV(filename):
#     with open(filename, 'r') as f:
#         lines = f.readlines()
#         height = len(lines)
#         width = len(lines[0].split(','))
#         data = []
#         for line in lines:
#             row = [int(cell) for cell in line.strip().split(',')]
#             data.extend(row)
#         return (bytearray(data), width, height)


# def loadObjectsCSV(container, filename):
#     global objectDefs
#     with open(filename, 'r') as f:
#         lines = f.readlines()
#         objData = []
#         for line in lines:
#             obj = []
#             for cell in line.strip().split(','):
#                 try:
#                     obj.append(int(cell))
#                 except ValueError:
#                     obj.append(cell)
#             if len(obj) > 0:
#                 objData.append(obj)

#         initObjectData(container, objData)

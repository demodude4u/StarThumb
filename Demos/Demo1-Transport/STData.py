import struct
from array import array
import gc


class PackReader:
    def __init__(self, filePath):
        self.filePath = filePath
        self.areaLookup = {}
        self.containerLookup = {}

    def __enter__(self):
        self.file = open(self.filePath, 'rb')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def readSection(self):
        gc.collect()
        print("Free", gc.mem_free())

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
            area.initContainer(cx, cy, cw, ch, container)

        self.areaLookup[name] = area
        return area

    def loadAreas(self, count):
        for _ in range(count):
            self.readArea()

    def readContainer(self, impTiles):
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

    def loadContainers(self, count, impTiles):
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

    def readSystem(self):
        areaSectionData = self.readSection()
        areaData = areaSectionData.decode()
        areaLines = areaData.split('\n')
        areaData = []
        for line in areaLines:
            fields = line.split(',')
            fields = [(int(field) if field.lstrip('-').isdigit() else field)
                      for field in fields]
            areaData.append(tuple(fields))

        routeSectionData = self.readSection()
        routeData = routeSectionData.decode()
        routeLines = routeData.split('\n')
        routeData = []
        for line in routeLines:
            fields = line.split(',')
            fields = [(int(field) if field.lstrip('-').isdigit() else field)
                      for field in fields]
            routeData.append(tuple(fields))

        system = System()

        for routeID, name, x, y in areaData:
            area = self.areaLookup[name]
            system.initArea(routeID, x, y, area)

        for srcAreaRouteID, srcGate, dstAreaRouteID, dstGate, time in routeData:
            srcArea = system.areas[srcAreaRouteID]
            dstArea = system.areas[dstAreaRouteID]
            system.initRoute(srcArea, srcGate, dstArea, dstGate, time)

        return system


class System:
    def __init__(self):
        self.areas = {}

    def initArea(self, routeID, x, y, area):
        area.initSystemCoords(x, y)
        self.areas[routeID] = area

    def initRoute(self, srcArea, srcGate, dstArea, dstGate, time):
        srcArea.initRoute(srcGate, dstArea, dstGate, time)


class Area:
    def __init__(self, name):
        self.name = name
        self.containers = []
        self.routes = {}
        self.gateLookup = {}

        # from system coords
        self.x = 0
        self.y = 0

    def initSystemCoords(self, x, y):
        self.x = x
        self.y = y

    def initContainer(self, x, y, w, h, container):
        container.initAreaBounds(x, y, w, h)
        container.initObjectData()
        for gate in container.gates:
            id, _, _, _ = gate
            self.gateLookup[id] = gate
        self.containers.append(container)

    def initRoute(self, srcGate, dstArea, dstGate, time):
        self.routes[srcGate] = (dstArea, dstGate, time)


class Container:
    objectDefs = {
        "DSZ": lambda con, obj: con.initDirSlowZone(x=obj[1], y=obj[2], w=obj[3], h=obj[4], dir=obj[5]),
        "SZ": lambda con, obj: con.initSlowZone(x=obj[1], y=obj[2], w=obj[3], h=obj[4]),
        "P": lambda con, obj: con.initPad(x=obj[1], y=obj[2], dir=obj[3]),
        "D": lambda con, obj: con.initDock(x=obj[1], y=obj[2], dir=obj[3]),
        "LT": lambda con, obj: con.initLargeText(text=obj[1], x=obj[2], y=obj[3], dir=obj[4]),
        "ST": lambda con, obj: con.initSmallText(text=obj[1], x=obj[2], y=obj[3], dir=obj[4]),
        "S": lambda con, obj: con.initScanner(x=obj[1], y=obj[2], w=obj[3], h=obj[4]),
        "G": lambda con, obj: con.initGate(id=obj[1], x=obj[2], y=obj[3], dir=obj[4])
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

    def initGate(self, id, x, y, dir):
        gate = (id, self.x+x, self.y+y, dir)
        self.gates.append(gate)


class Font:
    def __init__(self, charW, charH, imp):
        self.charW = charW
        self.charH = charH
        self.span = imp[1]
        self.imp = imp[0]

import struct
from array import array
import gc
import builtins
from collections import deque


class PackReader:
    def __init__(self, filePath):
        self.filePath = filePath
        self.areaLookup = {}
        self.containerLookup = {}
        self.file = None

    def __enter__(self):
        self.file = open(self.filePath, 'rb')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def readSection(self):
        gc.collect()
        # print("Free",gc.mem_free())

        sizeBytes = self.file.read(2)
        size = struct.unpack('H', sizeBytes)[0]

        sectionData = self.file.read(size)

        return sectionData

    def readArea(self):
        sectionData = self.readSection()
        worldData = sectionData.decode()
        worldLines = worldData.split('\n')

        key = worldLines[0]

        conData = []
        for line in worldLines[1:]:
            fields = line.split(',')
            fields = [(int(field) if field.lstrip('-').isdigit() else field)
                      for field in fields]
            conData.append(tuple(fields))

        area = Area(key)
        for cd in conData:
            cName, cx, cy, cw, ch = cd
            container = self.containerLookup[cName] if cName in self.containerLookup else None
            area.initContainer(cx, cy, cw, ch, container)

        area.buildNavGraph()

        self.areaLookup[key] = area
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
        imgSize = imgWidth * (8 * ((imgHeight + 7) // 8))
        imgBuffer = imgSectionData[4:4+imgSize]

        return imgBuffer, imgWidth, imgHeight

    def readIMPFrames(self):
        imgSectionData = self.readSection()

        imgWidth, imgHeight, frameCount = struct.unpack(
            'HHB', imgSectionData[:5])
        imgSize = imgWidth * (8 * ((imgHeight + 7) // 8))
        imgBuffers = []
        o1 = 5
        o2 = o1 + imgSize
        for _ in range(frameCount):
            imgBuffers.append(imgSectionData[o1:o2])
            o1 = o2
            o2 += imgSize

        return imgBuffers, imgWidth, imgHeight, frameCount

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

        for label, key, code, x, y in areaData:
            area = self.areaLookup[key]
            system.initArea(label, code, x, y, area)

        for srcAreaCode, srcGateCode, dstAreaCode, dstGateCode, time in routeData:
            srcArea = system.areaLookup[srcAreaCode]
            dstArea = system.areaLookup[dstAreaCode]
            system.initRoute(srcArea, srcGateCode, dstArea, dstGateCode, time)

        system.buildGateDestinations()

        return system


class System:
    def __init__(self):
        self.areaLookup = {}
        self.areas = []

    def initArea(self, label, code, x, y, area):
        area.initFromSystem(label, code, x, y)
        self.areaLookup[code] = area
        self.areas.append(area)

    def initRoute(self, srcArea, srcGateCode, dstArea, dstGateCode, time):
        srcArea.initGateRoute(srcGateCode, dstArea, dstGateCode, time)

    def buildGateDestinations(self):
        search = deque((), 64)
        for area in self.areas:
            # print("Building Gate Destinations For", area.code)
            search.append((area, 0))
            while len(search) > 0:
                searchArea, totalTime = search.popleft()
                # print(searchArea.code, totalTime)
                for _, prevArea, prevGateCode,  time in searchArea.gateReverseRoutes:
                    prevTotalTime = totalTime + time
                    # print("\t", prevGateCode, prevArea.code, prevTotalTime)
                    if prevArea != area and prevArea.initGateDestination(prevGateCode, area, prevTotalTime):
                        # print("\t\t***")
                        search.append((prevArea, prevTotalTime))


NODE_TYPE_BASIC = const(0)
NODE_TYPE_PAD = const(1)
NODE_TYPE_DOCK = const(2)
NODE_TYPE_GATE = const(3)


class NavPoint:
    def __init__(self, x, y, nodeType, obj):
        self.x = x
        self.y = y
        self.nodeType = nodeType
        self.obj = obj

        self.paths = []
        self.reversePaths = []
        self.destinations = {}

    def initPath(self, navPoint, distance):
        self.paths.append((navPoint, distance))
        navPoint.reversePaths.append((self, distance))

    def initDestination(self, code, navPoint, distance) -> bool:
        if code in self.destinations:
            _, prevDistance = self.destinations[code]
            if distance >= prevDistance:
                return False
        self.destinations[code] = (navPoint, distance)
        return True


class Area:
    def __init__(self, key):
        self.key = key

        self.containers = []

        self.gateLookup = {}
        self.gateRouteLookup = {}
        self.gateRoutes = []
        self.gateReverseRoutes = []
        self.gateDestinations = {}

        self.navPoints = []

        # from system ID
        self.label = None
        self.code = None
        self.x = 0
        self.y = 0

    def initFromSystem(self, label, code, x, y):
        self.label = label
        self.code = code
        self.x = x
        self.y = y

    def initContainer(self, x, y, w, h, container):
        container.initAreaBounds(x, y, w, h)
        container.initObjectData()
        container.buildChunks()
        for gate in container.gates:
            self.gateLookup[gate.code] = gate
        self.containers.append(container)

    def initGateRoute(self, srcGateCode, dstArea, dstGateCode, time):
        self.gateRouteLookup[srcGateCode] = (dstArea, dstGateCode, time)
        self.gateRoutes.append((srcGateCode, dstArea, dstGateCode, time))
        dstArea.gateReverseRoutes.append(
            (dstGateCode, self, srcGateCode, time))

    def initGateDestination(self, gateCode, area, time) -> bool:
        code = area.code
        if code in self.gateDestinations:
            _, _, prevTime = self.gateDestinations[code]
            if time >= prevTime:
                return False
        self.gateDestinations[code] = (gateCode, area, time)
        return True

    def buildNavGraph(self):
        # Initialize Points
        coordPoints = {}
        navPoints = {}
        for container in self.containers:
            cid = builtins.id(container)
            for n in container.navs:
                coord = (n.x, n.y)
                if coord in coordPoints:
                    navPoint = coordPoints[coord]
                else:
                    navPoint = NavPoint(n.x, n.y, n.nodeType, n.obj)
                    coordPoints[coord] = navPoint
                    self.navPoints.append(navPoint)
                navPoints[(cid, n.id)] = navPoint

        # Initialize Paths
        for container in self.containers:
            cid = builtins.id(container)
            for n in container.navs:
                navPoint = navPoints[(cid, n.id)]
                for nav in n.navs:
                    pathPoint = navPoints[(cid, nav)]
                    distance = abs(navPoint.x-pathPoint.x) + \
                        abs(navPoint.y-pathPoint.y)
                    navPoint.initPath(pathPoint, distance)

        # Initialize Destinations
        search = deque((), 64)
        for container in self.containers:
            cid = builtins.id(container)
            for n in container.navs:
                if n.nodeType == NODE_TYPE_BASIC:
                    continue
                navPoint = navPoints[(cid, n.id)]
                code = n.obj.code
                search.append((navPoint, 0))
                while len(search) > 0:
                    searchPoint, totalDistance = search.popleft()
                    for prevPoint, distance in searchPoint.reversePaths:
                        prevTotalDistance = totalDistance + distance
                        if prevPoint.initDestination(code, searchPoint, prevTotalDistance):
                            search.append((prevPoint, prevTotalDistance))


objectDefs = {
    "DSZ": lambda con, obj: con.initDirSlowZone(id=obj[1], x=obj[2], y=obj[3], w=obj[4], h=obj[5], dir=obj[6]),
    "SZ": lambda con, obj: con.initSlowZone(id=obj[1], x=obj[2], y=obj[3], w=obj[4], h=obj[5]),
    "P": lambda con, obj: con.initPad(id=obj[1], x=obj[2], y=obj[3], code=obj[4], dir=obj[5], nav=[obj[6]]),
    "D": lambda con, obj: con.initDock(id=obj[1], x=obj[2], y=obj[3], code=obj[4], dir=obj[5], nav=[obj[6]]),
    "LT": lambda con, obj: con.initLargeText(id=obj[1], x=obj[2], y=obj[3], text=obj[4], dir=obj[5]),
    "ST": lambda con, obj: con.initSmallText(id=obj[1], x=obj[2], y=obj[3], text=obj[4], dir=obj[5]),
    "S": lambda con, obj: con.initScanner(id=obj[1], x=obj[2], y=obj[3], w=obj[4], h=obj[5]),
    "G": lambda con, obj: con.initGate(id=obj[1], x=obj[2], y=obj[3], code=obj[4], dir=obj[5], nav=[obj[6]]),
    "N": lambda con, obj: con.initNav(id=obj[1], x=obj[2], y=obj[3], navs=[obj[4], obj[5], obj[6]], nodeType=NODE_TYPE_BASIC),
}


class Container:
    def __init__(self, name, columns, rows, map, objData, impTiles=None):
        self.name = name
        self.columns = columns
        self.rows = rows
        self.map = map
        self.objData = objData
        self.impTiles = impTiles

        self.dirSlowZones = []
        self.slowZones = []
        self.pads = []
        self.docks = []
        self.largeTexts = []
        self.smallTexts = []
        self.scanners = []
        self.gates = []
        self.navs = []
        self.navsLookup = {}

        # From build chunks
        self.chunks = None
        self.chunkColumns = 0
        self.chunkRows = 0

        # From area bounds
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0

        self.visible = False

    def initAreaBounds(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def initObjectData(self):
        for obj in self.objData:
            init = objectDefs.get(obj[0], None)
            if init:
                init(self, obj)

    class DirZone:
        def __init__(self, x, y, w, h, dir):
            self.x = x
            self.y = y
            self.w = w
            self.h = h
            self.dir = dir

    def initDirSlowZone(self, id, x, y, w, h, dir):
        self.dirSlowZones.append(self.DirZone(self.x1+x, self.y1+y, w, h, dir))

    def initSlowZone(self, id, x, y, w, h):
        self.slowZones.append(self.DirZone(
            self.x1+x, self.y1+y, w, h, dir=None))

    def initScanner(self, id, x, y, w, h):
        self.scanners.append(self.DirZone(
            self.x1+x, self.y1+y, w, h, dir=None))

    # TODO combine with NavPoint somehow
    class Nav:
        def __init__(self, id, x, y, navs, nodeType, obj):
            self.id = id
            self.x = x
            self.y = y
            self.navs = navs
            self.nodeType = nodeType
            self.obj = obj

    def initNav(self, id, x, y, navs, nodeType, obj=None):
        navs = [n for n in navs if n > 0]
        nav = self.Nav(id, self.x1+x, self.y1+y, navs, nodeType, obj)
        self.navs.append(nav)
        self.navsLookup[id] = nav

    class CodePoint:
        def __init__(self, code, x, y, dir):
            self.code = code
            self.x = x
            self.y = y
            self.dir = dir

    def initPad(self, id, x, y, code, dir, nav):
        pad = self.CodePoint(code, self.x1+x, self.y1+y, dir)
        self.pads.append(pad)
        self.initNav(id, x, y, nav, NODE_TYPE_PAD, pad)

    def initDock(self, id, x, y, code, dir, nav):
        dock = self.CodePoint(code, self.x1+x, self.y1+y, dir)
        self.docks.append(dock)
        self.initNav(id, x, y, nav, NODE_TYPE_DOCK, dock)

    def initGate(self, id, x, y, code, dir, nav):
        gate = self.CodePoint(code, self.x1+x, self.y1+y, dir)
        self.gates.append(gate)
        self.initNav(id, x, y, nav, NODE_TYPE_GATE, gate)

    class DisplayText:
        def __init__(self, text, x, y, dir):
            self.text = text
            self.x = x
            self.y = y
            self.dir = dir

    def initLargeText(self, id, x, y, text, dir):
        self.largeTexts.append(self.DisplayText(
            text, self.x1+x, self.y1+y, dir))

    def initSmallText(self, id, x, y, text, dir):
        self.smallTexts.append(self.DisplayText(
            text, self.x1+x, self.y1+y, dir))

    def buildChunks(self):
        self.chunkColumns = (self.x2-self.x1+63) >> 6
        self.chunkRows = (self.y2-self.y1+63) >> 6

        # TODO instead determine chunk ranges from object bounds to load faster
        self.chunks = [None] * (self.chunkColumns * self.chunkRows)

        def addChunkObjects(containerList, chunkList, chunkBounds, objectBoundsFunc):
            cx1, cy1, cx2, cy2 = chunkBounds
            objCount = 0
            for o in containerList:
                ox1, oy1, ox2, oy2 = objectBoundsFunc(o)
                if ox2 <= cx1 or oy2 <= cy1 or ox1 >= cx2 or oy1 >= cy2:
                    continue
                chunkList.append(o)
                objCount += 1
            return objCount

        def convert(x, y, w, h):
            return (x-self.x1, y-self.y1, x+w, y+h)

        def convertGate(x, y, dir):
            if dir == 0:
                x, y, w, h = x, y - 16, 8, 32
            elif dir == 1:
                x, y, w, h = x - 16, y, 32, 8
            elif dir == 2:
                x, y, w, h = x - 8, y - 16, 8, 32
            else:
                x, y, w, h = x - 16, y - 8, 32, 8
            return convert(x, y, w, h)

        for cx in range(self.chunkColumns):
            for cy in range(self.chunkRows):
                chunk = ContainerChunk()
                cx1, cy1 = cx*64, cy*64
                cx2, cy2 = cx1+64, cy1+64
                chunkBounds = (cx1, cy1, cx2, cy2)
                objCount = 0
                objCount += addChunkObjects(self.dirSlowZones, chunk.dirSlowZones,
                                            chunkBounds, lambda o: convert(o.x, o.y, o.w, o.h))
                objCount += addChunkObjects(self.slowZones, chunk.slowZones,
                                            chunkBounds, lambda o: convert(o.x, o.y, o.w, o.h))
                objCount += addChunkObjects(self.pads, chunk.pads, chunkBounds,
                                            lambda o: convert(o.x-8, o.y-8, 16, 16))
                objCount += addChunkObjects(self.docks, chunk.docks, chunkBounds,
                                            lambda o: convert(o.x-20, o.y-10, 40, 20))
                objCount += addChunkObjects(self.scanners, chunk.scanners, chunkBounds,
                                            lambda o: convert(o.x-5, o.y-5, o.w+10, o.h+10))
                objCount += addChunkObjects(self.gates, chunk.gates, chunkBounds,
                                            lambda o: convertGate(o.x, o.y, o.dir))
                if not objCount:
                    chunk = None
                self.chunks[cy*self.chunkColumns+cx] = chunk

    @staticmethod
    @micropython.native
    def updateVisible(camX: int, camY: int, containers):
        camX2 = camX + 72
        camY2 = camY + 40
        for container in containers:
            cx1 = container.x1
            cy1 = container.y1
            cx2 = container.x2
            cy2 = container.y2
            if camX >= cx2 or camX2 <= cx1 or camY >= cy2 or camY2 <= cy1:
                container.visible = False
            else:
                container.visible = True


class ContainerChunk:
    def __init__(self):
        self.dirSlowZones = []
        self.slowZones = []
        self.pads = []
        self.docks = []
        self.scanners = []
        self.gates = []


class Font:
    def __init__(self, charW, charH, imp):
        self.charW = charW
        self.charH = charH
        self.span = imp[1]
        self.imp = imp[0]

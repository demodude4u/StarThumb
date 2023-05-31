import xml.etree.ElementTree as ET
import json
import struct
from PIL import Image
from array import array


class PackWriter:
    OBJ_KEY_ORDER = {
        "DSZ": ["name", "x", "y", "width", "height", "Facing"],
        "SZ": ["name", "x", "y", "width", "height"],
        "P": ["name", "x", "y", "Facing"],
        "D": ["name", "x", "y", "Facing"],
        "LT": ["name", "text", "x", "y", "rotation"],
        "ST": ["name", "text", "x", "y", "rotation"],
        "S": ["name", "x", "y", "width", "height"],
        "G": ["name", "ID", "x", "y", "Facing"],
    }
    IMG_COLOR_CONVERT = {
        0x4040da: 0b11101000,
        0x8025da: 0b11110000,
        0xc040da: 0b11111000,
        0x2580da: 0b11100000,
        0x8080ff: 0b10000000,
        0xda80da: 0b11000000,
        0x40c0da: 0b11011000,
        0x80dada: 0b11010000,
        0xc0c0da: 0b11001000,
        0x1e1e74: 0b11101100,
        0x420f74: 0b11110100,
        0x661e74: 0b11111100,
        0x0f4274: 0b11100100,
        0x424289: 0b10000100,
        0x744274: 0b11000100,
        0x1e6674: 0b11011100,
        0x427474: 0b11010100,
        0x666674: 0b11001100,
        0xffffff: 0b10000001,
        0xa2a2a2: 0b10000011,
        0x4e4e4e: 0b10000010,
        0x000000: 0b10000000,
        0x008000: 0b00000000
    }

    def __init__(self):
        self.data = b''
        self.cd = ""

    def writeSection(self, data):
        size = len(data)
        sizeBytes = struct.pack('H', size)
        self.data += sizeBytes + data
        print("\t", size, " bytes")

    def writeSystem(self, filePath):
        print("SS", filePath)
        tree = ET.parse(self.cd+filePath)
        root = tree.getroot()

        # Extract Object data
        locations = []
        routes = []
        for obj in root.findall("./objectgroup[@id='2']/object"):
            objDict = obj.attrib

            # Get location name, World file, and coordinates
            locations.append([
                objDict['name'],
                obj.find(
                    "./properties/property[@name='World']").attrib['value'],
                int(objDict['x']),
                int(objDict['y'])
            ])

            # Check all properties for Gate properties
            for prop in obj.findall("./properties/property"):
                if 'Gate' in prop.attrib['name']:
                    # Get suffix after 'Gate'
                    gateName = prop.attrib['name'][4:]
                    destObjId = prop.find(
                        "./properties/property[@name='Destination']").attrib['value']
                    arrival = prop.find(
                        "./properties/property[@name='Arrival']").attrib['value']
                    duration = int(
                        prop.find("./properties/property[@name='Duration']").attrib['value'])

                    # Find destination object's name
                    destName = root.find(
                        f"./objectgroup[@id='2']/object[@id='{destObjId}']").attrib['name']

                    routes.append([
                        objDict['name'],
                        gateName,
                        destName,
                        arrival,
                        duration
                    ])

        locationsBytes = '\n'.join([','.join(map(str, line))
                                   for line in locations]).encode()
        self.writeSection(locationsBytes)

        routesBytes = '\n'.join([','.join(map(str, line))
                                 for line in routes]).encode()
        self.writeSection(routesBytes)

    def writeWorld(self, filePath):
        with open(self.cd+filePath, 'r') as file:
            print("W", filePath)
            data = json.load(file)  # .world file
            maps = [[filePath]]
            for m in data.get('maps', []):
                maps.append([m['fileName'], m['x'], m['y'],
                            m['width'], m['height']])
            worldBytes = '\n'.join([','.join(map(str, m))
                                    for m in maps]).encode()
            self.writeSection(worldBytes)

    def writeMap(self, filePath):
        print("M", filePath)
        tree = ET.parse(self.cd+filePath)  # .tmx file
        root = tree.getroot()

        objData = [[filePath]]
        for obj in root.findall("./objectgroup[@id='2']/object"):
            objDict = obj.attrib
            properties = obj.find('properties')
            if properties is not None:
                for prop in properties.findall('property'):
                    objDict[prop.attrib['name']] = prop.attrib['value']
            textElement = obj.find('text')
            if textElement is not None:
                objDict['text'] = textElement.text
            if "name" in objDict and objDict["name"] in self.OBJ_KEY_ORDER:
                objValues = []
                for key in self.OBJ_KEY_ORDER[objDict["name"]]:
                    if key in objDict:
                        try:
                            objValues.append(int(objDict[key]))
                        except ValueError:
                            objValues.append(objDict[key])
                    else:
                        objValues.append(0)
                objData.append(objValues)
        objBytes = '\n'.join([','.join(map(
            str, obj)) for obj in objData]).encode()
        self.writeSection(objBytes)

        csvLayer = root.find("./layer[@id='1']/data")
        csvData = bytearray([((int(cell)-1) & 0xFF) for row in csvLayer.text.split(
            "\n") if row for cell in row.split(",") if cell])
        csvWidth = int(root.find("./layer[@id='1']").attrib['width'])
        csvHeight = int(root.find("./layer[@id='1']").attrib['height'])
        csvBytes = struct.pack('HH', csvWidth, csvHeight)
        csvBytes += csvData
        self.writeSection(csvBytes)

    def writeImage(self, filePath):
        print("I", filePath)
        image = Image.open(self.cd+filePath).convert("RGB")

        paddedHeight = 8 * ((image.height + 7) // 8)
        buffer = bytearray(image.width * paddedHeight)

        pixels = image.getdata()
        si = 0
        for y in range(image.height):
            for x in range(image.width):
                pixel = pixels[si]
                rgb = pixel[0] << 16 | pixel[1] << 8 | pixel[2]
                try:
                    v = self.IMG_COLOR_CONVERT[rgb]
                except KeyError:
                    raise ValueError(
                        "Unknown color encountered: {:#06x}".format(rgb))
                buffer[((y >> 3)*image.width+x)*8+(y & 0b111)] = v
                si += 1
        self.writeSection(struct.pack(
            'HH', image.width, image.height) + buffer)

    def writeSplitImage(self, filePath):
        print("SI", filePath)
        image = Image.open(self.cd+filePath).convert("RGB")

        height = image.height // 2
        paddedHeight = 8 * ((height + 7) // 8)
        buffer = bytearray(image.width * paddedHeight)

        pixels = image.getdata()
        si1 = 0
        si2 = image.width * height
        for y in range(height):
            for x in range(image.width):
                v = 0
                for si in [si1, si2]:
                    pixel = pixels[si]
                    rgb = pixel[0] << 16 | pixel[1] << 8 | pixel[2]
                    try:
                        v |= self.IMG_COLOR_CONVERT[rgb]
                    except KeyError:
                        raise ValueError(
                            "Unknown color encountered: {:#06x}".format(rgb))
                buffer[((y >> 3)*image.width+x)*8+(y & 0b111)] = v
                si1 += 1
                si2 += 1
        self.writeSection(struct.pack(
            'HH', image.width, height) + buffer)

    def writeShader(self, filePath):
        print("S", filePath)
        image = Image.open(self.cd+filePath).convert("RGB")

        if image.width != 5 or image.height != 8:
            raise ValueError("Invalid shader image dimensions")

        colorData = bytearray(5*8)
        pixels = image.getdata()
        si = 0
        for y in range(image.height):
            for x in range(image.width):
                pixel = pixels[si]
                rgb = pixel[0] << 16 | pixel[1] << 8 | pixel[2]
                try:
                    v = self.IMG_COLOR_CONVERT[rgb]
                except KeyError:
                    raise ValueError(
                        "Unknown color encountered: {:#06x}".format(rgb))
                colorData[si] = v & 0b11
                si += 1

        shaderArray = array('H', [0] * 8)  # 8 16-bit values
        row_map = [3, 0, 2, 1, 7, 4, 6, 5]
        column_map = [0, 1, 2, 3, 4, 3, 2, 1]
        for sy in range(8):
            shader_value = 0
            cy = row_map[sy]
            for sx in range(8):
                cx = column_map[sx]
                color = colorData[cy*5+cx]
                shader_value |= color << (2 * sx)
            shaderArray[sy] = shader_value

        shaderData = b''
        for v in shaderArray:
            shaderData += struct.pack("H", v)

        self.writeSection(shaderData)

    def save(self, filePath):
        with open(self.cd+filePath, 'wb') as file:
            file.write(self.data)
        print("Saved", filePath)

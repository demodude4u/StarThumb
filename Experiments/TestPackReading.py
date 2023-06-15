import struct
from array import array
import gc


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

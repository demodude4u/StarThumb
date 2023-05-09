from array import array


def _readPPMHeader(file):
    if file.readline().rstrip() != b'P6':
        raise ValueError("Invalid PPM format")
    ret = []
    while True:
        line = file.readline().lstrip()
        if not line.startswith(b'#'):
            for s in line.rstrip().split():
                ret.append(int(s))
            if len(ret) >= 3:
                return ret[0], ret[1], ret[2]


def loadShaderPPM(shader_filename):
    # ppm binary file format

    color_map = {0: 0, 255: 1, 162: 3, 78: 2}
    row_map = [3, 0, 2, 1, 7, 4, 6, 5]
    column_map = [0, 1, 2, 3, 4, 3, 2, 1]

    with open(shader_filename, 'rb') as shader_file:
        width, height = _readPPMHeader(shader_file)[:2]

        if width != 5 or height != 8:
            raise ValueError("Invalid shader image dimensions")

        colorData = bytearray(5*8)
        for i in range(5*8):
            cr, cg, cb = shader_file.read(3)
            colorData[i] = color_map.get(cg, 0)

        shader_array = array('H', [0] * 8)  # 8 16-bit values
        for sy in range(8):
            shader_value = 0
            cy = row_map[sy]
            for sx in range(8):
                cx = column_map[sx]
                color = colorData[cy*5+cx]
                shader_value |= color << (2 * sx)
            shader_array[sy] = shader_value

    return shader_array


@micropython.viper
def postShading(buffer: ptr8, shader: ptr16, light: int):
    width = 72
    height = 40

    pixel_count = width * height

    df = True
    for i in range(pixel_count):
        pixel = buffer[i]

        if not (pixel & 0b10000000):  # Transparent
            continue

        if not (pixel & 0b01000000):  # Flat
            continue

        shading_rule = shader[pixel & 0b111]
        normal = (pixel >> 3) & 0b111

        shading_color = (shading_rule >> (
            2 * ((light - normal + 8) & 0b111))) & 0x03

        if df and (pixel & 0b111 == 0b011) and (normal == 0):
            df = False

        buffer[i] = (pixel & 0b11111100) | shading_color

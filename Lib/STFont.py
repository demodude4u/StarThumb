from STGraphics import loadImpPPM


class Font:
    def __init__(self, w, h, span, imp):
        self.w = w
        self.h = h
        self.span = span
        self.imp = imp


def loadFontPPM(w, h, color_filename, shading_filename=None):
    imp, iw, _ = loadImpPPM(color_filename, shading_filename)
    return Font(w, h, iw, imp)


@micropython.viper
def blitText(buffer: ptr8, font, text, x: int, y: int, vertical=False):
    cw = int(font.w)
    ch = int(font.h)
    span = int(font.span)
    imp = ptr8(font.imp)

    count = int(len(text))

    if vertical:
        dx, dy = 0, ch + 1
        w, h = cw, dy * count - 1
    else:
        dx, dy = cw + 1, 0
        w, h = dx * count - 1, ch

    if x > 71 or x+w < 0 or y > 39 or y+h < 0:
        return

    # TODO this is slow
    cx, cy = x, y
    for ti in range(count):
        fi = int(ord(text[ti])) - 65
        fx = (fi * cw) % span
        fy = ch * ((fi * cw) // span)
        for py in range(cw):
            for px in range(ch):
                srcX = fx + px
                srcY = fy + py
                v = imp[((srcY >> 3)*span+srcX)*8+(srcY & 0b111)]
                if not (v & 0b10000000):
                    continue
                dstX = cx + px
                dstY = cy + py
                if 0 <= dstX < 72 and 0 <= dstY < 40:
                    buffer[((dstY >> 3)*72+dstX)*8+(dstY & 0b111)] = v
        cx += dx
        cy += dy

import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import java.util.List;

public class AssetCompiler {
    public static void main(String[] args) {
        File containersFolder = new File("Containers");
        File fragmentsFolder = new File("Fragments");
        File tilesFolder = new File("Tiles");
        File spritesFolder = new File("Sprites");

    }
}

class ContainerAsset {
    class ContainerLink {
        int id;
    }

    class FragmentLink {
        int id;
        int row;
        int column;
        boolean mirrorX;
        boolean mirrorY;
    }

    List<ContainerLink> edges;
    List<FragmentLink> fragments;
    int rows;
    int columns;

    public void serialize(DataOutputStream dos) throws IOException {
        if (columns > 0b11111111) {
            throw new IOException("Container Columns too big!");
        }
        dos.writeByte(columns);

        if (rows > 0b11111111) {
            throw new IOException("Container Rows too big!");
        }
        dos.writeByte(rows);

        if (edges.size() > 0b11111111) {
            throw new IOException("Edge Count too big!");
        }
        dos.writeByte(edges.size());

        for (ContainerLink edge : edges) {
            if (edge.id > 0b1111111111) {
                throw new IOException("Edge ID too big!");
            }
            dos.writeShort(edge.id);
        }

        if (fragments.size() > 0b11111111) {
            throw new IOException("Fragment Count too big!");
        }
        dos.writeByte(edges.size());

        for (FragmentLink fragment : fragments) {
            if (fragment.id > 0b1111111111) {
                throw new IOException("Fragment ID too big!");
            }
            if (fragment.row > 0b11111111) {
                throw new IOException("Fragment Row too big!");
            }
            if (fragment.column > 0b11111111) {
                throw new IOException("Fragment Column too big!");
            }
            dos.writeInt((fragment.row << 20)
                    | (fragment.column << 12)
                    | ((fragment.mirrorX ? 1 : 0) << 11)
                    | ((fragment.mirrorY ? 1 : 0) << 10)
                    | fragment.id);
        }
    }
}

class FragmentAsset {
    class TileLink {
        int id;
        boolean mirrorX;
        boolean mirrorY;
    }

    TileLink[][] tiles;
    int rows;
    int columns;

    public void serialize(DataOutputStream dos) throws IOException {
        if (rows > 0b11111111) {
            throw new IOException("Tile Rows too big!");
        }
        dos.writeByte(rows);

        if (columns > 0b11111111) {
            throw new IOException("Tile Columns too big!");
        }
        dos.writeByte(columns);

        for (TileLink[] row : tiles) {
            for (TileLink tile : row) {
                if (tile.id > 0b1111111111) {
                    throw new IOException("Tile ID too big!");
                }
                dos.writeShort(((tile.mirrorX ? 1 : 0) << 11)
                        | ((tile.mirrorY ? 1 : 0) << 10)
                        | tile.id);
            }
        }
    }
}

class TileAsset {
    PixelData[][] pixels;

    public void serialize(DataOutputStream dos) throws IOException {
        for (PixelData[] column : pixels) {
            for (PixelData pixel : column) {
                pixel.serialize(dos);
            }
        }
    }
}

class PixelData {
    public enum Color {
        BLACK,
        DARK_GRAY,
        LIGHT_GRAY,
        WHITE
    }

    public enum Surface {
        TRANSPARENT,
        UNLIT,
        MATTE,
        SHINY
    }

    public enum Normal {
        E,
        SE,
        S,
        SW,
        W,
        NW,
        N,
        NE
    }

    boolean special;
    Color color;
    Surface surface;
    Normal normal;

    public void serialize(DataOutputStream dos) throws IOException {
        dos.writeByte(((special ? 1 : 0) << 7)
                | (surface.ordinal() << 5)
                | (normal.ordinal() << 2)
                | color.ordinal());
    }
}
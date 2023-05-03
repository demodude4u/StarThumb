import java.awt.Color;
import java.awt.Desktop;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.nio.Buffer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.ImageWriter;
import javax.imageio.ImageTypeSpecifier;
import javax.imageio.ImageWriteParam;
import javax.imageio.metadata.IIOMetadata;
import javax.imageio.metadata.IIOMetadataNode;
import javax.imageio.stream.FileImageOutputStream;
import javax.imageio.stream.ImageOutputStream;

class BuildLSBitmap {

    private static List<Integer> grayscaleColorId = List.of(0x000000, 0x4e4e4e, 0xa2a2a2, 0xffffff);
    private static List<Integer> surfaceColorId = List.of(0xff0000, 0xff8000, 0xffff00, 0x00ff00);
    private static List<Integer> slopeColorId = List.of(0x000000, 0x8080ff, 0xda80da, 0xc0c0da, 0x80dada, 0x40c0da,
            0x2580da, 0x4040da, 0x8025da, 0xc040da);

    private static int[] shadingAngles = { 0, 1, 2, 3, 4, 3, 2, 1 };

    public static void main(String[] args) throws IOException {
        String argEnvironment;
        String argImage;
        if (args.length == 2) {
            argEnvironment = args[0];
            argImage = args[1];
        } else if (args.length == 1) {
            argEnvironment = "environment.png";
            argImage = args[0];
        } else {
            System.out.println("Usage: BuildLSBitmap.java [environment] image");
            return;
        }

        BufferedImage imgEnv = ImageIO.read(new File(argEnvironment));
        File fileImage = new File(argImage);
        BufferedImage image = ImageIO.read(fileImage);

        Map<Integer, int[]> envSurfaceShadings = new LinkedHashMap<>();
        for (int y = 0; y < imgEnv.getHeight(); y++) {
            int id = (colorIndex(surfaceColorId, imgEnv, 1, y) << 2) | colorIndex(grayscaleColorId, imgEnv, 0, y);
            int[] shades = new int[5];
            for (int i = 0; i < shades.length; i++) {
                shades[i] = colorIndex(grayscaleColorId, imgEnv, 2 + i, y);
            }
            envSurfaceShadings.put(id, shades);
        }

        BufferedImage imagePreview = new BufferedImage(image.getWidth() * 2 + 1, (image.getHeight() / 3) * 4 + 3,
                BufferedImage.TYPE_INT_ARGB);

        List<BufferedImage> previewFrames = new ArrayList<>();
        {
            Graphics2D g = imagePreview.createGraphics();
            for (int lightAngle = 0; lightAngle < 8; lightAngle++) {
                int x = (image.getWidth() + 1) * (lightAngle / 4);
                int y = (image.getHeight() / 3 + 1) * (lightAngle % 4);
                BufferedImage previewFrame = previewScaled(previewShading(image, envSurfaceShadings, lightAngle), 4, 10,
                        Color.black);
                previewFrames.add(previewFrame);
                g.drawImage(previewFrame, null, x, y);
            }
            g.dispose();
        }

        File fileImagePreview = new File(fileImage.getParent(), fileImage.getName().replace(".", "_preview."));
        ImageIO.write(imagePreview, "PNG", fileImagePreview);

        File fileImageAnim = new File(fileImage.getParent(), fileImage.getName().split("\\.")[0] + "_anim.gif");
        createAnimatedGif(previewFrames.toArray(BufferedImage[]::new), fileImageAnim, 250, true);

        Desktop.getDesktop().open(fileImageAnim);
    }

    private static int colorIndex(List<Integer> colors, BufferedImage image, int x, int y) {
        int closestIndex = -1;
        int closestDistance = Integer.MAX_VALUE;
        Color sample = new Color(image.getRGB(x, y));
        for (int i = 0; i < colors.size(); i++) {
            Color indexed = new Color(colors.get(i));
            int distance = Math.abs(sample.getRed() - indexed.getRed())
                    + Math.abs(sample.getGreen() - indexed.getGreen()) + Math.abs(sample.getBlue() - indexed.getBlue());
            if (distance < closestDistance) {
                closestIndex = i;
                closestDistance = distance;
            }
        }
        return closestIndex;
    }

    private static BufferedImage previewShading(BufferedImage image, Map<Integer, int[]> envSurfaceShadings,
            int lightAngle) {
        BufferedImage preview = new BufferedImage(image.getWidth(), image.getHeight() / 3, BufferedImage.TYPE_INT_ARGB);
        for (int y = 0; y < preview.getHeight(); y++) {
            for (int x = 0; x < preview.getWidth(); x++) {
                if (((image.getRGB(x, y) >> 24) & 0xFF) < 128) {
                    continue;
                }

                int color = colorIndex(grayscaleColorId, image, x, y);
                int surface = colorIndex(surfaceColorId, image, x, y + preview.getHeight() * 2);
                int slope = colorIndex(slopeColorId, image, x, y + preview.getHeight());

                int rgb;
                if (slope < 2) {
                    rgb = grayscaleColorId.get(color);
                } else {
                    int id = (surface << 2) | color;
                    rgb = grayscaleColorId.get(envSurfaceShadings.get(id)[shadingAngles[(slope - 2 + lightAngle) % 8]]);
                }

                preview.setRGB(x, y, 0xFF000000 | rgb);
            }
        }
        return preview;
    }

    private static BufferedImage previewScaled(BufferedImage image, int scale, int padding, Color bg) {
        BufferedImage ret = new BufferedImage(image.getWidth() * scale + padding * 2,
                image.getHeight() * scale + padding * 2, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = ret.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR);
        g.setColor(bg);
        g.fillRect(0, 0, ret.getWidth(), ret.getHeight());
        g.drawImage(image, padding, padding, padding + image.getWidth() * scale, padding + image.getHeight() * scale, 0,
                0, image.getWidth(), image.getHeight(), null);
        g.dispose();
        return ret;
    }

    private static void createAnimatedGif(BufferedImage[] frames, File output, int delay, boolean loop)
            throws IOException {

        // Create a new GifImageWriter instance
        ImageWriter writer = ImageIO.getImageWritersBySuffix("gif").next();
        ImageWriteParam params = writer.getDefaultWriteParam();

        ImageTypeSpecifier imageTypeSpecifier = new ImageTypeSpecifier(frames[0]);
        IIOMetadata metadata = writer.getDefaultImageMetadata(imageTypeSpecifier, params);

        String metaFormatName = metadata.getNativeMetadataFormatName();
        IIOMetadataNode root = (IIOMetadataNode) metadata.getAsTree(metaFormatName);

        IIOMetadataNode graphicsControlExtensionNode = getNode(root, "GraphicControlExtension");
        graphicsControlExtensionNode.setAttribute("disposalMethod", "none");
        graphicsControlExtensionNode.setAttribute("userInputFlag", "FALSE");
        graphicsControlExtensionNode.setAttribute("transparentColorFlag", "FALSE");
        graphicsControlExtensionNode.setAttribute("delayTime", Integer.toString(delay / 10));
        graphicsControlExtensionNode.setAttribute("transparentColorIndex", "0");

        IIOMetadataNode commentsNode = getNode(root, "CommentExtensions");
        commentsNode.setAttribute("CommentExtension", "Created by: https://memorynotfound.com");

        IIOMetadataNode appExtensionsNode = getNode(root, "ApplicationExtensions");
        IIOMetadataNode child = new IIOMetadataNode("ApplicationExtension");
        child.setAttribute("applicationID", "NETSCAPE");
        child.setAttribute("authenticationCode", "2.0");

        int loopContinuously = loop ? 0 : 1;
        child.setUserObject(
                new byte[] { 0x1, (byte) (loopContinuously & 0xFF), (byte) ((loopContinuously >> 8) & 0xFF) });
        appExtensionsNode.appendChild(child);
        metadata.setFromTree(metaFormatName, root);

        ImageOutputStream ios = new FileImageOutputStream(output);
        writer.setOutput(ios);
        writer.prepareWriteSequence(null);
        for (int i = 0; i < frames.length; i++) {
            writer.writeToSequence(new IIOImage(frames[i], null, metadata), null);
        }
        writer.endWriteSequence();
        ios.close();
    }

    private static IIOMetadataNode getNode(IIOMetadataNode rootNode, String nodeName) {
        for (int i = 0; i < rootNode.getLength(); i++) {
            if (rootNode.item(i).getNodeName().equalsIgnoreCase(nodeName)) {
                return ((IIOMetadataNode) rootNode.item(i));
            }
        }
        IIOMetadataNode node = new IIOMetadataNode(nodeName);
        rootNode.appendChild(node);
        return (node);
    }

}
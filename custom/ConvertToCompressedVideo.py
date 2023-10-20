__version__ = "1.0"

from meshroom.core import desc


class ConvertToCompressedVideo(desc.CommandLineNode):
    category = "Custom"
    documentation = """This node converts an input sequence of images into a compressed video with the specified characteristics using FFMPEG."""

    inputs = [
        desc.File(
            name="inputFiles",
            label="Input Files",
            description="Input images to convert into a video, with or without a pattern.",
            value="",
            uid=[0]
        ),
        desc.ChoiceParam(
            name="compressionOptions",
            label="Compression Options",
            description="Compression settings to apply. Compressing will reduce the size of the output video but might \n"
                        "degrade its quality.\n"
                        " - none: No compression will be applied\n"
                        " - fast: FFMPEG's 'fast' preset will be applied\n"
                        " - veryfast: FFMPEG's 'veryfast' preset will be applied",
            values=["none", "fast", "veryfast"],
            value="veryfast",
            exclusive=True,
            uid=[0]
        ),
        desc.BoolParam(
            name="inputIsExr",
            label="EXR Inputs",
            description="Select if the input file is a sequence of EXR images so that the correct conversion flag can be applied.",
            value=False,
            uid=[0]
        ),
        desc.StringParam(
            name="outputName",
            label="Output Name",
            description="Filename of the output video.",
            value='output.mp4',
            uid=[0],
        ),
        desc.IntParam(
            name="framerate",
            label="Framerate",
            description="Framerate for the output video.",
            value=24,
            range=(1, 100, 1),
            uid=[0]
        ),
        desc.StringParam(
            name="outputSize",
            label="Output Size",
            description="Size of the output video, written as \"width:height\" (e.g. 320:200). Setting either width or height to -1 will preserve the aspect ratio.\n"
                        "Setting the size to \"-1:-1\" means no rescale will be applied.",
            value="-1:-1",
            uid=[0]
        ),
    ]

    outputs = [
        desc.File(
            name='outputVideo',
            label='Output Video',
            description="Generated video.",
            value=desc.Node.internalFolder + '{outputNameValue}',
            uid=[],
        ),
    ]

    def processChunk(self, chunk):
        isExr = chunk.node.attribute("inputIsExr").value
        compression = chunk.node.attribute("compressionOptions").value

        if compression == "none":
            if isExr:
                self.commandLine = "ffmpeg -y -apply_trc iec61966_2_1 -pattern_type glob -i {inputFilesValue} -framerate {framerateValue} -vf scale={outputSizeValue} {outputVideoValue}"
            else:
                self.commandLine = "ffmpeg -y -pattern_type glob -i {inputFilesValue} -framerate {framerateValue} -vf scale={outputSizeValue} {outputVideoValue}"

        elif compression == "fast":
            if isExr:
                self.commandLine = "ffmpeg -y -apply_trc iec61966_2_1 -pattern_type glob -i {inputFilesValue} -profile:v main -preset fast -movflags +faststart -framerate {framerateValue} -vf scale={outputSizeValue} {outputVideoValue}"
            else:
                self.commandLine = "ffmpeg -y -pattern_type glob -i {inputFilesValue} -profile:v main -preset fast -movflags +faststart -framerate {framerateValue} -vf scale={outputSizeValue} {outputVideoValue}"
        
        else:
            if isExr:
                self.commandLine = "ffmpeg -y -apply_trc iec61966_2_1 -pattern_type glob -i {inputFilesValue} -profile:v main -preset veryfast -movflags +faststart -framerate {framerateValue} -vf scale={outputSizeValue} {outputVideoValue}"
            else:
                self.commandLine = "ffmpeg -y -pattern_type glob -i {inputFilesValue} -profile:v main -preset veryfast -movflags +faststart -framerate {framerateValue} -vf scale={outputSizeValue} {outputVideoValue}"

        desc.CommandLineNode.processChunk(self, chunk)


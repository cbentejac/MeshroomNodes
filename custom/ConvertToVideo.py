__version__ = "2.0"

from meshroom.core import desc


class ConvertToVideo(desc.CommandLineNode):
    category = "Custom"
    documentation = """This node converts an input sequence of images or a video into a video that may or may not be compressed with the specified characteristics using FFMPEG."""

    inputs = [
        desc.File(
            name="inputFiles",
            label="Input Files",
            description="Input images or video to convert into a compressed video, with or without a pattern.",
            value="",
            uid=[0]
        ),
        desc.BoolParam(
            name="isVideo",
            label="Video Input",
            description="True if the input is a video file, false otherwise. This will disable the \"Input Extension\" parameter.",
            value=False,
            uid=[0]
        ),
        desc.ChoiceParam(
            name="inputExtension",
            label="Input Extension",
            description="Extension of the input images. This will be used to determine which images are to be used if \n"
                        "a directory is provided as the input. If \"\" is selected, the provided input will be used as such.",
            values=["", "jpg", "jpeg", "png", "exr"],
            value="jpg",
            exclusive=True,
            enabled=lambda node: not node.isVideo.value,
            uid=[0]
        ),
        desc.GroupAttribute(
            name="compressionOptions",
            label="Compression Options",
            description="Compression settings.",
            groupDesc=[
                desc.ChoiceParam(
                    name="compressionType",
                    label="Compression Type",
                    description="Type of the compression to apply. Compressing will reduce the size of the output video but might \n"
                                "degrade its quality.\n"
                                " - none: No compression will be applied\n"
                                " - fast: FFMPEG's 'fast' preset will be applied\n"
                                " - veryfast: FFMPEG's 'veryfast' preset will be applied",
                    values=["none", "fast", "veryfast"],
                    value="veryfast",
                    validValue=lambda node: not (node.compressionOptions.compressionType.value != "none" and node.inputExtension.value == "exr"),
                    errorMessage="FFMPEG presets cannot be applied for .exr inputs. The compression type should be set to \"none\" \n"
                                  "for .exr inputs.",
                    exclusive=True,
                    uid=[0]
                ),
                desc.ChoiceParam(
                    name="resolutionFps",
                    label="Resolution And Framerate",
                    description="Resolution and framerate to use when generating the video, with the format 'HEIGHTpFPS'.",
                    values=["1080p30", "720p30", "576p25", "480p30"],
                    value="1080p30",
                    exclusive=True,
                    uid=[0]
                ),
            ]
        ),
        desc.StringParam(
            name="outputName",
            label="Output Name",
            description="Filename of the output video.",
            value="output.mp4",
            uid=[]
        ),
        desc.IntParam(
            name="pixelRatio",
            label="Pixel Aspect Ratio",
            description="Pixel aspect ratio to take into account when generating the output video.\n"
                        "The set aspect ratio will be applied on the width of the output video.",
            value=1,
            range=(1, 10, 1),
            uid=[],
            advanced=True
        ),
        desc.GroupAttribute(
            name="customResFps",
            label="Custom Resolution And Framerate",
            description="Override the resolution and framerate settings.",
            advanced=True,
            groupDesc=[
                desc.GroupAttribute(
                    name="customSize",
                    label="Size",
                    description="Custom size for the output video.",
                    groupDesc=[
                        desc.BoolParam(
                            name="overrideRes",
                            label="Override Size",
                            description="Override the preset size with a custom one.",
                            value=False,
                            uid=[0]
                        ),
                        desc.StringParam(
                            name="outputSize",
                            label="Output Size",
                            description="Size of the output video, written as \"width:height\" (e.g. 320:200). Setting either width or height to -1 will preserve the aspect ratio.\n"
                                        "Setting the size to \"-1:-1\" means no rescale will be applied.",
                            value="-1:-1",
                            uid=[0],
                            advanced=True,
                            enabled=lambda node: node.customResFps.customSize.overrideRes.value
                        )
                    ]
                ),
                desc.GroupAttribute(
                    name="customFramerate",
                    label="Framerate",
                    description="Framerate.",
                    groupDesc=[
                        desc.BoolParam(
                            name="overrideFps",
                            label="Override Framerate",
                            description="Override the preset framerate with a custom one.",
                            value=False,
                            uid=[0]
                        ),
                        desc.IntParam(
                            name="framerate",
                            label="Framerate",
                            description="Framerate for the output video.",
                            value=24,
                            range=(1, 100, 1),
                            uid=[0],
                            advanced=True,
                            enabled=lambda node: node.customResFps.customFramerate.overrideFps.value
                        )
                    ]
                )
            ]
        )
    ]

    outputs = [
        desc.File(
            name='outputVideo',
            label='Output Video',
            description="Generated video.",
            value=desc.Node.internalFolder + '{outputNameValue}',
            uid=[]
        )
    ]

    def processChunk(self, chunk):
        # Input files: if not a video or a regular expression, create a regular expression using the set file extension
        inputValue = "{inputFilesValue}"
        if chunk.node.attribute("inputExtension").enabled and chunk.node.attribute("inputExtension").value != "":
            inputValue = "{inputFilesValue}/*.{inputExtensionValue}"

        # If the input is not a video, use the pattern_type option
        patternType = " "
        if not chunk.node.attribute("isVideo").value:
            patternType = " -pattern_type glob "

        # If the input files are .exr files, a specific option must be applied to get correct colors
        isExr = " "
        if chunk.node.attribute("inputExtension").enabled and chunk.node.attribute("inputExtension").value == "exr":
            isExr = " -apply_trc iec61966_2_1 "

        # Depending on the compression type, use the corresponding FFMPEG profiles
        compression = " "
        compressionType = chunk.node.attribute("compressionOptions.compressionType").value
        if compressionType == "fast":
            compression = " -profile:v main -preset fast -movflags +faststart "
        elif compressionType == "veryfast":
            compression = " -profile:v main -preset veryfast -movflags +faststart "

        # Initialize the resolution and framerate for the output
        size = "-1:-1"
        fps = "30"
        resolution = chunk.node.attribute("compressionOptions.resolutionFps").value

        # Set the resolution and framerate based on the predetermined settings. If the options to override the size
        # and/or framerate are enabled, use those custom values over the standard ones
        if chunk.node.attribute("customResFps.customSize.outputSize").enabled or chunk.node.attribute("customResFps.customFramerate.framerate").enabled:
            if chunk.node.attribute("customResFps.customSize.outputSize").enabled:
                size = chunk.node.attribute("customResFps.customSize.outputSize").value
            if chunk.node.attribute("customResFps.customFramerate.framerate").enabled:
                fps = chunk.attribute("customResFps.customFramerate.framerate").value
        elif resolution == "1080p30":
            size = "-1:1080"
        elif resolution == "720p30":
            size = "-1:720"
        elif resolution == "576p25":
            size = "-1:576"
            fps = "25"
        else:
            size = "-1:480"

        # Set the pixel aspect ratio if needed
        pixelRatio = " "
        if chunk.node.attribute("pixelRatio").value != 1:
            pixelRatio = " -aspect {pixelRatioValue}:1 "

        self.commandLine = "ffmpeg -y" + isExr + patternType + "-i " + inputValue + compression + \
                           " -c:v libx264 -level 42 -framerate " + fps + " -vf scale=" + size + pixelRatio + \
                           "{outputVideoValue}"

        desc.CommandLineNode.processChunk(self, chunk)


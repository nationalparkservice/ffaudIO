# ffaudIO
Read nearly any kind of media into NumPy arrays with help from [ffmpeg](http://ffmpeg.org/)

## Installation

First, install ffmpeg if you haven't.

On Mac or Linux, this is relatively painless using a package manager such as `brew` or `apt-get`. However, on Windows, you need to set things up yourself:

1. Go to http://ffmpeg.org/download.html, hover over Windows, and click [Windows Builds](http://ffmpeg.zeranoe.com/builds/)
2. Download a *static* build, most likely 64-bit
    - If you don't have [7-zip](http://www.7-zip.org/), you'll need to first download and install it to unzip the ffmpeg download (requires administrator privileges)
4. Right-click on the zipped ffmpeg file in your Downloads folder and click 7-zip > Extract Here
5. Move the folder (which should be named like `ffmpeg-<lots of text>`) to the root of your hard drive (i.e. `C:/`)
6. Feel free to rename the folder to just plain `ffmpeg`

Now, you *could* be done here in order to use ffaudIO. But you might as well add ffmpeg to your `PATH` as well, so you can use it in Command Prompt.

1. Open the Start menu, right click on Computer, and click Properties
2. Click Advanced System Settings on the left (requires administrator privileges)
3. Select the Advanced tab, and click Environment Variables at the bottom
4. Scroll down in the lower pane (System variables) until you find a variable named `Path`
5. Double-click on `Path`, and press the right arrow to jump to the end of the Variable value text box
6. Enter this exact text after everything that's already in the Variable value field: `;C:\ffmpeg\bin`
    - If you didn't rename your ffmpeg folder to `ffmpeg`, but kept its original long name, replace `ffmpeg` with that long name
7. Click, OK, OK, and OK.
8. To make sure everything works, open Command Prompt
9. Type `ffmpeg` and press enter.
10. You should see lots of info about ffmpeg's build configuration. You shouldn't see `'ffmpeg' is not recognized as an internal or external command, operable program or batch file.`

## Configuration

On line 12 of [ffaudIO.py](ffaudIO.py#L12), set the `FFMPEG_CMD` variable to the path to your ffmpeg executable. Or, if typing `ffmpeg` works at your command prompt, then just set `FFMPEG_CMD` to `ffmpeg`; your OS already knows where to find it.

*The rest of this README will be completed sometime soon.*
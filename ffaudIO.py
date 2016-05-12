import subprocess
import sys
import re
import numpy as np
import collections

"""
Pipe out of ffmpeg as a subprocess to decode audio from files. Heavily adapted from @Zulko's moviepy:
https://github.com/Zulko/moviepy/blob/master/moviepy/audio/io/readers.py
"""

FFMPEG_CMD = 'C:/ffmpeg/bin/ffmpeg.exe'   # command to invoke ffmpeg (just `ffmpeg` if it's in the shell's search path,
                        # otherwise path to the binary)

def info(filename):
    """
    Returns duration (sec), rate (Hz), codec, and channels (int) of named file
    """

    ffmpeg = subprocess.Popen([FFMPEG_CMD, '-i', filename],
        stdout= subprocess.PIPE,
        stderr= subprocess.PIPE)
    ffmpeg.stdout.readline()
    ffmpeg.terminate()

    info = ffmpeg.stderr.read().decode('utf8')
    lines = info.splitlines()

    if "No such file or directory" in lines[-1]:
        raise IOError("%s not found! Wrong path ?"%filename)
    elif "Invalid data found" in lines[-1]:
        raise IOError("{} contains invalid data.".format(filename))

    duration_line_i, duration_line = next((i, l) for i, l in enumerate(lines) if l.strip().startswith("Duration"))

    # get duration in seconds
    dur_match = re.search(r"(\d+):(\d\d):(\d\d\.\d+)", duration_line)
    try:
        hms = [ float(group) for group in dur_match.groups() ]
        secs = hms[0] * 3600 + hms[1] * 60 + hms[2]
    except ValueError:
        raise ValueError("Unable to parse duration from line '{}'".format(duration_line))

    stream_line = lines[duration_line_i+1].strip()
    if not stream_line.startswith("Stream"):
        raise ValueError("Unexpected line after duration line: '{}'".format(stream_line))

    # get codec
    stream_parts = stream_line.split(", ")
    try:
        codec = re.search(r"Audio: (\w+)\s?", stream_parts[0]).group(1)
    except ValueError:
        raise ValueError("Unable to parse codec from '{}'".format(stream_parts[0]))

    # get rate
    try:
        rate = re.search(r'(\d+) Hz', stream_parts[1]).group(1)
        rate = int(rate)
    except ValueError:
        raise ValueError("Unable to parse rate from '{}'".format(stream_parts[1]))

    # get channels
    channels_str = stream_parts[2]
    if channels_str == "mono":
        channels = 1
    elif channels_str == "stereo":
        channels = 2
    else:
        try:
            channels = int(channels_str.split(" ")[0])
        except ValueError:
            raise ValueError("Unable to parse channels from '{}'".format(channels_str))

    # get format
    fmt = stream_parts[3]

    FFinfo = collections.namedtuple("FFinfo", "secs rate codec channels")
    return FFinfo(secs, rate, codec, channels)

def read(filename, dtype= np.int16):
    if not isinstance(dtype, np.dtype):
        dtype = np.dtype(dtype)

    # determine size, kind, and byteorder of desired dtype
    bits = dtype.itemsize * 8
    kind = dtype.kind
    byteorder = dtype.byteorder

    if byteorder == "=":
        byteorder = "<" if sys.byteorder == "little" else ">"

    # translate into ffmpeg format string
    if kind == "i":
        kind = "s"

    if kind not in ('s','u','f'):
        raise TypeError("Cannot read audio into an array of datatype '{}' (unsupported kind '{}')".format(dtype, kind))

    if bits not in (8, 16, 24, 32, 64):
        raise TypeError("Cannot read audio into an array of datatype '{}' (unsupported item size '{}')".format(dtype, bits/8))

    ff_byteorder = "le" if byteorder == "<" else "be"

    ff_format = kind+str(bits)+ff_byteorder
    ff_codec = "pcm_" + ff_format

    # TODO:
    # Calling ffmpeg twice, just to get the info, is a significant slowdown on small files
    # The issue is that np.fromfile() doesn't work on stdout, and doing stdout.readall()
    # returns immutable bytes, and an np array created from that buffer is also immutable.
    # Using np.readinto() and a bytearray (or it could be an empty ndarray) requires knowing
    # the length in advance---hence needing info.
    # But reading from stderr will block until (most? all? not just any) data has been read from
    # stdout, so with a single ffmpeg call, data *must* be read before it's possible to know
    # the number of bytes coming.
    #
    # The best option might be to manually fill a bytearray (or better, empty ndarray)
    # with bytes in a loop of stdout.read(1024, or wordsize, or io.DEFAULT_BUFFER_SIZE, or something)
    # 
    # Need to timeit:
    # - current method, with double ffmpeg call
    # - stdout.readall() into immutable bytes, then copying into an array in order to be mutable
    # - manually expanding an empty array/bytestring in while loop, possibly trying to read from
    #   stderr and expanding the array to the full size when possible (well, still, there's the
    #   bitrate-length-estimation issue, so that's possibly an unnecessary optimization)

    ff_info = info(filename)

    # TODO: why does bufsize= 0 in Popen cause only 4608 bytes to be read with readinto()?

    # read audio into raw binary, formatted to match the given numpy dtype
    ffmpeg = subprocess.Popen([FFMPEG_CMD, '-i', filename,
        '-vn',                       # ignore video
        '-f', ff_format,             # input format
        '-acodec', ff_codec,         # audio codec format 
        '-'],                        # pipe to stdout
        stdout= subprocess.PIPE,
        stderr= subprocess.PIPE)

    # overshoot length of the file to account for length-estimation-from-bitrate errors
    # TODO: is 5% a reasonable amount??
    # print("ff_info.secs", ff_info.secs)
    nsamples_guess = int((ff_info.secs * 1.05) * ff_info.rate * ff_info.channels)
    # print("nsamples_guess:", nsamples_guess)
    totalBytes_guess = nsamples_guess * dtype.itemsize
    # print("totalBytes_guess:", totalBytes_guess)

    audio_bytes = bytearray(totalBytes_guess)
    actualBytes = ffmpeg.stdout.readinto(audio_bytes)
    # print("actualBytes:", actualBytes)
    # print("actualBytes // dtype.itemsize:", actualBytes // dtype.itemsize)

    # create ndarray using actual number of bytes read
    audio = np.frombuffer(audio_bytes, dtype= dtype, count= actualBytes // dtype.itemsize)
    # print("audio.shape", audio.shape)


    # audio_bytes = ffmpeg.stdout.read()
    # audio = np.frombuffer(audio_bytes, dtype= dtype)
    # audio = np.frombuffer(ffmpeg.stdout, dtype= dtype)
    if ff_info.channels > 1:
        audio.shape = ( len(audio) / ff_info.channels, ff_info.channels )

    # ffmpeg.terminate()
    # print(ffmpeg.stderr.read().decode("utf8"))
    return ff_info, audio

# def writeAudio(filename, data, rate, codec= None):
#     """
#     Write the given raw audio data to disk as an audio file
#     If no codec specified, defaults to an uncompressed WAV file of same byte format as input
#     """

#     bytes = data.dtype.itemsize
#     f_format = 's' + str(bytes * 8) + 'le'  # [num bits] signed little-endian bits
#     acodec = 'pcm_s' + str(bytes * 8) + 'le'

#     if codec is None:
#         codec = acodec

#     ffmpeg = subprocess.Popen([FFMPEG_CMD,
#         '-y',                                               # overwrite without asking
#         '-f', f_format,                                     # input format
#         '-acodec', acodec,                                  # audio codec format 
#         '-ar', str(rate),                                   # rate (Hz)
#         '-ac', str(data.shape[1] if data.ndim == 2 else 1), # channles to use
#         '-i', '-',                                          # pipe from stdin
#         '-acodec', codec,                                   # output codec
#         '-ar', str(rate),                                   # output rate == input rate
#         filename],                                          # filename to write to
#         stdin= subprocess.PIPE,
#         stderr= subprocess.PIPE)

#     data.tofile(ffmpeg.stdin)
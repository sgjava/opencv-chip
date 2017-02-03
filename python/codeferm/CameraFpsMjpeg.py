"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on January 30, 2017
sgoldsmith@codeferm.com
"""

"""Video capture using socket and calculate FPS.

sys.argv[1] = camera index, url or will default to "-1" if no args passed.
sys.argv[2] = frames to capture, int or will default to "200" if no args passed.

Add ?dummy=param.mjpg at end of URL. For example:
http://host/?action=stream?dummy=param.mjpg

@author: sgoldsmith

"""

import logging, sys, time, re, socket, urlparse, base64, numpy, cv2

def open():
    """Open socket"""
    # Parse URL
    parsed = urlparse.urlparse(url)
    port = parsed.port
    # Set port to default if not set
    if not port:
        port = 80
    # See if query string present
    if not parsed.query:
        path = parsed.path
    else:
        path = "%s%s%s" % (parsed.path, "?", parsed.query)   
    # See if we need to do HTTP basic access authentication
    if parsed.username is None:
        # Build HTTP header
        lines = [
            "GET %s HTTP/1.1" % path,
            "Host: %s" % parsed.hostname,
        ]
    else:
        # Base64 encode username and password
        token = base64.encodestring("%s:%s" % (parsed.username, parsed.password)).strip()
        # Build HTTP header
        lines = [
            "GET %s HTTP/1.1" % path,
            "Host: %s" % parsed.hostname,
            "Authorization: Basic %s" % token,
        ]
    # AF_INET: IPv4 protocols (both TCP and UDP)
    # SOCK_STREAM: a connection-oriented, TCP byte stream
    streamSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    streamSock.connect((parsed.hostname, port))
    # Socket file in read, write, binary mode and no buffer
    socketFile = streamSock.makefile("rwb", bufsize=0)
    # Send HTTP GET for MJPEG stream
    socketFile.write("\r\n".join(lines) + "\r\n\r\n")
    # Read in HTTP headers
    line = socketFile.readline()
    while len(line) > 0 and line.strip() != "":
        parts = line.split(":")
        if len(parts) > 1 and parts[0].lower() == "content-type":
            # Extract boundary string from content-type
            content_type = parts[1].strip()
            boundary = content_type.split(";")[1].split("=")[1]
        line = socketFile.readline()
    # See if we found "content-type"
    if not boundary:
        raise Exception("Cannot find content-type")
    return socketFile, streamSock, boundary

def getFrameLength(socketFile):
    """Get frame length from stream"""
    line = socketFile.readline()
    # Find boundary
    while len(line) > 0 and line.count(boundary) == 0:
        line = socketFile.readline()
    # Read in chunk headers
    while len(line) > 0 and line.strip() != "":
        parts = line.split(":")
        if len(parts) > 1 and parts[0].lower().count("content-length") > 0:
            # Grab chunk length
            length = int(parts[1].strip())
        line = socketFile.readline()
    return length

def getFrame(socketFile):
    """Get raw frame data from stream and decode"""
    image = socketFile.read(getFrameLength(socketFile))
    return cv2.imdecode(numpy.fromstring(image, numpy.uint8), cv2.IMREAD_COLOR)

logger = logging.getLogger("CameraFpsMjpeg")
logger.setLevel("INFO")
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(module)s %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)
# If no args passed then use default camera
if len(sys.argv) < 2:
    url = "http://localhost:8080/?action=stream?dummy=param.mjpg"
    frames = 200
else:
    url = sys.argv[1]
    frames = int(sys.argv[2])
logger.info("OpenCV %s" % cv2.__version__)
logger.info("URL: %s, frames to capture: %d" % (url, frames))
# Set socket timeout
socket.setdefaulttimeout(10)
socketFile, streamSock, boundary = open()
image = getFrame(socketFile)
height, width, unknown = image.shape
logger.info("Resolution: %dx%d" % (width,height))
if width > 0 and height > 0:
    logger.info("Calculate FPS using %d frames" % frames)
    framesLeft = frames
    start = time.time()
    # Calculate FPS
    while(framesLeft > 0):
        image = getFrame(socketFile)
        framesLeft -= 1
    elapsed = time.time() - start
    fps = frames / elapsed
    logger.info("Calculated %4.1f FPS, elapsed time: %4.2f seconds" % (fps, elapsed))
socketFile.close()
streamSock.close()

"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 3, 2017
sgoldsmith@codeferm.com
"""

"""Video capture using cv2.VideoCapture and calculate FPS.

sys.argv[1] = camera index, url or will default to "-1" if no args passed.
sys.argv[2] = frames to capture, int or will default to "200" if no args passed.
sys.argv[3] = frame width, int or will default to "640" if no args passed.
sys.argv[4] = frame height, int or will default to "480" if no args passed.
sys.argv[5] = frame per second, int or will default to "5" if no args passed.

For MJPEG streams use ?dummy=param.mjpg at end of URL. For example:
http://host/?action=stream?dummy=param.mjpg

@author: sgoldsmith

"""

import logging, sys, time, re, socket, cv2

# Configure logger
logger = logging.getLogger("camerfpscv")
logger.setLevel("INFO")
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(module)s %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)
# If no args passed then use default camera
if len(sys.argv) < 4:
    url = -1
    frames = 200
    width = 640
    height = 480
    fps = 5
# If arg is an integer then convert to int
elif re.match(r"[-+]?\d+$", sys.argv[1]) is not None:
    url = int(sys.argv[1])
    frames = int(sys.argv[2])
    width = int(sys.argv[3])
    height = int(sys.argv[4])
    fps = int(sys.argv[5])
else:
    url = sys.argv[1]
    frames = int(sys.argv[2])
    width = int(sys.argv[3])
    height = int(sys.argv[4])
    fps = int(sys.argv[5])
videoCapture = cv2.VideoCapture()
# This returns True even for bad URLs
success = videoCapture.open(url)
# Set resolution
videoCapture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
videoCapture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
# Set FPS
videoCapture.set(cv2.CAP_PROP_FPS, fps)
logger.info("OpenCV %s" % cv2.__version__)
logger.info("URL: %s, frames to capture: %d, width: %d, height: %d, fps: %d" % (url, frames, width, height, fps))
logger.info("Resolution: %dx%d" % (videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH),
                               videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
# Deal with VideoCapture always returning True otherwise it will hang on VideoCapture.grab()
if videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH) > 0 and videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT) > 0:
    logger.info("Calculate FPS using %d frames" % frames)
    framesLeft = frames
    start = time.time()
    # Calculate FPS
    while(framesLeft > 0):
        videoCapture.grab()
        success, image = videoCapture.read()
        if not success:
            logger.error("Failed to read image")
        framesLeft -= 1
    elapsed = time.time() - start
    fps = frames / elapsed
    logger.info("Calculated %4.1f FPS, elapsed time: %4.2f seconds" % (fps, elapsed))
del videoCapture

"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 3, 2017
sgoldsmith@codeferm.com
"""

"""Video capture using socket, write to video file and calculate FPS.

sys.argv[1] = camera index, url or will default to "http://localhost:8080/?action=stream" if no args passed.
sys.argv[2] = frames to capture, int or will default to "200" if no args passed.
sys.argv[3] = fourcc, string or will default to "XVID" if no args passed.
sys.argv[4] = frames per second for writer, int or will default to 5 if no args passed.
sys.argv[5] = output file name, string or will default to "camera.avi" if no args passed.

Add ?dummy=param.mjpg at end of URL. For example:
http://host/?action=stream?dummy=param.mjpg

@author: sgoldsmith

"""

import logging, sys, time, cv2, mjpegclient

logger = logging.getLogger("camerawriter")
logger.setLevel("INFO")
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(module)s %(message)s")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)
# If no args passed then use defaults
if len(sys.argv) < 5:
    url = "http://localhost:8080/?action=stream"
    frames = 200
    fourcc = "XVID"
    fps = 5
    outputFile = "camera.avi"
else:
    url = sys.argv[1]
    frames = int(sys.argv[2])
    fourcc = sys.argv[3]
    fps = int(sys.argv[4])
    outputFile = sys.argv[5]
   
logger.info("OpenCV %s" % cv2.__version__)
logger.info("URL: %s, frames to capture: %d" % (url, frames))
socketFile, streamSock, boundary = mjpegclient.open(url, 10)
image = mjpegclient.getFrame(socketFile, boundary)
height, width, unknown = image.shape
logger.info("Resolution: %dx%d" % (width, height))
if width > 0 and height > 0:
    videoWriter = cv2.VideoWriter(outputFile, cv2.VideoWriter_fourcc(fourcc[0], fourcc[1], fourcc[2], fourcc[3]), fps, (width, height), True)
    logger.info("Calculate FPS using %d frames" % frames)
    framesLeft = frames
    start = time.time()
    # Calculate FPS
    while(framesLeft > 0):
        image = mjpegclient.getFrame(socketFile, boundary)
        videoWriter.write(image)
        framesLeft -= 1
    elapsed = time.time() - start
    fps = frames / elapsed
    logger.info("Calculated %4.1f FPS, elapsed time: %4.2f seconds" % (fps, elapsed))
    del videoWriter
socketFile.close()
streamSock.close()

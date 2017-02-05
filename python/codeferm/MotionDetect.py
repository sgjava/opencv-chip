"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 4, 2017
sgoldsmith@codeferm.com
"""
from email.mime import image

"""Motion detector.

Resizes frame and uses moving average to determine change percent. Inner
rectangles are filtered out as well. This can result in ~40% better
performance and a more stable ROI.

sys.argv[1] = url or will default to "http://localhost:8080/?action=stream" if no args passed.
sys.argv[2] = frames to capture, int or will default to "200" if no args passed.
sys.argv[3] = fourcc, string or will default to "XVID" if no args passed.
sys.argv[4] = frames per second for writer, int or will default to 5 if no args passed.
sys.argv[5] = recording dir, string or will default to "motion" if no args passed.

@author: sgoldsmith

"""

import logging, sys, os, time, datetime, numpy, cv2, mjpegclient

def inside(r, q):
    """See if one rectangle inside another"""
    rx, ry, rw, rh = r
    qx, qy, qw, qh = q
    return rx > qx and ry > qy and rx + rw < qx + qw and ry + rh < qy + qh

def contours(source):
    """Return contours"""
    # The background (bright) dilates around the black regions of frame
    source = cv2.dilate(source, None, iterations=15);
    # The bright areas of the image (the background, apparently), get thinner, whereas the dark zones bigger
    source = cv2.erode(source, None, iterations=10);
    # Find contours
    image, contours, heirarchy = cv2.findContours(source, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # Add objects with motion
    movementLocations = []
    for contour in contours:
        rect = cv2.boundingRect(contour)
        movementLocations.append(rect)
    return movementLocations

if __name__ == '__main__':
    # Configure logger
    logger = logging.getLogger("MotionDetect")
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
        recordDir = "motion"
    else:
        url = sys.argv[1]
        frames = int(sys.argv[2])
        fourcc = sys.argv[3]
        fps = int(sys.argv[4])
        recordDir = sys.argv[5]
        
    logger.info("OpenCV %s" % cv2.__version__)
    logger.info("URL: %s, frames to capture: %d" % (url, frames))
    socketFile, streamSock, boundary = mjpegclient.open(url, 10)
    image = mjpegclient.getFrame(socketFile, boundary)
    frameHeight, frameWidth, unknown = image.shape
    logger.info("Resolution: %dx%d" % (frameWidth, frameHeight))
    if frameWidth > 0 and frameHeight > 0:
        # Motion detection generally works best with 320 or wider images
        widthDivisor = int(frameWidth / 320)
        if widthDivisor < 1:
            widthDivisor = 1
        frameResizeWidth = int(frameWidth / widthDivisor)
        frameResizeHeight = int(frameHeight / widthDivisor)
        logger.info("Resized to: %dx%d" % (frameResizeWidth, frameResizeHeight))
        # Used for full size image marking
        widthMultiplier = int(frameWidth / frameResizeWidth)
        heightMultiplier = int(frameHeight / frameResizeHeight)     
        movingAvgImg = None
        totalPixels = frameResizeWidth * frameResizeHeight
        framesLeft = frames
        movementLocations = []
        recording = False
        start = time.time()
        # Calculate FPS
        while(framesLeft > 0):
            image = mjpegclient.getFrame(socketFile, boundary)
            # Resize image if not the same size as the original
            if frameResizeWidth != frameWidth:
                resizeImg = cv2.resize(image, (frameResizeWidth, frameResizeHeight), interpolation=cv2.INTER_NEAREST)
            else:
                resizeImg = image
            # Generate work image by blurring
            workImg = cv2.blur(resizeImg, (8, 8))
            # Generate moving average image if needed
            if movingAvgImg is None:
                movingAvgImg = numpy.float32(workImg)
            # Generate moving average image
            cv2.accumulateWeighted(workImg, movingAvgImg, .03)
            diffImg = cv2.absdiff(workImg, cv2.convertScaleAbs(movingAvgImg))
            # Convert to grayscale
            grayImg = cv2.cvtColor(diffImg, cv2.COLOR_BGR2GRAY)
            # Convert to BW
            return_val, grayImg = cv2.threshold(grayImg, 25, 255, cv2.THRESH_BINARY)
            # Total number of changed motion pixels
            motionPercent = 100.0 * cv2.countNonZero(grayImg) / totalPixels
            # Detect if camera is adjusting and reset reference if more than maxChange
            if motionPercent > 25.0:
                movingAvgImg = numpy.float32(workImg)
            movementLocations = contours(grayImg)
            movementLocationsFiltered = []
            # Filter out inside rectangles
            for ri, r in enumerate(movementLocations):
                for qi, q in enumerate(movementLocations):
                    if ri != qi and inside(r, q):
                        break
                else:
                    movementLocationsFiltered.append(r)
            # Threshold to trigger motion
            if motionPercent > 2.0:
                if not recording:
                    now = datetime.datetime.now()
                    # Construct directory from configuration, camera name and date
                    fileDir = "%s%s%s%s%s%s" % (recordDir, os.sep, "motion", os.sep, now.strftime("%Y-%m-%d"), os.sep)
                    # Create dir for if it doesn"t exist
                    if not os.path.exists(fileDir):
                        os.makedirs(fileDir)
                    fileName = "%s.%s" % (now.strftime("%H-%M-%S"), "avi")
                    videoWriter = cv2.VideoWriter("%s/%s" % (fileDir,fileName), cv2.VideoWriter_fourcc(fourcc[0],fourcc[1],fourcc[2],fourcc[3]), fps, (frameWidth, frameHeight), True)
                    logger.info("Start recording (%4.2f) %s%s @ %3.1f FPS" % (motionPercent, fileDir, fileName, fps))
                    recording = True
                for x, y, w, h in movementLocationsFiltered:
                    cv2.putText(image, "%dw x %dh" % (w, h), (x * widthMultiplier, (y * heightMultiplier) - 4), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), thickness=2, lineType=cv2.LINE_AA)
                    # Draw rectangle around fond objects
                    cv2.rectangle(image, (x * widthMultiplier, y * heightMultiplier),
                                  ((x + w) * widthMultiplier, (y + h) * heightMultiplier),
                                  (0, 255, 0), 2)
            # If recording write frame and check motion percent
            if recording:
                videoWriter.write(image)
                if motionPercent <= 0.0:
                    logger.info("Stop recording")
                    del videoWriter
                    recording = False
            framesLeft -= 1
        elapsed = time.time() - start
        fps = frames / elapsed
        logger.info("Calculated %4.1f FPS, elapsed time: %4.2f seconds" % (fps, elapsed))
        socketFile.close()
        streamSock.close()

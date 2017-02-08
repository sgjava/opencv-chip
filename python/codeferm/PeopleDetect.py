"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 4, 2017
sgoldsmith@codeferm.com
"""

"""People detector using sampling, resize and motion ROIs.

Resizes frame and uses moving average to determine change percent. This can
result in up to ~1200% better performance and a more stable ROI. Histogram
of Oriented Gradients ([Dalal2005]) object detector is used.

A frame buffer is used to record 1 second before motion threshold is triggered.

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
    logger = logging.getLogger("PeopleDetect")
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
        recordDir = "people"
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
        # Analyze only ~3 FPS which works well with this type of detection
        frameToCheck = int(fps / 3)
        # 0 means check every frame
        if frameToCheck < 1:
            frameToCheck = 0
        skipCount = 0         
        movingAvgImg = None
        totalPixels = frameResizeWidth * frameResizeHeight
        framesLeft = frames
        movementLocations = []
        frameBuf = []  # Frame buffer, so we can record just before motion starts
        frameBufSize = fps  # Buffer one second of video
        recording = False
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        start = time.time()
        # Calculate FPS
        while(framesLeft > 0):
            now = datetime.datetime.now()  # Used for timestamp in frame buffer and filename
            image = mjpegclient.getFrame(socketFile, boundary)
            # Buffer image
            if len(frameBuf) == frameBufSize:
                # Toss first image in list (oldest)
                frameBuf.pop(0)
            # Add new image to end of list
            frameBuf.append((image, int(time.mktime(now.timetuple()) * 1000000 + now.microsecond)))            
            # Skip frames until skip count <= 0
            if skipCount <= 0:
                skipCount = frameToCheck
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
                        # Construct directory name from recordDir and date
                        fileDir = "%s%s%s%s%s%s" % (recordDir, os.sep, "people-detect", os.sep, now.strftime("%Y-%m-%d"), os.sep)
                        # Create dir if it doesn"t exist
                        if not os.path.exists(fileDir):
                            os.makedirs(fileDir)
                        fileName = "%s.%s" % (now.strftime("%H-%M-%S"), "avi")
                        videoWriter = cv2.VideoWriter("%s/%s" % (fileDir, fileName), cv2.VideoWriter_fourcc(fourcc[0], fourcc[1], fourcc[2], fourcc[3]), fps, (frameWidth, frameHeight), True)
                        logger.info("Start recording (%4.2f) %s%s @ %3.1f FPS" % (motionPercent, fileDir, fileName, fps))
                        peopleFound = False
                        recording = True
                    for x, y, w, h in movementLocationsFiltered:
                        cv2.putText(image, "%dw x %dh" % (w, h), (x * widthMultiplier, (y * heightMultiplier) - 4), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), thickness=2, lineType=cv2.LINE_AA)
                        # Draw rectangle around found objects
                        cv2.rectangle(image, (x * widthMultiplier, y * heightMultiplier),
                                      ((x + w) * widthMultiplier, (y + h) * heightMultiplier),
                                      (0, 255, 0), 2)
                    # Check motion ROIs for people
                    for x, y, w, h in movementLocationsFiltered:
                        # Make sure ROI is big enough for detector
                        if w > 63 and h > 127:
                            imageRoi = resizeImg[y:y + h, x:x + w]
                            # foundLocations, foundWeights = hog.detectMultiScale(imageRoi, winStride=(8, 8), padding=(16, 16), scale=1.05)
                            foundLocations, foundWeights = hog.detectMultiScale(imageRoi, winStride=(8, 8), padding=(8, 8), scale=1.1)
                            if len(foundLocations) > 0:
                                peopleFound = True
                                i = 0
                                for x2, y2, w2, h2 in foundLocations:
                                    imageRoi2 = image[y * heightMultiplier:y * heightMultiplier + (h * heightMultiplier), x * widthMultiplier:x * widthMultiplier + (w * widthMultiplier)]
                                    # Draw rectangle around people
                                    cv2.rectangle(imageRoi2, (x2, y2), (x2 + (w2 * widthMultiplier), y2 + (h2 * heightMultiplier) - 1), (255, 0, 0), 2)
                                    # Print weight
                                    cv2.putText(imageRoi2, "%1.2f" % foundWeights[i], (x2, y2 - 4), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), thickness=2, lineType=cv2.LINE_AA)
                                    i += 1
                                logger.info("People detected locations: %s" % (foundLocations))
            else:
                skipCount -= 1                        
            # If recording write frame and check motion percent
            if recording:
                # Write first image in buffer (the oldest)
                videoWriter.write(frameBuf[0][0])
                # Threshold to stop recording
                if motionPercent <= 0.25:
                    logger.info("Stop recording")
                    del videoWriter
                    # Change name if people found during motion
                    if peopleFound:
                        os.rename("%s/%s" % (fileDir, fileName),"%s/%s-people" % (fileDir, fileName))
                    recording = False
            framesLeft -= 1
        elapsed = time.time() - start
        fps = frames / elapsed
        logger.info("Calculated %4.1f FPS, elapsed time: %4.2f seconds" % (fps, elapsed))
        socketFile.close()
        streamSock.close()

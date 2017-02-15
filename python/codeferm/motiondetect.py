"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 4, 2017
sgoldsmith@codeferm.com
"""

"""Motion detector.

Resizes frame, sampling and uses moving average to determine change percent. Inner
rectangles are filtered out as well. This can result in better performance and
a more stable ROI.

Optional pedestrian detector using sampling, resize and motion ROI. Histogram of Oriented
Gradients ([Dalal2005]) object detector is used. You can get up to 1200%
performance boost using this method.

A frame buffer is used to record 1 second before motion threshold is triggered.

sys.argv[1] = configuration file name or will default to "motiondetect.ini" if no args passed.

@author: sgoldsmith

"""

import ConfigParser, logging, sys, os, time, datetime, numpy, cv2, urlparse, mjpegclient, motiondet, pedestriandet, facedet

def markImg(target, rects, widthMul, heightMul, boxColor, boxThickness):
    """Mark detected objects in image"""
    for x, y, w, h in rects:
        # Mark target
        cv2.rectangle(target, (x * widthMul, y * heightMul), ((x + w) * widthMul, (y + h) * heightMul), boxColor, boxThickness)
        if x <= 0:
            x = 2
        if y <= 0:
            y = 7
        cv2.putText(target, "%dw x %dh" % (w, h), (x * widthMul, (y * heightMul) - 4), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), thickness=2, lineType=cv2.LINE_AA)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        configFileName = "../config/motiondetect.ini"
    else:
        configFileName = sys.argv[1]
    parser = ConfigParser.SafeConfigParser()
    # Read configuration file
    parser.read(configFileName)
    # Configure logger
    logger = logging.getLogger("motiondetect")
    logger.setLevel(parser.get("logging", "level"))
    formatter = logging.Formatter(parser.get("logging", "formatter"))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Set camera related data attributes
    cameraName = parser.get("camera", "name")    
    url = parser.get("camera", "url")
    fpsInterval = parser.getfloat("camera", "fpsInterval")
    fps = parser.getint("camera", "fps")
    fourcc = parser.get("camera", "fourcc")
    recordFileExt = parser.get("camera", "recordFileExt")
    recordDir = parser.get("camera", "recordDir")
    detectType = parser.get("camera", "detectType")
    mark = parser.getboolean("camera", "mark")
    cascadeFile = parser.get("camera", "cascadeFile")
    # See if we should use MJPEG client
    if urlparse.urlparse(url).scheme == "http":
        mjpeg = True
    else:
        mjpeg = False
    # Init video capture
    if mjpeg:
        # Open MJPEG stream
        socketFile, streamSock, boundary = mjpegclient.open(url, 10)
        # Determine image dimensions
        image = mjpegclient.getFrame(socketFile, boundary)
        frameHeight, frameWidth, unknown = image.shape
    else:
        videoCapture = cv2.VideoCapture(url)
        frameHeight = int(videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frameWidth = int(videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = int(videoCapture.get(cv2.CAP_PROP_FPS))
    logger.info("OpenCV %s" % cv2.__version__)
    logger.info("URL: %s, fps: %d" % (url, fps))
    logger.info("Resolution: %dx%d" % (frameWidth, frameHeight))
    # Make sure we have positive values
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
        frameToCheck = int(fps / 4)
        # 0 means check every frame
        if frameToCheck < 1:
            frameToCheck = 0
        skipCount = 0         
        # Frame buffer, so we can record just before motion starts
        frameBuf = []
        # Buffer one second of video
        frameBufSize = fps
        recording = False
        frameOk = True
        frames = 0
        if detectType.lower() == "f":
            facedet.init(cascadeFile)
        start = time.time()
        # Calculate FPS
        while(frameOk):
            # Used for timestamp in frame buffer and filename
            now = datetime.datetime.now()
            if mjpeg:
                image = mjpegclient.getFrame(socketFile, boundary)
            else:
                frameOk, image = videoCapture.read()
            if frameOk:
                # Calc FPS    
                frames += 1
                curTime = time.time()
                elapse = curTime - start
                # Log FPS
                if elapse >= fpsInterval:
                    start = curTime
                    fps = frames / elapse
                    logger.debug("%3.1f FPS" % fps)
                    frames = 0                
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
                    # Detect motion
                    grayImg, motionPercent, movementLocations = motiondet.detect(resizeImg)
                    # Threshold to trigger motion
                    if motionPercent > 2.0:
                        if not recording:
                            # Construct directory name from recordDir and date
                            fileDir = "%s/%s" % (recordDir, now.strftime("%Y-%m-%d"))
                            # Create dir if it doesn"t exist
                            if not os.path.exists(fileDir):
                                os.makedirs(fileDir)
                            fileName = "%s.%s" % (now.strftime("%H-%M-%S"), recordFileExt)
                            videoWriter = cv2.VideoWriter("%s/%s" % (fileDir, fileName), cv2.VideoWriter_fourcc(fourcc[0], fourcc[1], fourcc[2], fourcc[3]), fps, (frameWidth, frameHeight), True)
                            logger.info("Start recording (%4.2f) %s/%s @ %3.1f FPS" % (motionPercent, fileDir, fileName, fps))
                            peopleFound = False
                            facesFound = False
                            recording = True
                        if mark:
                            # Draw rectangle around found objects
                            markImg(image, movementLocations, widthMultiplier, heightMultiplier, (0, 255, 0), 2)
                        # Detect pedestrians ?
                        if detectType.lower() == "p":
                            roiList, foundLocationsList, foundWeightsList = pedestriandet.detect(movementLocations, resizeImg)
                            if len(foundLocationsList) > 0:
                                peopleFound = True
                                if mark:
                                    for imageRoi, foundLocations, foundWeights in zip(roiList, foundLocationsList, foundWeightsList):
                                        i = 0
                                        for x, y, w, h in foundLocations:
                                            imageRoi2 = imageRoi[y : y + h, x : x + w]
                                            print str(imageRoi2.type)
                                            (x2, y2, w2, h2) = imageRoi2
                                            # Draw rectangle around people
                                            cv2.rectangle(image, (x2 * widthMultiplier, y2 * heightMultiplier),
                                            ((x2 + w2) * widthMultiplier, (y2 + h2) * heightMultiplier), (255, 0, 0), 2)
                                            if x <= 0:
                                                x = 2
                                            if y <= 0:
                                                y = 7
                                            # Print weight
                                            cv2.putText(image, "%1.2f" % foundWeights[i], (x2 * widthMultiplier, y2 * heightMultiplier - 4), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), thickness=2, lineType=cv2.LINE_AA)
                                            i += 1
                                logger.debug("People detected locations: %s" % (foundLocationsList))
                        # Face detection?
                        elif detectType.lower() == "f":
                            foundLocationsList = facedet.detect(movementLocations, grayImg)
                            if len(foundLocationsList) > 0:
                                facesFound = True
                                if mark:
                                    for foundLocations in foundLocationsList:
                                        for x, y, w, h in foundLocations:
                                            imageRoi = image[y * heightMultiplier:y * heightMultiplier + (h * heightMultiplier), x * widthMultiplier:x * widthMultiplier + (w * widthMultiplier)]
                                            # Draw rectangle around faces
                                            cv2.rectangle(imageRoi, (x * widthMultiplier, y * heightMultiplier),
                                            ((x + w) * widthMultiplier, (y + h) * heightMultiplier), (255, 0, 0), 2)
                                logger.debug("Face detected locations: %s" % (foundLocationsList))
                else:
                    skipCount -= 1
            # If recording write frame and check motion percent
            if recording:
                # Write first image in buffer (the oldest)
                if frameOk:
                    videoWriter.write(frameBuf[0][0])
                # Threshold to stop recording
                if motionPercent <= 0.25 or not frameOk:
                    logger.info("Stop recording")
                    del videoWriter
                    # Rename video to show people found
                    if peopleFound:
                        os.rename("%s/%s" % (fileDir, fileName), "%s/people-%s" % (fileDir, fileName))
                    elif facesFound:
                        os.rename("%s/%s" % (fileDir, fileName), "%s/faces-%s" % (fileDir, fileName))
                    recording = False
        elapsed = time.time() - start
        # Clean up
        if mjpeg:
            socketFile.close()
            streamSock.close()
        else:
            del videoCapture

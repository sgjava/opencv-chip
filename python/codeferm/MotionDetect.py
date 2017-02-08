"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 4, 2017
sgoldsmith@codeferm.com
"""

"""Motion detector.

Resizes frame, sampling and use moving average to determine change percent. Inner
rectangles are filtered out as well. This can result in better performance and
a more stable ROI.

A frame buffer is used to record 1 second before motion threshold is triggered.

sys.argv[1] = url or will default to "http://localhost:8080/?action=stream" if no args passed.
sys.argv[2] = frames to capture, int or will default to "200" if no args passed.
sys.argv[3] = fourcc, string or will default to "XVID" if no args passed.
sys.argv[4] = frames per second for writer, int or will default to 5 if no args passed.
sys.argv[5] = recording dir, string or will default to "motion" if no args passed.

@author: sgoldsmith

"""

import logging, sys, os, time, datetime, numpy, cv2, mjpegclient, motiondet

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
    # Open MJPEG stream
    socketFile, streamSock, boundary = mjpegclient.open(url, 10)
    # Determine image dimensions
    image = mjpegclient.getFrame(socketFile, boundary)
    frameHeight, frameWidth, unknown = image.shape
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
        frameToCheck = int(fps / 3)
        # 0 means check every frame
        if frameToCheck < 1:
            frameToCheck = 0
        skipCount = 0         
        framesLeft = frames
        movementLocations = []
        # Frame buffer, so we can record just before motion starts
        frameBuf = []
        # Buffer one second of video
        frameBufSize = fps
        recording = False
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
                motionPercent, movementLocationsFiltered = motiondet.detect(resizeImg)
                # Threshold to trigger motion
                if motionPercent > 2.0:
                    if not recording:
                        # Construct directory name from recordDir and date
                        fileDir = "%s%s%s%s%s%s" % (recordDir, os.sep, "motion-detect", os.sep, now.strftime("%Y-%m-%d"), os.sep)
                        # Create dir if it doesn"t exist
                        if not os.path.exists(fileDir):
                            os.makedirs(fileDir)
                        fileName = "%s.%s" % (now.strftime("%H-%M-%S"), "avi")
                        videoWriter = cv2.VideoWriter("%s/%s" % (fileDir, fileName), cv2.VideoWriter_fourcc(fourcc[0], fourcc[1], fourcc[2], fourcc[3]), fps, (frameWidth, frameHeight), True)
                        logger.info("Start recording (%4.2f) %s%s @ %3.1f FPS" % (motionPercent, fileDir, fileName, fps))
                        recording = True
                    for x, y, w, h in movementLocationsFiltered:
                        cv2.putText(image, "%dw x %dh" % (w, h), (x * widthMultiplier, (y * heightMultiplier) - 4), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), thickness=2, lineType=cv2.LINE_AA)
                        # Draw rectangle around found objects
                        cv2.rectangle(image, (x * widthMultiplier, y * heightMultiplier),
                                      ((x + w) * widthMultiplier, (y + h) * heightMultiplier),
                                      (0, 255, 0), 2)
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
                    recording = False
            framesLeft -= 1
        elapsed = time.time() - start
        fps = frames / elapsed
        logger.info("Calculated %4.1f FPS, elapsed time: %4.2f seconds" % (fps, elapsed))
        socketFile.close()
        streamSock.close()

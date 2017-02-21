"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 8, 2017
sgoldsmith@codeferm.com
"""

"""Motion detector using moving average.

@author: sgoldsmith

"""

import numpy, cv2

movingAvgImg = None

def inside(r, q):
    """See if one rectangle inside another"""
    rx, ry, rw, rh = r
    qx, qy, qw, qh = q
    return rx > qx and ry > qy and rx + rw < qx + qw and ry + rh < qy + qh

def contours(image, dilateAmount, erodeAmount):
    """Return contours"""
    # The background (bright) dilates around the black regions of frame
    image = cv2.dilate(image, None, iterations=dilateAmount);
    # The bright areas of the image (the background, apparently), get thinner, whereas the dark zones bigger
    image = cv2.erode(image, None, iterations=erodeAmount);
    # Find contours
    image, contours, heirarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # Add objects with motion
    movementLocations = []
    for contour in contours:
        rect = cv2.boundingRect(contour)
        movementLocations.append(rect)
    return movementLocations

def detect(image, kSize, alpha, blackThreshold, maxChange, dilateAmount, erodeAmount):
    """Detect motion"""
    global movingAvgImg
    movementLocationsFiltered = []
    # Generate work image by blurring
    workImg = cv2.blur(image, kSize)
    # Generate moving average image if needed
    if movingAvgImg is None:
        movingAvgImg = numpy.float32(workImg)
    # Generate moving average image
    cv2.accumulateWeighted(workImg, movingAvgImg, alpha)
    diffImg = cv2.absdiff(workImg, cv2.convertScaleAbs(movingAvgImg))
    # Convert to grayscale
    grayImg = cv2.cvtColor(diffImg, cv2.COLOR_BGR2GRAY)
    # Convert to BW
    ret, bwImg = cv2.threshold(grayImg, blackThreshold, 255, cv2.THRESH_BINARY)
    # Total number of changed motion pixels
    height, width, unknown = image.shape
    motionPercent = 100.0 * cv2.countNonZero(bwImg) / (width * height)
    # Detect if camera is adjusting and reset reference if more than threshold
    if motionPercent > maxChange:
        movingAvgImg = numpy.float32(workImg)
    movementLocations = contours(bwImg, dilateAmount, erodeAmount)
    # Filter out inside rectangles
    for ri, r in enumerate(movementLocations):
        for qi, q in enumerate(movementLocations):
            if ri != qi and inside(r, q):
                break
        else:
            rx, ry, rw, rh = r
            regPercent = ((rw * rh) / (width * height)) * 100.0
            # Toss rectangles >= maxChange percent of total frame
            if regPercent < maxChange :
                movementLocationsFiltered.append(r)
    return grayImg, motionPercent, movementLocationsFiltered

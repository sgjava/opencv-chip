"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 8, 2017
sgoldsmith@codeferm.com
"""

"""Motion detector.

@author: sgoldsmith

"""

import numpy, cv2

def inside(r, q):
    """See if one rectangle inside another"""
    rx, ry, rw, rh = r
    qx, qy, qw, qh = q
    return rx > qx and ry > qy and rx + rw < qx + qw and ry + rh < qy + qh

def contours(image):
    """Return contours"""
    # The background (bright) dilates around the black regions of frame
    source = cv2.dilate(image, None, iterations=15);
    # The bright areas of the image (the background, apparently), get thinner, whereas the dark zones bigger
    source = cv2.erode(image, None, iterations=10);
    # Find contours
    image, contours, heirarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # Add objects with motion
    movementLocations = []
    for contour in contours:
        rect = cv2.boundingRect(contour)
        movementLocations.append(rect)
    return movementLocations

def detect(image, movingAvgImg):
    """Detect motion"""
    # Generate work image by blurring
    workImg = cv2.blur(image, (8, 8))
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
    height, width, unknown = image.shape
    motionPercent = 100.0 * cv2.countNonZero(grayImg) / (width * height)
    # Detect if camera is adjusting and reset reference if more than threshold
    if motionPercent > 25.0:
        movingAvgImg = numpy.float32(workImg)
    movementLocations = contours(grayImg)
    # Filter out inside rectangles
    movementLocationsFiltered = []
    for ri, r in enumerate(movementLocations):
        for qi, q in enumerate(movementLocations):
            if ri != qi and inside(r, q):
                break
        else:
            movementLocationsFiltered.append(r)
    return movingAvgImg, motionPercent, movementLocationsFiltered

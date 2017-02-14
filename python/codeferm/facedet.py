"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 13, 2017
sgoldsmith@codeferm.com
"""

"""Face detector using ROI.

@author: sgoldsmith

"""

import cv2

faceCascade = None

def init(fileName):
    global faceCascade
    faceCascade = cv2.CascadeClassifier(fileName)

def detect(locations, image):
    """Check ROI for faces"""
    global faceCascade
    foundLocationsList = []
    for x, y, w, h in locations:
        # Make sure ROI is big enough for detector
        if w > 16 and h > 16:
            # Image should be gray scale
            imageRoi = image[y:y + h, x:x + w]
            foundLocations = faceCascade.detectMultiScale(imageRoi, 1.3, 5)
            if len(foundLocations) > 0:
                foundLocationsList.append(foundLocations)
    return foundLocationsList

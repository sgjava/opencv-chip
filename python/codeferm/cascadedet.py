"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 13, 2017
sgoldsmith@codeferm.com
"""

"""Cascade classifier detector using ROI.

@author: sgoldsmith

"""

import cv2

cascade = None

def init(fileName):
    global cascade
    cascade = cv2.CascadeClassifier(fileName)

def detect(locations, image, scaleFactor, minNeighbors, minWidth, minHeight):
    """Cascade detect ROI"""
    global cascade
    locationsList = []
    foundLocationsList = []
    for x, y, w, h in locations:
        # Make sure ROI is big enough for detector
        if w > minWidth and h > minHeight:
            # Image should be gray scale
            imageRoi = image[y:y + h, x:x + w]
            foundLocations = cascade.detectMultiScale(imageRoi, scaleFactor, minNeighbors)
            if len(foundLocations) > 0:
                locationsList.append((x, y, w, h))
                foundLocationsList.append(foundLocations)
    return locationsList, foundLocationsList

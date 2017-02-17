"""
Copyright (c) Steven P. Goldsmith. All rights reserved.

Created by Steven P. Goldsmith on February 8, 2017
sgoldsmith@codeferm.com
"""

"""Pedestrian detector using ROI.

Histogram of Oriented Gradients ([Dalal2005]) object detector is used.

@author: sgoldsmith

"""

import cv2

# Initialize HOG
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

def detect(locations, image, winStride, padding, scale0):
    """Check ROI for pedestrians"""
    global hog
    locationsList = []
    foundLocationsList = []
    foundWeightsList = []
    for x, y, w, h in locations:
        # Make sure ROI is big enough for detector
        if w > 63 and h > 127:
            imageRoi = image[y:y + h, x:x + w]
            foundLocations, foundWeights = hog.detectMultiScale(imageRoi, winStride=winStride, padding=padding, scale=scale0)
            if len(foundLocations) > 0:
                locationsList.append((x, y, w, h))
                foundLocationsList.append(foundLocations)
                foundWeightsList.append(foundWeights)
    return locationsList, foundLocationsList, foundWeightsList

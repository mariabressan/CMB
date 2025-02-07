# !/usr/bin/env python
# title           :BasicReadout.py
# description     :This file reads data fro multimeter and writes to a file in disk
# author          :Adriana Perez Rotondo
# date            :2016/11/11
# version         :0.1
# usage           :python BasicReadout.py
# notes           :
# python_version  :2.7.10
# ==============================================================================

import Readout
import time
import numpy as np
import os
from ProgressBar import printProgress

# =========
# Presets
# =========

# Duration of the read
duration = 1*30

# Set the path and name for the file where the data will be wirtten
# the file name will be of the form: path+"%Y-%m-%d_%H:%M:%S"+extension
# e.g "./Data/2016-11-10_10:20:50_Readout.txt"
# the extension must be a .txt file
path = "./Data/BW"
extension = "_LCal2_BNC.txt"

calibrator_boolean = 0
if calibrator_boolean:
    # where the horn was pointing
    looking = "Calibrator paddle"
    # was the calibrator in front
    calibrator = "YES"
else:
    looking = "Sky"
    calibrator = "NO"

# Set heading information
date = time.strftime("%Y-%m-%d_%H:%M:%S")
# angle of the horn form the horizontal perp to support axis
angle_perp = "48.70"
# angle of the horn form the horizontal along the support axis
angle_par = "0"
# temperatures
temperatureOutside = "25.4"
temperatureCalibrator = "Low"
weather = "very clear"
duration_str = str(duration)
units = "Volts"
#
# ===========
# Read Data
# ===========

# Create a new multimeter of the class Readout to read data
multimeter = Readout.Readout()

# printProgress(0, 10, prefix='Progress writing data:', suffix='Complete', barLength=50)

# Read for the duration set
data = multimeter.read_loop(duration)
#read = np.random.rand(10)

# printProgress(7, 10, prefix='Progress writing data:', suffix='Complete', barLength=50)
# ============
# Write Data
# ============

title = path + date + extension

# Create header for the file with all the information
# The header has 8 lines all satrting with #
header = "{0}\nDuration (in s): {7}" \
         "\nPointing Position of the Horn: {1}" \
         "\nAngle pointing (from horizontal perpendicular to supporting axis): {2}" \
         "\nAngle pointing (from horizontal parallel to supporting axis): {8}" \
         "\nCalibrator used: {3}" \
         "\nTemperature Outside (in celcius): {4}" \
         "\nTemperature of the calibrator (in celcius): {5}" \
         "\nWeather: {6}" \
         "\nUnits: {9}".format(
            title, looking, angle_perp, calibrator, temperatureOutside, temperatureCalibrator, weather, duration_str, angle_par, units)

np.savetxt(title, data, header=header)
# printProgress(10, 10, prefix='Progress writing data:', suffix='Complete', barLength=50)
print('\a')

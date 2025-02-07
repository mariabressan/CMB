#!/usr/bin/env python3
# title           :Readout.py
# description     :This file creates a class for a Agilent 34405A 5 1/2 Digit Multimeter
# author          :Adriana Perez Rotondo
# date            :2016/11/11
# version         :0.1
# usage           :import Readout
#                  r = Readout.Readout()
# notes           :
# python_version  :3.x
# ==============================================================================
"""This code creates a class for a Agilent 34405A 5 1/2 Digit Multimeter
and basic functions to read from the multimeter"""

import numpy as np
import time
import pyvisa
from ProgressBar import printProgress


class Readout():
    """This class creates a connection with the multimeter and has methods to read data from it"""

    def __init__(self):
        self.rm = pyvisa.ResourceManager()  # Correct the module name for Python 3
        self.multimeter = self.rm.open_resource('USB0::0x0957::0x0618::MY52210065::INSTR')
        # configure multimeter
        self.multimeter.write("CONF:VOLT:DC:RANG 1")
        return

    def close(self):
        self.rm.close()

    def trigger(self, trigger_mode):
        # trigger multimeter with specific mode
        self.multimeter.write("TRIG:SOUR " + trigger_mode)
        return

    def read_loop(self, duration):
        """Reads from multimeter for a given duration and returns an array with the time and value read for all readings

            Usually around 8 values are read per second

            :param duration: duration in seconds of the read
            :return: data read in array with time in seconds since the epoch and value read
        """
        # Trigger "IMM"
        self.trigger("IMM")
        data = []
        t = []
        t1 = time.time()            # start time
        i = 0
        while time.time() - t1 <= duration:
            if (int(time.time()) - int(t1)) % 10 == 0:
                i += 1
                printProgress(i, duration, prefix='Progress reading data:', suffix='Complete', barLength=100)
            t.append(time.time() - t1)  # Changed from time.time()
            data.append(self.read())
        # when reading ends, set trigger to "BUS"
        self.trigger("BUS")
        combined_data = np.column_stack((t, data))
        return combined_data

    def read(self):
        """ reads from multimeter and returns the data read
        -**return** and **return types**
            :return: returns the read data
        """
        # read from multimeter (automatically switches mode to "IMM")
        return self.multimeter.query_ascii_values("READ?")[0]

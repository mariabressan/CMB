import sys
import numpy as np
import time
import os

try:
    import pyvisa  
    HAS_PYVISA = True
except ImportError:
    HAS_PYVISA = False  

# ==============================
#       HEADER CONSTANTS
# ==============================
DATA_DIR = "./Data/"
UNITS = "Volts"
TEMP_OUTSIDE = "2" # Temperature in Celsius
WEATHER = "very clear" # Weather conditions
AZIMUTH_ANGLE = "0.00" # Angle from North
DURATION = 30 # How many seconds to collect data for 
CALLIBRATING = None # True if calibrating, False if not, or None to prompt user 

HEADER_TEMPLATE = """{0}
Duration (in s): {6}
Calibrating: {2}
Temperature of the calibrator (in Celsius): {4}
Azimuth angle from North: {1}
Altitude angle from the horizon: {7}
Temperature Outside (in Celsius): {3}
Weather: {7}
Units: {8}

Time (s), Voltage (V)"""

# ==============================
#       READOUT CLASS
# ==============================

class Readout():
    """Class for interfacing with an Agilent 34405A 5 1/2 Digit Multimeter."""

    def __init__(self, use_mock=None, data_dir=DATA_DIR):
        """Initialize the Readout class.

        :param use_mock: If None, auto-detect. If True, force mock mode. If False, force real mode.
        :param data_dir: Directory where output data will be saved.
        """
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)  

        self.date = time.strftime("%Y-%m-%d_%H:%M:%S")  
        self.filename = None  
        self.units = UNITS

        if use_mock is None:
            if HAS_PYVISA:
                self.use_mock = False  
                print("✅ Running in REAL mode: Multimeter connected.")
            else:
                response = input("⚠️ `pyvisa` not found. Run in mock mode? [y/n]: ").strip().lower()
                if response == "y":
                    self.use_mock = True
                else:
                    print("❌ Exiting. Please install `pyvisa` to use real hardware.")
                    sys.exit(1)
        else:
            self.use_mock = use_mock

        if not self.use_mock:
            self.rm = pyvisa.ResourceManager()
            self.multimeter = self.rm.open_resource('USB0::0x0957::0x0618::MY52210065::INSTR')
            self.multimeter.write("CONF:VOLT:DC:RANG 1")  
        else:
            print("✅ Running in MOCK mode: No hardware connected.")
            self.azimuth_angle = np.nan  
            self.elevation_angle = np.nan  

    def set_experiment_info(self):
        """Gathers user input for experiment metadata."""
        self.run_name = input("Enter the run name: ")

        if not self.use_mock:
            self.azimuth_angle = AZIMUTH_ANGLE
            self.elevation_angle = input("Enter the elevation angle from the horizon: ")
        else:
            self.azimuth_angle, self.elevation_angle = np.nan, np.nan 
        
        if type(CALLIBRATING) != bool:
            self.calibrating = input("Are you calibrating the multimeter? [y/n]: ").strip().lower() == "y"
        else:
            self.calibrating = CALLIBRATING
        if self.calibrating:
            self.temperatureCalibrator = input("Enter the temperature of the calibrator (in Celsius): ")
        else:
            self.temperatureCalibrator = np.nan
        self.temperatureOutside = TEMP_OUTSIDE
        self.weather = WEATHER
        self.duration = DURATION
        self.filename = os.path.join(self.data_dir, self.date + self.run_name + ".txt")

    def close(self):
        """Close the connection (only applies if using real hardware)."""
        if not self.use_mock:
            self.rm.close()

    def trigger(self, trigger_mode):
        """Trigger the multimeter (only applies in real mode)."""
        if not self.use_mock:
            self.multimeter.write(f"TRIG:SOUR {trigger_mode}")

    def read_loop(self):
        """Reads from the multimeter (or mock data) for a given duration.

        :param duration: Duration in seconds for data collection.
        :return: NumPy array with time (s) and voltage (V).
        """
        if not self.use_mock:
            self.trigger("IMM")  

        data = []
        t = []
        start_time = time.time()
        last_update = start_time

        self.prefix = f"Reading Data for {self.duration} s:"
        self.printProgress(0, self.duration, prefix=self.prefix, suffix="Complete", barLength=50)

        while True:
            elapsed_time = time.time() - start_time

            if elapsed_time >= self.duration:
                break  

            if time.time() - last_update >= 0.1:
                self.printProgress(elapsed_time, self.duration, prefix=self.prefix, suffix="Complete", barLength=50)
                last_update = time.time()

            t.append(elapsed_time)
            data.append(self.read())

        self.printProgress(self.duration, self.duration, prefix=self.prefix, suffix="Complete", barLength=50)

        if not self.use_mock:
            self.trigger("BUS")  

        return np.column_stack((t, data))

    def read(self):
        """Reads voltage data from the multimeter (or generates mock data)."""
        if self.use_mock:
            time.sleep(0.1)
            return np.random.uniform(0, 5)  
        else:
            return self.multimeter.query_ascii_values("READ?")[0]

    def save_data(self, data):
        """Saves the collected data to a CSV or TXT file.

        :param data: NumPy array with columns (time, voltage).
        """
        header = HEADER_TEMPLATE.format(
            self.filename, self.azimuth_angle, self.calibrating, 
            self.temperatureOutside, self.temperatureCalibrator, self.weather, 
            self.duration, self.elevation_angle, self.units
        )

        np.savetxt(self.filename, data, header=header, delimiter=",", comments="")
        print(f"✅ Data saved to {self.filename}")

    @staticmethod
    def printProgress(iteration, total, prefix='', suffix='', decimals=1, barLength=50):
        """Displays a terminal progress bar."""
        if total == 0:
            return  
        
        percent = f"{100 * (iteration / total):.{decimals}f}"
        filled_length = int(barLength * iteration / total)
        bar = "#" * filled_length + "-" * (barLength - filled_length)

        sys.stdout.write(f"\r{prefix} |{bar}| {percent}% {suffix}")
        sys.stdout.flush()

        if iteration >= total:
            sys.stdout.write("\n")


# ==============================
#        MAIN EXECUTION
# ==============================
if __name__ == "__main__":
    multimeter = Readout()
    multimeter.set_experiment_info()  

    data = multimeter.read_loop()  

    multimeter.save_data(data)  

    print('\a')  

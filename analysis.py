import numpy as np
import glob
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def read_data_file(filename):
    """Reads a data file and extracts angle, voltage, and calibration status."""
    angle = None
    voltage_values = []
    calibrating = False
    temperature_outside = None  # Used for calibration files
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("Calibrating:"):
                calibrating = line.split(":")[1].strip() == "True"
            elif line.startswith("Temperature of the calibrator (in Celsius):"):
                temperature_outside = float(line.split(":")[1].strip())
            elif line.startswith("Altitude angle from the horizon:"):
                angle = float(line.split(":")[1].strip())
            elif not line.startswith("#") and not line.startswith("Time"):  # Data section
                parts = line.split(",")
                if len(parts) == 2:
                    try:
                        voltage_values.append(float(parts[1]))  # Extract Voltage
                    except ValueError:
                        print(f"Skipping invalid line in {filename}: {line}")

    avg_voltage = np.mean(voltage_values) if voltage_values else None
    return calibrating, temperature_outside, angle, avg_voltage

def calibrate_temperature(voltage_hot, voltage_cold, T_hot, T_cold):
    """Finds the linear calibration constants (a, b) for temperature conversion."""
    a = (T_hot - T_cold) / (voltage_hot - voltage_cold)
    b = T_hot - a * voltage_hot
    return a, b

def convert_voltage_to_temperature(voltage, a, b):
    """Converts voltage to temperature using the calibration constants."""
    return a * voltage + b

def fit_cmb_temperature(angles, temperatures):
    """Fits the observed temperature model to estimate T_cmb."""
    def temperature_model(sin_theta, T_cmb, T_vertical):
        return T_cmb + T_vertical / sin_theta

    sin_thetas = np.sin(np.radians(angles))
    popt, _ = curve_fit(temperature_model, sin_thetas, temperatures, p0=[2.7, 10])
    
    return popt[0], popt[1]  # T_cmb, T_vertical

def plot_cmb_estimate(filenames):
    """Processes calibration and skydip test data, applies calibration, and fits T_cmb."""
    calibration_files = []
    skydip_files = []
    
    # Sort files into calibration and skydip tests
    for file in filenames:
        calibrating, calib_temp, angle, avg_voltage = read_data_file(file)
        print(f"{file}: {calibrating=}, {calib_temp=}, {angle=}, {avg_voltage=}")
        if calibrating:
            calibration_files.append((calib_temp, avg_voltage))
        else:
            skydip_files.append((angle-90, avg_voltage))
    
    if len(calibration_files) < 2:
        raise ValueError("Need at least two calibration files (hot and cold) to calibrate.")

    # Identify hot and cold calibration points
    calibration_files.sort()  # Sort by temperature (cold first)
    (T_cold, voltage_cold), (T_hot, voltage_hot) = calibration_files[:2]
    print(f"Calibration Points: Cold ({T_cold} K, {voltage_cold} V), Hot ({T_hot} K, {voltage_hot} V)")

    # Compute calibration parameters
    a, b = calibrate_temperature(voltage_hot, voltage_cold, T_hot, T_cold)

    # Process skydip test data
    angles, voltages = zip(*skydip_files)
    temperatures = [convert_voltage_to_temperature(v, a, b) for v in voltages]

    # Fit T_cmb model
    T_cmb, T_vertical = fit_cmb_temperature(angles, temperatures)

    # Plot
    sin_thetas = np.sin(np.radians(angles))
    plt.scatter(sin_thetas, temperatures, label="Observed Data", color="blue")
    
    sin_fit = np.linspace(0.1, 1, 100)  # Avoid division by zero
    plt.plot(sin_fit, T_cmb + T_vertical / sin_fit, 'r--', label=f"Fit: T_cmb={T_cmb:.2f}K")

    plt.xlabel(r"$\sin(\theta)$")
    plt.ylabel("Observed Temperature (K)")
    plt.title("CMB Temperature Estimation with Calibration")
    plt.legend()
    plt.grid()
    plt.show()

    print(f"Estimated CMB Temperature: {T_cmb:.2f} K")
    print(f"Estimated Vertical Temperature Contribution: {T_vertical:.2f} K")
    print(f"Calibration: T = {a:.3f} * Voltage + {b:.3f}")


filenames = glob.glob("./Data/*.txt")
plot_cmb_estimate(filenames)

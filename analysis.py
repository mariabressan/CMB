import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def read_data_file(filename):
    """Reads a single data file and extracts the angle and voltage values."""
    angle = None
    voltage_values = []
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                if "Angle pointing (from horizontal parallel to supporting axis):" in line:
                    angle = float(line.split(":")[1].strip())
            elif line:
                parts = line.split()
                if len(parts) >= 2:
                    voltage_values.append(float(parts[1]))
    
    if angle is None:
        raise ValueError(f"Could not find angle in file: {filename}")
    
    return angle, np.mean(voltage_values)

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

def plot_cmb_estimate(filenames, voltage_hot, voltage_cold, T_hot=275.15, T_cold=77):
    """Reads multiple files, extracts angles and voltages, applies calibration, and fits T_cmb."""
    angles = []
    voltages = []

    for file in filenames:
        print(file)
        angle, avg_voltage = read_data_file(file)
        angles.append(angle-90)
        voltages.append(avg_voltage)

    # Calibration
    a, b = calibrate_temperature(voltage_hot, voltage_cold, T_hot, T_cold)
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

# Example usage:
# filenames = ["./Data/file1.txt", "./Data/file2.txt", ...]
# voltage_hot = measured_voltage_at_outside_temperature
# voltage_cold = measured_voltage_at_liquid_nitrogen
# plot_cmb_estimate(filenames, voltage_hot, voltage_cold, T_hot=298.15, T_cold=77)

# Example usage:
if __name__ == "__main__":
    skydip = glob.glob('Data/*sky')
    calib_hot = "Data/BW2025-02-07_15:58:23blackbody_nonitogen"  # "Data/BW2025-02-07_16:21:40calibration2"
    calib_cold = "Data/BW2025-02-07_16:01:05blackbody_withnitrogen" #"Data/BW2025-02-07_16:23:39calibration2"
    voltage_hot = read_data_file(calib_hot)[1].mean()
    voltage_cold = read_data_file(calib_cold)[1].mean()
    outside_temp = 2
    
    plot_cmb_estimate(skydip, voltage_hot, voltage_cold, T_hot=275.15+outside_temp, T_cold=77)


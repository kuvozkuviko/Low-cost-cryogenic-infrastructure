"""
Cryostat Thermal Heat Load Measurement Script
Automates stepping through a sequence of bias currents using a Keysight B2902A SMU,
logs the corresponding voltage/power metrics alongside live temperatures from a 
cryostat log file using Pygtail, and generates a live plot of Temperature vs. Power.
"""

import sys
# Add custom directory path for local laboratory instrument scripts
sys.path.append('/Users/photonspotaqua/src/EPFLCryoTestingScripts')

import time
import datetime
import csv
import random
import matplotlib
# Force interactive GUI rendering backend for real-time plot tracking
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

# Custom library imports for instrument communication and log tailing
from snspd_measure.inst.keysightB2902A import keysightB2902A
from pygtail import Pygtail

fake_cryostat = False  # Simulate temperature readings if cryostat software is offline
fake_SMU = False       # Simulate voltage readouts without hardware attached

# Array of target bias currents to source through the heater element
I = [0.5e-3, 0.8e-3, 1e-3, 1.5e-3, 2e-3, 2.5e-3, 3e-3, 4e-3] 
time_per_I = 2 * 60     # Duration in seconds to hold each current step

SMU_channel = 1
SMU_IP = '169.254.5.2'  # Static IP address of the Keysight SMU

# Dynamic log generation using current calendar date
current_day = datetime.datetime.today().strftime('%Y%m%d')
logfile = '/Users/photonspotaqua/PhotonSpotShare/logging/log/{}_log.csv'.format(current_day)
measurement_log = "/Users/photonspotaqua/PhotonSpotShare/logging/log/andres_2_06_log_heatload.csv"

measurement_lag = 120 # Settle time in seconds to allow temperature equalization before reading
measruement_time_limit = True # Set a time limit for the measurement
measurement_time = 60 * 60  # Maximum experiment runtime limit 1 hour
stop = False

# Initialize Log Reader
if fake_cryostat:
    log_obj = None
else:
    # Initialize Pygtail to read and track appending lines from the live cryostat log
    log_obj = Pygtail(logfile)

def get_last_from_log(log_pointer):
    """
    Helper function to continuously iterate to the very end of an 
    actively updating log file and return only the most recent entry.
    """
    if fake_cryostat:
        # Generate simulated 4.2 K nominal stage temperature if flag is active
        sim = f"{4.2 + random.uniform(-0.2, 0.2):.4f}"
        return f"fake_time, fake_data, {sim}"
    else:
        end_f = False
        current_line = ''
        # Exhaust the Pygtail iterator until StopIteration is thrown, isolation the newest line
        while not end_f:
            try:
                current_line = log_pointer.next()
            except StopIteration:
                end_f = True
        return current_line


# Establish connection via VISA interface and run safe default resets
source = keysightB2902A(SMU_IP)
source.connect_inst()

# Configure 4-wire (Kelvin) sensing mode to eliminate voltage measurement errors from lead resistance
source.configure_measurement_type(SMU_channel, 'fourwire')

# Set up channel 1 to monitor voltage drops while supplying a fixed current
source.set_sense_measurement(SMU_channel, 'VOLT')
source.set_source_mode(SMU_channel, 'CURR', 'FIX')

# Enforce a 10V compliance ceiling to safeguard hardware from voltage spikes if a lead disconnects
source.set_compliance(SMU_channel, 'VOLT', val=10)  

csvfile = open(measurement_log, 'w', newline='')
writer = csv.writer(csvfile)
writer.writerow(['Time [s]', 'T [K]', 'Current [A]', 'Voltage [V]', 'Power [mW]', 'Resistance [Ohm]']) # Construct structural data column headers

plt.ion()  # Engage interactive plotting loop
fig, ax = plt.subplots(figsize=(12,8))
ax.set_xlabel('Temperature [K]', fontsize=14)
ax.set_ylabel('Power [mW]', fontsize=14)
ax.tick_params(axis='both', which='major')
ax.set_title("4 K Stage", fontsize="16")
ax.grid(True)

# Dictionaries to capture and maintain multi-trace step histories
lines = {}
temp_per_step = {}
powers_per_step = {}

time_start = time.time()

# Main measurement loop
try:
    # Safely activate the SMU channel output stage
    source.output_on(SMU_channel)
    
    # Sequential processing over each current value in our sweep profile
    for I_b in I:
        # Calculate expected power at room temperature
        P_mW_expected = (I_b**2) * 1000 * 1000 
        step_label = f"{I_b*1000:.1f} mA"
        
        print(f"Sourcing {step_label}. Expected power: {P_mW_expected:.1f} mW.")
        print("Time [s] | Temperature [K] | Current [mA] | Voltage [V] | Power [mW] | Resistance [Ω]")
        print("==========================================================")
        
        # Adjust the SMU operational output setpoint to the current loop level
        source.set_op_level(SMU_channel, 'CURR', I_b)

        # Allocate empty line handles and storage targets tracking this explicit current step
        lines[step_label], = ax.plot([], [], label=step_label, linewidth=2.5)
        ax.legend(fontsize=12, loc='upper left')
        temp_per_step[step_label] = []
        powers_per_step[step_label] = []

        step_start = time.time()

        # Hold operation for the thermal settle duration before querying values
        time.sleep(measurement_lag)
        timestamp = time.time() - time_start
        
        # Collect the current temperature value from our rolling file log
        line = get_last_from_log(log_obj)
        print(line)
        
        if line == '':
            T = "Error"
        else:
            try:
                parts = line.split(",")
                T = parts[2]  # Isolate column index tracking the target system stage
            except IndexError:
                T = "Error"

        if fake_SMU:
            V = I_b * 1000 + random.uniform(-0.5, 0.5) # Generate random voltages
        else:
            # Command the SMU to capture and return a single precise voltage reading
            V = float(source.read_single_measurement(SMU_channel, 'VOLT'))
            
        # Calculate experimental power ($P = VI$) and resistance values ($R = V/I$)
        P = V * I_b 
        P_mw = P * 1000
        R = V / I_b

        # Flush data values down to the file line to guarantee persistent saving
        writer.writerow([format(timestamp, ".1f"), T, I_b, V, P_mw, R])
        csvfile.flush()

        # Dynamic Graph Updating Layout
        if T != "Error":
            try:
                T = float(T)

                # Store validated scalar values in the current step tracking arrays
                temp_per_step[step_label].append(T)
                powers_per_step[step_label].append(P_mw)

                # Map newly acquired indices directly to the graph window traces
                lines[step_label].set_data(temp_per_step[step_label], powers_per_step[step_label])
                ax.relim()
                ax.autoscale_view()
 
            except ValueError:
                pass  # Safely ignore formatting anomalies or invalid sensor strings

        # Pause briefly to allow matplotlib to draw the updated frame
        plt.pause(0.01)

        print(f"{timestamp:8.1f} s  | {T} K | {I_b*1000:.1f} mA  | {V:.6f} V  |  {P*1000:.4f} mW  |  {R:.2f} Ω")

except KeyboardInterrupt:
    print("Stopping acquisition.")

finally:
    # Ensure active current sources are powered down safely to protect the cryostat's internal wiring
    source.output_off(SMU_channel)
    csvfile.close()
    print("Output off. CSV closed.")
    
    # Save a final snapshot of the graph as a PDF
    plt.savefig("/Users/photonspotaqua/PhotonSpotShare/logging/log/andres_2_06_log_thermalload_plot.pdf", format='pdf', dpi=300, bbox_inches='tight')
    
    # Close out continuous refresh loops and render a fixed view window
    plt.ioff()
    plt.show()
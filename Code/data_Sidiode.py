"""
Cryostat Temperature Logging and Real-Time Plotting Script
Reads comma-separated serial data (time_ms, T1, T2) from an Arduino,
logs it to a CSV file, and plots the temperature curves in real-time.
"""

import sys
# Add custom directory to system path to import local modules if needed
sys.path.append('/Users/photonspotaqua/src/EPFLCryoTestingScripts')

import serial
import csv
import matplotlib
# Force matplotlib to use TkAgg backend for interactive GUI rendering
matplotlib.use("TkAgg") 
import matplotlib.pyplot as plt

# Limits
stop_at_time = 24 * 60 * 60  # 24 hours in seconds
stop_at_temp = 1.4           # Lowest temperature the sensor can sense in Kelvin
time_limit = False           # Limit the measurement to 24h
temp_limit = False           # Finish the measurement once 1.4K is reached

times = []
T1_list = []
T2_list = []

# Serial Port Setup
ser = serial.Serial('/dev/cu.usbmodemF0F5BD5263802', 9600) # Change COM port as needed depending on OS and connection
# ser = serial.Serial('/dev/ttyACM0', 9600)  # Alternative Linux port

# Clear junk startup lines already sitting in the buffer from the microcontroller
ser.reset_input_buffer() 

# Create CSV
csvfile = "/Users/photonspotaqua/PhotonSpotShare/logging/log/andres_2_06_log_temperaturereadout_hot.csv"

# Write the header row to the CSV file (using 'a' for append mode)
with open(csvfile, 'a') as write_fn:
    write_fn.write("time [s], T1 [K], T2 [K] \n")

# Matplotlib Figure Setup
plt.ion()  # Turn on interactive mode for real-time plot updates
fig, ax = plt.subplots(figsize=(12,8))

# Initialize empty line objects that will updated with data later
line1, = ax.plot([], [], label='4 K Stage')
line2, = ax.plot([], [], label='40 K Stage')

# Format the plot
ax.set_xlabel('Time [s]', fontsize=14, labelpad=8)
ax.set_ylabel('Temperature [K]', fontsize=14, labelpad=8)
ax.tick_params(axis="both", which="major", width=1, length=4)
ax.legend(fontsize=12)
ax.grid(True)

# Main Acquisition Loop
try: 
    # Keep logging until a limit is hit or the user presses CTRL+C
    while True:
        print("waiting for this line")
        
        # Read a line from the serial port, decode from bytes to string, and remove whitespace
        line = ser.readline().decode().strip()
        print(f"got {line}")

        try:
            # Parse the incoming data: expected format is "time_ms, T1, T2"
            variables = line.split(',')
            
            # Skip this loop iteration if the data is malformed (missing columns)
            if len(variables) != 3:
                continue
                
            # Convert values to floats and convert time from milliseconds to seconds
            time_s = float(variables[0]) / 1000.0
            T1 = float(variables[1])
            T2 = float(variables[2])

            # Ignore invalid physical readings (e.g., disconnected sensors reading zero or negative)
            if T1 < 0 or T1 > 600:
                continue
            if T2 < 0 or T2 > 600:
                continue

            # Stop Conditions
            if time_limit and time_s >= stop_at_time:
                print("24h time limit reached")
                break

            if temp_limit and T1 < stop_at_temp and T2 < stop_at_temp:
                print("1.4 K temperature limit reached for both sensors")
                break

            # Append the validated data to the CSV file
            with open(csvfile, 'a') as write_fn:
                write_fn.write("{}, {}, {} \n".format(time_s, T1, T2))

            # Store data in memory for plotting
            times.append(time_s)
            T1_list.append(T1)
            T2_list.append(T2)

            # Update the line objects with the new arrays
            line1.set_data(times, T1_list)
            line2.set_data(times, T2_list)
            
            # Recalculate plot limits so the new data fits inside the window
            ax.relim()
            ax.autoscale_view()
            
            # Pause briefly to allow matplotlib to draw the updated frame
            plt.pause(0.01)

        except Exception as e:
            # Catch parsing errors (like strings where floats should be) so the script doesn't crash
            print("Parse error:", e)

except KeyboardInterrupt:
    # Handle the user stopping the script via the terminal
    print("Stopping acquisition")

finally:
    # This block always runs, whether the script finishes normally, errors out, or is interrupted
    ser.close()
    print("CSV file and serial connection closed")
    
    # Save a final snapshot of the graph as a PDF
    plt.savefig("/Users/photonspotaqua/PhotonSpotShare/logging/log/andres_2_06_log_temperaturereadout_hot.pdf", format="pdf", dpi=300, bbox_inches="tight")
    
    # Turn off interactive mode and display the final static plot
    plt.ioff()
    plt.show()
"""
Cryostat Temperature Data Plotting Script
Reads log files (.csv) and generates customized dual-trace plots for two runs, one 24 hour
one and one which was done about 30 minutes which lasted a few hours.
Scaled into time: 1000 s and temperature: 25 K intervals.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# skipinitialspace=True handles accidental spaces immediately following commas
df = pd.read_csv("andres_2_06_log_temperaturereadout.csv", skipinitialspace=True) # First measurement
# Direct strip to catch and remove trailing/leading whitespaces from column headers
df.columns = df.columns.str.strip()

df_hot = pd.read_csv("andres_2_06_log_temperaturereadout_hot.csv", skipinitialspace=True) # Second measurment
df_hot.columns = df_hot.columns.str.strip()

# First measurement

time = df["time [s]"]
T1 = df["T1 [K]"]
T2 = df["T2 [K]"]


fig, ax = plt.subplots(figsize=(12, 8))

ax.plot(time, T1, label='4 K Stage', linewidth=2.5)
ax.plot(time, T2, label='40 K Stage', linewidth=2.5)

# Label axes in units of 1000 seconds
ax.set_xlabel('Time [1000 s]', fontsize=14, labelpad=8)
ax.set_ylabel('Temperature [K]', fontsize=14, labelpad=8)

x_tick_step = 5000  # Generate an explicit mark every 5000 seconds
x_max = time.max()
x_ticks = np.arange(0, x_max + x_tick_step, x_tick_step)
ax.set_xticks(x_ticks)
ax.set_xticklabels((x_ticks / 1000).astype(int)) # Divide raw seconds by 1000 so the axis displays compact indices (5, 10, 15)

y_tick_step = 25  # Generate a structural gridline every 25 Kelvin
y_max = max(T1.max(), T2.max())
y_ticks = np.arange(0, y_max + y_tick_step, y_tick_step)
ax.set_yticks(y_ticks)

# Force bounds to lock cleanly onto coordinate (0,0) up to maximum calculated steps
ax.set_xlim(0, x_ticks[-1])   
ax.set_ylim(0, y_ticks[-1])

ax.tick_params(axis="both", which="major", length=8, width=2, labelsize=13, direction="in")
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='lower right', borderaxespad=1.5, fontsize=14)

plt.tight_layout()
fig.savefig("Temperature_readout.pdf", dpi=150, format="pdf")


# Second measurement

time_h = df_hot["time [s]"]
T1_h = df_hot["T1 [K]"]
T2_h = df_hot["T2 [K]"]

fig2, ax2 = plt.subplots(figsize=(12, 8))

ax2.plot(time_h, T1_h, label='4 K Stage', linewidth=2.5)
ax2.plot(time_h, T2_h, label='40 K Stage', linewidth=2.5)
ax2.set_xlabel('Time [1000 s]', fontsize=14, labelpad=8)
ax2.set_ylabel('Temperature [K]', fontsize=14, labelpad=8)

x_max_h = time_h.max()
x_min_h = time_h.min()
x_ticks_h = np.arange(x_min_h, x_max_h + x_tick_step, x_tick_step / 3)
ax2.set_xticks(x_ticks_h)
ax2.set_xticklabels((x_ticks_h / 1000).astype(int))

y_max_h = max(T1_h.max(), T2_h.max())
y_ticks_h = np.arange(0, y_max_h + y_tick_step, y_tick_step)
ax2.set_yticks(y_ticks_h)

ax2.set_xlim(x_min_h, 105 * 1000)
ax2.set_ylim(0, y_ticks_h[-1] + 25)

ax2.tick_params(axis="both", which="major", length=8, width=2, labelsize=13, direction="in")
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='lower right', borderaxespad=1.5, fontsize=14)

fig2.tight_layout()
fig2.savefig("Temperature_readout_hot.pdf", dpi=150, format="pdf")

plt.show()
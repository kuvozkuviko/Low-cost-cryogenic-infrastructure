"""
Cryogenic Heat Load and Resistance Characterization Plotting Script
Processes and compares thermal load data from two experimental runs (coarse and smooth).
Calculates and contrasts measured electrical power dissipation against room 
temperature values and models the data using quadratic polynomial regressions.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Load separate experimental datasets: a coarse sweeping scan and a high-resolution smooth scan
df_coarse = pd.read_csv("andres_2_06_log_heatload_coarse.csv")
df_smooth = pd.read_csv("andres_2_06_log_heatload.csv")
R = 1e3 # Value of the resistor on the PCB

# Calculate the reference power dissipation ($P = I^2 R$) in milliwatts
df_coarse["I2R_mW"] = (df_coarse["Current [A]"]**2) * R * 1000
df_smooth["I2R_mW"]  = (df_smooth["Current [A]"]**2) * R * 1000

# Find the difference between room and cryogenic temperature resistance
df_coarse["diff_mW"] = df_coarse["Power [mW]"] - df_coarse["I2R_mW"]
df_smooth["diff_mW"] = df_smooth["Power [mW]"] - df_smooth["I2R_mW"]

# Calculate uniform X-axis step intervals to split the scale into exactly 17 tick marks
T_max_c = df_coarse["T [K]"].max()
T_max_s = df_smooth["T [K]"].max()
num_ticks = 17
step_c = max(1, round(T_max_c / (num_ticks - 1)))
xticks_c = np.arange(0, step_c * (num_ticks - 1) + 1, step_c)[:num_ticks]
step_s = max(1, round(T_max_s / (num_ticks - 1)))
xticks_s = np.arange(0, step_s * (num_ticks - 1) + 1, step_s)[:num_ticks]


def fmt_poly(coeffs, var='x'):
    """
    Parses polynomial coefficient arrays from numpy regressions into clean, 
    algebraically correct LaTeX strings for mathematical graph text overlays.
    """
    terms = []
    degree = len(coeffs) - 1
    for i, c in enumerate(coeffs):
        if abs(c) < 1e-12:
            continue
        power = degree - i
        if power == 0:
            term = f"{c:.4g}"
        elif power == 1:
            term = f"{c:.4g}{var}"
        else:
            term = f"{c:.4g}{var}^{power}"
        if i == 0:
            terms.append(term)
        else:
            if c >= 0:
                terms.append(f"+ {term}")
            else:
                if term.startswith('-'):
                    terms.append(f"- {term[1:]}")
                else:
                    terms.append(f"+ {term}")
    return ' '.join(terms)

# Construct a custom proxy legend handle (hollow circle) to define the reference I^2R marks
hollow_handle = Line2D([0], [0], marker='o', color='black', markerfacecolor='none', linestyle='None', markersize=8, label='Ref')

# Plot the coarse current sweep
fig1, (ax_c, ax_cd) = plt.subplots(2, 1, figsize=(12, 10))

ax_c.set_title(r"Coarse: Measured Power & $I^2$ 1$k\Omega$", fontsize=14)
ax_c.set_xlabel("Temperature [K]", fontsize=14)
ax_c.set_ylabel("Power [mW]", fontsize=14)
ax_c.tick_params(axis="both", which="major", length=8, width=2, labelsize=12, direction="in")
ax_c.set_xticks(xticks_c)

# Simultaneously plot instrument measurements (solid markers) against computed reference values (hollow boundaries)
for current, group in df_coarse.groupby("Current [A]"):
    scatter = ax_c.scatter(group["T [K]"], group["Power [mW]"], label=f"{current*1000:.1f}", s=60)
    color = scatter.get_facecolors()[0]
    ax_c.scatter(group["T [K]"], group["I2R_mW"], facecolors='none', edgecolors=color, s=60)

# Compute a quadratic (2nd-degree polynomial) fit tracing measured power growth as a function of temperature
z_pow_c = np.polyfit(df_coarse["T [K]"], df_coarse["Power [mW]"], 2)
p_pow_c = np.poly1d(z_pow_c)
T_range_c = np.linspace(df_coarse["T [K]"].min(), df_coarse["T [K]"].max(), 200)
ax_c.plot(T_range_c, p_pow_c(T_range_c), 'k--', label='Fit')

# Append the custom reference proxy handle to the standard dynamic legend
handles, labels = ax_c.get_legend_handles_labels()
handles.append(hollow_handle)
ax_c.legend(ncols=2,handles=handles, title="Current [mA]", fontsize=12, title_fontsize=12)

# Format and embed the mathematical regression equation within the layout bounds
eq_top = f"Fit: $y = {fmt_poly(z_pow_c)}$"
ax_c.text(0.05, 0.95, eq_top, transform=ax_c.transAxes, fontsize=11, verticalalignment='top')
ax_c.set_ylim(0, max(df_coarse["Power [mW]"] + 2.5))

ax_cd.set_title("Coarse: Power Difference (Measured − $I^2$ 1$k\Omega$)", fontsize=14)
ax_cd.set_xlabel("Temperature [K]", fontsize=14)
ax_cd.set_ylabel(r"$\Delta$ Power [mW]", fontsize=14)
ax_cd.tick_params(axis="both", which="major", length=8, width=2, labelsize=12, direction="in")
ax_cd.set_xticks(xticks_c)

for current, group in df_coarse.groupby("Current [A]"):
    ax_cd.scatter(group["T [K]"], group["diff_mW"], label=f"{current*1000:.1f}", s=60)

# Compute a quadratic fit tracing the behavior of the isolated delta power drift
z_diff_c = np.polyfit(df_coarse["T [K]"], df_coarse["diff_mW"], 2)
p_diff_c = np.poly1d(z_diff_c)
ax_cd.plot(T_range_c, p_diff_c(T_range_c), 'k--', label='Fit')

eq_bot = f"Fit: $y = {fmt_poly(z_diff_c)}$"
ax_cd.text(0.05, 0.95, eq_bot, transform=ax_cd.transAxes, fontsize=11, verticalalignment='top')

ax_cd.legend(ncols=2, title="Current [mA]", fontsize=12, title_fontsize=12)
ax_cd.set_ylim(0, max(df_coarse["diff_mW"] + 0.5))

plt.tight_layout()
fig1.savefig("Thermal_load_coarse.pdf", dpi=150, format="pdf")



# Plot smooth current sweep

fig2, (ax_s, ax_sd) = plt.subplots(2, 1, figsize=(12, 10))

ax_s.set_title(r"Smooth: Measured Power & $I^2$ 1$k\Omega$", fontsize=14)
ax_s.set_xlabel("Temperature [K]", fontsize=14)
ax_s.set_ylabel("Power [mW]", fontsize=14)
ax_s.tick_params(axis="both", which="major", length=8, width=2, labelsize=12, direction="in")
ax_s.set_xticks(xticks_s)

# Replicate overlay strategy (solid measurements vs hollow calculations) for the smooth dataset
for current, group in df_smooth.groupby("Current [A]"):
    scatter = ax_s.scatter(group["T [K]"], group["Power [mW]"], label=f"{current*1000:.1f}", s=60)
    color = scatter.get_facecolors()[0]
    ax_s.scatter(group["T [K]"], group["I2R_mW"], facecolors='none', edgecolors=color, s=60)

# Compute quadratic total power regression for the high-resolution run
z_pow_s = np.polyfit(df_smooth["T [K]"], df_smooth["Power [mW]"], 2)
p_pow_s = np.poly1d(z_pow_s)
T_range_s = np.linspace(df_smooth["T [K]"].min(), df_smooth["T [K]"].max(), 200)
ax_s.plot(T_range_s, p_pow_s(T_range_s), 'k--', label='Fit')

handles, labels = ax_s.get_legend_handles_labels()
handles.append(hollow_handle)

eq_top_s = f"Fit: $y = {fmt_poly(z_pow_s)}$"
ax_s.text(0.05, 0.95, eq_top_s, transform=ax_s.transAxes, fontsize=11, verticalalignment='top')

ax_s.legend(ncols=2, handles=handles, title="Current [mA]", fontsize=12, title_fontsize=12)
ax_s.set_ylim(0, max(df_smooth["Power [mW]"] + 2.5))


ax_sd.set_title("Smooth: Power Difference (Measured − $I^2$ 1$k\Omega$)", fontsize=14)
ax_sd.set_xlabel("Temperature [K]", fontsize=14)
ax_sd.set_ylabel("$\Delta$ Power [mW]", fontsize=14)
ax_sd.tick_params(axis="both", which="major", length=8, width=2, labelsize=12, direction="in")
ax_sd.set_xticks(xticks_s)

for current, group in df_smooth.groupby("Current [A]"):
    ax_sd.scatter(group["T [K]"], group["diff_mW"], label=f"{current*1000:.1f}", s=60)

# Compute quadratic load delta regression for the high-resolution run
z_diff_s = np.polyfit(df_smooth["T [K]"], df_smooth["diff_mW"], 2)
p_diff_s = np.poly1d(z_diff_s)
ax_sd.plot(T_range_s, p_diff_s(T_range_s), 'k--', label='Fit')

eq_bot_s = f"Fit: $y = {fmt_poly(z_diff_s)}$"
ax_sd.text(0.05, 0.95, eq_bot_s, transform=ax_sd.transAxes, fontsize=11, verticalalignment='top')
ax_sd.legend(ncols=2, title="Current [mA]", fontsize=12, title_fontsize=12)
ax_sd.set_ylim(0, max(df_smooth["diff_mW"] + 0.5))


plt.tight_layout()
fig2.savefig("Thermal_load_smooth.pdf", dpi=150, format="pdf")


# Plot cryogenic resistance values 

fig3, ax_r = plt.subplots(figsize=(8, 6))
ax_r.set_title("R(T)", fontsize=14)
ax_r.set_xlabel("Temperature [K]", fontsize=14)
ax_r.set_ylabel(r"Resistance $\Omega$", fontsize=14)
ax_r.tick_params(axis="both", which="major", length=8, width=2, labelsize=11, direction="in")

# Consolidate physical resistance data from both runs to contrast tracking matching behavior
scatter_s = ax_r.scatter(df_smooth["T [K]"], df_smooth["Resistance [Ohm]"], label="Smooth", s=70, zorder=5)
scatter_c = ax_r.scatter(df_coarse["T [K]"], df_coarse["Resistance [Ohm]"], label="Coarse", s=70, marker='s', zorder=5)
color_s = scatter_s.get_facecolors()[0]
color_c = scatter_c.get_facecolors()[0]

# Fit independent curves mapping the scaling behaviors of experimental resistance over temperature
z_r_s = np.polyfit(df_smooth["T [K]"], df_smooth["Resistance [Ohm]"], 2)
p_r_s = np.poly1d(z_r_s)
T_range_r_s = np.linspace(df_smooth["T [K]"].min(), df_smooth["T [K]"].max(), 200)
ax_r.plot(T_range_r_s, p_r_s(T_range_r_s), color=color_s, linestyle='--', zorder=4, label="Fit Smooth")

z_r_c = np.polyfit(df_coarse["T [K]"], df_coarse["Resistance [Ohm]"], 2)
p_r_c = np.poly1d(z_r_c)
T_range_r_c = np.linspace(df_coarse["T [K]"].min(), df_coarse["T [K]"].max(), 200)
ax_r.plot(T_range_r_c, p_r_c(T_range_r_c), color=color_c, linestyle='--', zorder=4, label="Fit Coarse")

eq_r_s = f"Smooth Fit: $y = {fmt_poly(z_r_s)}$"
eq_r_c = f"Coarse Fit: $y = {fmt_poly(z_r_c)}$"
ax_r.text(0.05, 0.95, eq_r_s + "\n" + eq_r_c, transform=ax_r.transAxes, fontsize=11, verticalalignment='top')

# Draw an absolute 1000 Ohm horizontal baseline to isolate wire resistance growth from the starting load
ax_r.axhline(1000, color='k', linestyle='-')

# Calculate dynamic integer limits across the unified temperature bounds to set discrete single-Kelvin steps
x_min = min(df_smooth["T [K]"].min(), df_coarse["T [K]"].min())
x_max = max(df_smooth["T [K]"].max(), df_coarse["T [K]"].max())
ax_r.set_xticks(np.arange(np.floor(x_min), np.ceil(x_max) + 1, 1))

ax_r.legend(fontsize=11)
ax_r.set_ylim(1000, 1600)
plt.tight_layout()
fig3.savefig("Cryogenic_resistance.pdf", dpi=150, format="pdf")

plt.show()
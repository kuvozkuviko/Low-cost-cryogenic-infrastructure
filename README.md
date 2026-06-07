# Low-Cost Cryogenic Infrastructure

**EPFL Quantum Science and Engineering — Semester Project 2025–2026**  
**Author:** Andrés Quesnel González  
**Supervisor:** Dr. Gregor Taylor  
**Professor:** Prof. Edoardo Charbon

A low-cost cryogenic temperature readout system based on the Lake Shore Cryotronics DT-670 silicon diode and a thermal load measurement PCB for characterising the heat dissipation of 
cryogenic electronics.

---

## Overview

The system provides a stable 10 µA excitation current to a DT-670 silicon diode, reads the resulting voltage with a 24-bit ADC, converts it to temperature using the manufacturer's calibration 
table, and displays the result on two 7-segment displays. It was validated by monitoring the 4 K and 40 K stages of a Photon Spot Cryospot 4 over 24 hours.

The companion thermal load PCB uses a 1 kΩ thin-film resistor as a controllable heat source to establish a calibration curve of the cryocooler's cooling capacity as a function of temperature. 
This curve can then be used to quantify the thermal impact of any electronics placed inside the cryostat.

---

## Hardware

### Temperature Readout PCB

A custom PCB (60 × 35 mm) that drives a DT-670 silicon diode with a stable 10 µA constant current and reads its voltage response via a 24-bit ADS1220 ADC. 
The converted temperature is shown on two Grove 4-digit 7-segment displays connected to an Arduino UNO R4 WiFi.

**Key components:**

| Component | Part | Purpose |
|---|---|---|
| Voltage shunt regulator | LM4041-N ADJ | Precision 1.225 V reference |
| Transistor array | THAT 320S14-U | PNP current source with thermal compensation |
| Sensing resistor | TNPW0603 66.5 kΩ (0.1%, 10 PPM/°C) | Sets output current to 10 µA |
| ADC | ADS1220 | 24-bit, 596 nV resolution with 5 V reference |
| Voltage regulator | LM78L05 | 5 V regulated supply from 12 V lab rail |
| Microcontroller | Arduino UNO R4 WiFi | Reads ADC via SPI, drives displays |
| Displays | Grove 4-digit 7-segment (TM1637) | Shows temperature in kelvin |
| Connector | L17HTNES4R2C (Amphenol, right-angle DB-9) | Interfaces with cryostat wiring |

**Temperature resolution:**  
20 µK at 4 K · 259 µK at 300 K  
(24-bit ADC at 5 V reference, diode sensitivity from Table 2 of the report)

**Total system cost: CHF 273.26**

### Thermal Load PCB

A minimal PCB (16.24 × 15.26 mm) with a single 1 kΩ thin-film resistor, M3 mounting hole, and 4-pin through-hole connector for 4-wire SMU connection. 
It attaches to the PCB under test on one side and to a copper puck on the other.

---

## Getting Started

### Arduino Firmware

#### Requirements

- Arduino IDE 2.x or later
- Libraries (install via Library Manager):
  - `ADS1220_WE` by Wolfgang Ewald
  - `TM1637Display` by Avishay Orpaz

#### Wiring

| ADS1220 pin | Arduino UNO R4 pin |
|---|---|
| CS | 7 |
| DRDY | 6 |
| SCLK | 13 (SPI SCK) |
| DIN | 11 (SPI MOSI) |
| DOUT | 12 (SPI MISO) |

| Display | CLK | DIO |
|---|---|---|
| Sensor 1 (4 K stage) | 2 | 3 |
| Sensor 2 (40 K stage) | 4 | 5 |

---

### Python — Data Acquisition

Reads the Arduino's serial output and saves it to a CSV file.

#### Requirements

```
pip install pyserial
```

#### Usage

```bash
python code/data_Sidiode.py --port /dev/ttyUSB0 --output CSVs/andres_2_06_log_temperaturereadout.csv
```

Arguments:
- `--port`: Serial port the Arduino is connected to (e.g. `COM3` on Windows, `/dev/ttyACM0` on Linux)
- `--output`: Path to the output CSV file
- `--baud`: Baud rate (default: 9600)

Output CSV format:
```
time_ms, T1_K, T2_K
1204, 3.214823, 32.771456
...
```

---

### Python — Analysis and Plotting

#### Requirements

```
pip install numpy pandas matplotlib scipy
```

#### Temperature curves (RT measurement)

```bash
python Code/Sidiode_plot.py --input CSVs/andres_2_06_log_temperaturereadout.csv
```

Produces a plot of temperature vs time for both stages, equivalent to Figure 8 in the report.

#### Thermal load calibration curves

```bash
python python/analysis/plot_heatload.py \
    --smooth data/heatload_smooth.csv \
    --coarse data/heatload_coarse.csv
```

Produces the three-panel plot (Figure 9 in the report): measured power vs temperature, power difference vs temperature, and cryogenic resistance R(T).

Input CSV format (from the AQUA lab measurement script):
```
Time [s], T [K], Current [A], Voltage [V], Power [mW], Resistance [Ohm]
```

---

## Mechanical

`mechanical/copper_puck.step` is the STEP file for the copper puck used to absorb heat on the back side of the thermal load PCB when it is mounted inside the cryostat. Import into FreeCAD, Fusion 360, or any STEP-compatible CAD tool.

---

## SPICE Simulation

`spice/current_source.asc` is the LTspice XVII simulation of the LM4041-N ADJ constant current source. It was used to verify that the output current is independent of the biasing current and to compare the performance of the 120 kΩ and 122.5 kΩ sensing resistor values.

Open with LTspice XVII (free, from Analog Devices).

---

## Bill of Materials

| Item | Cost (CHF) |
|---|---|
| PCB fabrication (Eurocircuits) | 200.00 |
| Arduino UNO R4 WiFi | 23.70 |
| 2× Grove 7-segment displays | 13.77 |
| Display cables | 1.10 |
| Stripboard | 5.10 |
| Aluminium enclosure (Hammond) | 25.30 |
| **Total** | **269.97** |

*Component costs for resistors, capacitors, ICs, and connectors on the PCB itself are included in the Eurocircuits fabrication quote.*

---

## Known Issues and Future Work

- The 66.5 kΩ sensing resistor was hand-soldered to replace the original 120 kΩ value. The solder joints are visually imperfect and the output current may deviate slightly from the target 10 µA, introducing a small systematic temperature offset.
- The DB-9 connector pin ordering on the original PCB was incorrect and was corrected with a wired adapter. A future PCB revision should use the correct pinout directly.
- The ADS1220 is configured with a 5 V external reference (REFP0 = 5 V), giving 596 nV resolution. Using the internal 2.048 V reference would improve resolution to 244 nV, since the DT-670 voltage never exceeds 1.644 V.
- Two-minute dwell times between thermal load current steps were insufficient for full thermal equilibration. Future measurements should use at least 5 minutes per step.
- The thermal load calibration was performed with the PCB under test powered off. A future measurement with the PCB powered will yield its actual heat dissipation.

---

## Related Files

The full semester project report (`TP4_report.pdf`) is included at the root of this repository and contains the full circuit analysis, component selection rationale, measurement results, and discussion.

---

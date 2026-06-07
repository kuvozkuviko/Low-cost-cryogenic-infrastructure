/*
 *  Hardware:
 *    - ADS1220 24-bit ADC, connected via SPI (J1 on PCB)
 *    - 2× TM1637 4-digit 7-segment displays
 *    - 2× Lakeshore DT-670 silicon diodes via DE-9 connectors
 *      (Pout1: Sense1_V+, Sense1_V-, Sense2_V+, Sense2_V-, GND)
 *
 *  Required libraries:
 *    - "ADS1220_WE" by Wolfgang Ewald
 *    - "TM1637Display" by Avishay Orpaz
 *
 *  Pin assignments:
 *    ADS1220 CS   → Arduino pin 7
 *    ADS1220 DRDY → Arduino pin 6
 *    ADS1220 SCLK → Arduino pin 13 (hardware SPI SCK)
 *    ADS1220 DIN  → Arduino pin 11 (hardware SPI MOSI)
 *    ADS1220 DOUT → Arduino pin 12 (hardware SPI MISO)
 *
 *    Display 1 CLK → Arduino pin 2
 *    Display 1 DIO → Arduino pin 3
 *    Display 2 CLK → Arduino pin 4
 *    Display 2 DIO → Arduino pin 5
 *
 *  ADC channel assignment (verify against schematic):
 *    Sensor 1: AIN0 (Sense1_V+) vs AIN1 (Sense1_V−)  — differential
 *    Sensor 2: AIN2 (Sense2_V+) vs AIN3 (Sense2_V−)  — differential
 *
 *  Display format (Kelvin):
 *    T ≥ 100 K  →  " 300"   (integer, no decimal)
 *    10 ≤ T < 100 K  →  "77.35"   (2 decimal place)
 *    T < 10 K   →  " 4.22"   (2 decimal places)
 *    Out of range   →  "Err "
 */

#include <ADS1220_WE.h>
#include <SPI.h>
#include <TM1637Display.h>
#include <avr/pgmspace.h>

// Pin definitions

#define ADS1220_CS_PIN    7   // ADS1220 chip select (active low)
#define ADS1220_DRDY_PIN 6   // ADS1220 data ready (active low)

#define DISP1_CLK  2          // TM1637 display 1 — Sensor 1
#define DISP1_DIO  3
#define DISP2_CLK  4          // TM1637 display 2 — Sensor 2
#define DISP2_DIO  5

struct TempPoint {
  float voltage;  // Volts
  float temp;     // Kelvin
};

unsigned long time_ms;

// !!!Calibration Table!!!
const TempPoint dt670_table[] PROGMEM = {
  {1.644290f, 1.4f},
  {1.642990f, 1.5f},
  {1.641570f, 1.6f},
  {1.640030f, 1.7f},
  {1.638370f, 1.8f},
  {1.636600f, 1.9f},
  {1.634720f, 2.0f},
  {1.632740f, 2.1f},
  {1.630670f, 2.2f},
  {1.628520f, 2.3f},
  {1.626290f, 2.4f},
  {1.624000f, 2.5f},
  {1.621660f, 2.6f},
  {1.619280f, 2.7f},
  {1.616870f, 2.8f},
  {1.614450f, 2.9f},
  {1.612000f, 3.0f},
  {1.609510f, 3.1f},
  {1.606970f, 3.2f},
  {1.604380f, 3.3f},
  {1.601730f, 3.4f},
  {1.599020f, 3.5f},
  {1.596260f, 3.6f},
  {1.593440f, 3.7f},
  {1.590570f, 3.8f},
  {1.587640f, 3.9f},
  {1.584650f, 4.0f},
  {1.578480f, 4.2f},
  {1.572020f, 4.4f},
  {1.565330f, 4.6f},
  {1.558450f, 4.8f},
  {1.551450f, 5.0f},
  {1.544360f, 5.2f},
  {1.537210f, 5.4f},
  {1.530000f, 5.6f},
  {1.522730f, 5.8f},
  {1.515410f, 6.0f},
  {1.496980f, 6.5f},
  {1.478680f, 7.0f},
  {1.460860f, 7.5f},
  {1.443740f, 8.0f},
  {1.427470f, 8.5f},
  {1.412070f, 9.0f},
  {1.397510f, 9.5f},
  {1.383730f, 10.0f},
  {1.370650f, 10.5f},
  {1.358200f, 11.0f},
  {1.346320f, 11.5f},
  {1.334990f, 12.0f},
  {1.324160f, 12.5f},
  {1.313810f, 13.0f},
  {1.303900f, 13.5f},
  {1.294390f, 14.0f},
  {1.285260f, 14.5f},
  {1.276450f, 15.0f},
  {1.267940f, 15.5f},
  {1.259670f, 16.0f},
  {1.251610f, 16.5f},
  {1.243720f, 17.0f},
  {1.235960f, 17.5f},
  {1.228300f, 18.0f},
  {1.220700f, 18.5f},
  {1.213110f, 19.0f},
  {1.205480f, 19.5f},
  {1.197748f, 20.0f},
  {1.181548f, 21.0f},
  {1.162797f, 22.0f},
  {1.140817f, 23.0f},
  {1.125923f, 24.0f},
  {1.119448f, 25.0f},
  {1.115658f, 26.0f},
  {1.112810f, 27.0f},
  {1.110421f, 28.0f},
  {1.108261f, 29.0f},
  {1.106244f, 30.0f},
  {1.104324f, 31.0f},
  {1.102476f, 32.0f},
  {1.100681f, 33.0f},
  {1.098930f, 34.0f},
  {1.097216f, 35.0f},
  {1.095534f, 36.0f},
  {1.093878f, 37.0f},
  {1.092244f, 38.0f},
  {1.090627f, 39.0f},
  {1.089024f, 40.0f},
  {1.085842f, 42.0f},
  {1.082669f, 44.0f},
  {1.079492f, 46.0f},
  {1.076303f, 48.0f},
  {1.073099f, 50.0f},
  {1.069881f, 52.0f},
  {1.066650f, 54.0f},
  {1.063403f, 56.0f},
  {1.060141f, 58.0f},
  {1.056862f, 60.0f},
  {1.048584f, 65.0f},
  {1.040183f, 70.0f},
  {1.031651f, 75.0f},
  {1.027594f, 77.35f},
  {1.022984f, 80.0f},
  {1.014181f, 85.0f},
  {1.005244f, 90.0f},
  {0.986974f, 100.0f},
  {0.968209f, 110.0f},
  {0.949000f, 120.0f},
  {0.929390f, 130.0f},
  {0.909416f, 140.0f},
  {0.889114f, 150.0f},
  {0.868518f, 160.0f},
  {0.847659f, 170.0f},
  {0.826560f, 180.0f},
  {0.805242f, 190.0f},
  {0.783720f, 200.0f},
  {0.762007f, 210.0f},
  {0.740115f, 220.0f},
  {0.718054f, 230.0f},
  {0.695834f, 240.0f},
  {0.673462f, 250.0f},
  {0.650949f, 260.0f},
  {0.628302f, 270.0f},
  {0.621141f, 273.0f},
  {0.605528f, 280.0f},
  {0.582637f, 290.0f},
  {0.559639f, 300.0f},
  {0.536542f, 310.0f},
  {0.513361f, 320.0f},
  {0.490106f, 330.0f},
  {0.466760f, 340.0f},
  {0.443371f, 350.0f},
  {0.419960f, 360.0f},
  {0.396503f, 370.0f},
  {0.373002f, 380.0f},
  {0.349453f, 390.0f},
  {0.325839f, 400.0f},
  {0.302161f, 410.0f},
  {0.278416f, 420.0f},
  {0.254592f, 430.0f},
  {0.230697f, 440.0f},
  {0.206758f, 450.0f},
  {0.182832f, 460.0f},
  {0.159010f, 470.0f},
  {0.135480f, 480.0f},
  {0.112553f, 490.0f},
  {0.090681f, 500.0f}
};

const int TABLE_SIZE = sizeof(dt670_table) / sizeof(TempPoint);

// !!!Segment patterns!!!

// "Err " — shown when voltage is outside the calibrated range
const uint8_t SEG_ERR[] = {
  SEG_A | SEG_D | SEG_E | SEG_F | SEG_G,  // E
  SEG_E | SEG_G,                           // r
  SEG_E | SEG_G,                           // r
  0x00                                     // (blank)
};

// !!!Object instantiation!!!
ADS1220_WE ads = ADS1220_WE(ADS1220_CS_PIN, ADS1220_DRDY_PIN);
TM1637Display disp1(DISP1_CLK, DISP1_DIO);
TM1637Display disp2(DISP2_CLK, DISP2_DIO);

// !!!Voltage to Temperature conversion!!!

// Linear interpolation between the two nearest table entries.
// Returns temperature in Kelvin, or -1.0 if out of range.
//
// The table is sorted by decreasing voltage, so we search for
// the interval where:  voltage[i] >= measured_V >= voltage[i+1]

float voltageToKelvin(float voltage_V) {
  // Read bounds from PROGMEM
  float v_max = pgm_read_float(&(dt670_table[0].voltage));
  float v_min = pgm_read_float(&(dt670_table[TABLE_SIZE - 1].voltage));

  if (voltage_V > v_max || voltage_V < v_min) {
    return -1.0f;  // voltage out of calibrated range
  }

  for (int i = 0; i < TABLE_SIZE - 1; i++) {
    float v_hi = pgm_read_float(&(dt670_table[i].voltage));
    float v_lo = pgm_read_float(&(dt670_table[i + 1].voltage));

    if (voltage_V <= v_hi && voltage_V >= v_lo) {
      float T_lo = pgm_read_float(&(dt670_table[i].temp));
      float T_hi = pgm_read_float(&(dt670_table[i + 1].temp));

      // Linear interpolation:
      // frac = 0 → v_hi → T_lo (lower temperature)
      // frac = 1 → v_lo → T_hi (higher temperature)
      float frac = (v_hi - voltage_V) / (v_hi - v_lo);
      return T_lo + frac * (T_hi - T_lo);
    }
  }

  return -1.0f;  // should never be reached
}

// !!!Display temperature in Kelvin on a TM1637!!!
//
// TM1637Display dots parameter (avishorp library):
//   0x80 → dot after digit 0 (leftmost)
//   0x40 → dot after digit 1  ← colon on clock displays
//   0x20 → dot after digit 2
//   0x10 → dot after digit 3 (rightmost)
//
// With 0x20 and right-justified numbers:
//   num=773 → [' ']['7']['7']['3'] + dot at pos 2 → " 77.3"
//   num=42  → [' '][' ']['4']['2'] + dot at pos 2 → "  4.2"
//   num=300 → [' ']['3']['0']['0'] no dot          → " 300"

void displayKelvin(TM1637Display& disp, float tempK) {
  if (tempK < 0.0f) {
    // Show "Err " – setSegments expects length and position
    disp.setSegments(SEG_ERR, 4, 0);
    return;
  }

  // Temperatures ≥ 100 K → integer only (no decimal, no colon)
  if (tempK >= 100.0f) {
    int integerPart = (int)(tempK + 0.5f);
    disp.showNumberDec(integerPart, false);  // false = no leading zeros
    return;
  }

  // For T < 100 K: show "AB:CD" using colon between digits 1 & 2
  // Round to two fractional digits, then multiply by 100
  int value = (int)(tempK * 100.0f + 0.5f);
  
  // Display as 4‑digit number with leading zeros, colon mask 0x60
  // 0x60 lights both colon dots (between digit1 and digit2)
  disp.showNumberDecEx(value, 0x60, true, 4, 0);
}


// !!!Setup!!!

void setup() {
  Serial.begin(9600);
  Serial.println(F("DT-670 Cryogenic Temperature Readout"));
  Serial.println(F("EPFL SiDiodeReadout_v1"));
  
  // Initialise TM1637 displays
  disp1.setBrightness(0x0F); // maximum brightness
  disp2.setBrightness(0x0F);
  
  // Power-on self-test: all segments on for 1 second
  disp1.showNumberDecEx(8888, 0xFF, true);
  disp2.showNumberDecEx(8888, 0xFF, true);
  delay(1000);
  disp1.clear();
  disp2.clear();

  // Initialise ADS1220
  if (!ads.init()) {
    Serial.println(F("ERROR: ADS1220 not responding. Check SPI wiring!"));
    disp1.setSegments(SEG_ERR);
    disp2.setSegments(SEG_ERR);
    while (1); // halt execution
  }
  
  // !!!ADS1220 configuration!!!
  //
  // PGA bypassed:
  //   DT-670 output spans 0.09 V–1.64 V, well within the 2.048 V
  //   internal reference. Gain = 1 is sufficient; no amplification needed.

  ads.bypassPGA(true);

  // Data rate: 20 SPS
  //   Lowest available rate → best noise performance.
  //   The ADS1220 digital filter simultaneously rejects 50 Hz and 60 Hz
  //   at 20 SPS — ideal for a rack instrument in a lab environment.
  ads.setDataRate(ADS1220_DR_LVL_0);

  // Conversion mode: single-shot
  //   Triggered on demand before each reading. Saves power and avoids
  //   noise from continuous conversion between readings.
  ads.setConversionMode(ADS1220_SINGLE_SHOT);

  Serial.println(F("ADS1220 initialised. Starting readout."));
  Serial.println(F("--------------------------------------------"));
  Serial.println(F("Sensor | Voltage (V) | Temperature (K)"));
  Serial.println(F("--------------------------------------------"));
}

// !!!Main loop!!!

void loop() {

  // Sensor 1: AIN0 (+) vs AIN1 (−), differential
  ads.setCompareChannels(ADS1220_MUX_0_1);
  float voltage1_V = ads.getVoltage_mV() / 1000.0f;
  float temp1_K    = voltageToKelvin(voltage1_V);

  // Sensor 2: AIN2 (+) vs AIN3 (−), differential
  ads.setCompareChannels(ADS1220_MUX_2_3);
  float voltage2_V = ads.getVoltage_mV() / 1000.0f;
  float temp2_K    = voltageToKelvin(voltage2_V);

  // Update 7-segment displays
  displayKelvin(disp1, temp1_K);
  displayKelvin(disp2, temp2_K);

// !!!Outputting live data into terminal when testing!!!
//  Serial.print(F("  S1   | "));
//  Serial.print(voltage1_V, 6);
//  Serial.print(F(" V  | "));
//  if (temp1_K < 0.0f) Serial.println(F("OUT OF RANGE"));
//  else { Serial.print(temp1_K, 3); Serial.println(F(" K")); }

//   Serial.print(F("  S2   | "));
//   Serial.print(voltage2_V, 6);
 //  Serial.print(F(" V  | "));
 //  if (temp2_K < 0.0f) Serial.println(F("OUT OF RANGE"));
  // else { Serial.print(temp2_K, 3); Serial.println(F(" K")); }


    time_ms = millis();
    Serial.print(time_ms);
    Serial.print(",");

    if (temp1_K < 0.0f) Serial.print(-999.0);
    else Serial.print(temp1_K, 6);

    Serial.print(",");

    if (temp2_K < 0.0f) Serial.print(-999.0);
    else Serial.print(temp2_K, 6);

    Serial.println();

  // Take a measurement every 10 seconds
  delay(500);
}

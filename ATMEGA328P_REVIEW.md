# ATmega328P Node Review

Reviewed against the current KiCad schematic/PCB, the OpenEVSE PLUS v6.5.1 Eagle source in `orig/`, the ATmega328P data sheet, and the current OpenEVSE `m328p` firmware target. The corrective changes listed below were subsequently applied to the schematic and PCB.

## Overall result

The ATmega328P pin assignment and 16 MHz clock concept are sound, and the unusual `+5V -> L1 -> R27 -> VCC` supply path is inherited from the original OpenEVSE design. Digital decoupling, the C19 return, C21 value, I2C clock label, and MCU power-source modelling have now been corrected. Project-wide ERC/DRC findings outside this node remain.

## Pin assignment and firmware compatibility

`IC2` uses the correct 32-pin TQFP mapping. The analog inputs match the firmware target: `AMP_READ` is ADC0/PC0, `PILOT_READ` is ADC1/PC1, and `PP_READ` is ADC2/PC2. GFCI interrupt is PD2/INT0, and the pilot PWM is PB2/OC1B. ISP has the standard signal set (`MISO`, `MOSI`, `AVR_SCK`, `RESET`, `+5V`, `GND`). ADC7 and PC3 are intentionally unused on the schematic; PC3 is the optional firmware button input and is not required for this board.

PC5 and the MCP9808 clock input are now labelled `SCL`. The firmware uses `Wire` and MCP9808 address `0x18`; SDA/PC4 and SCL/PC5 are the correct pins.

## Power and decoupling

Pins 4 and 6 are on filtered `VCC`; AVCC pin 18 is on `+5V`. This reproduces the original Eagle circuit: `L1` (BLM21PG331SN1D) and `R27` (2 ohm) filter the digital rail while AVCC stays on the regulator rail. At an estimated 10–20 mA MCU current, R27 drops about 20–40 mV, safely below the data-sheet limit that AVCC and VCC remain within 0.3 V. This topology is acceptable only if the VCC load remains limited to the MCU/local logic and the voltage difference is verified during relay switching.

The present bypass layout needs improvement:

- `C19` and the added `C35` now provide one 100 nF bypass for each digital VCC group. C35 uses a 0402 footprint on B.Cu directly beneath IC2 and short via connections to pins 5/6.
- `C19` and `C35` now return directly to `UGND`. Bulk capacitors C17/C18 remain on the main GND side of net tie SH1.
- `C21` has been restored from 1.0 uF to the original 100 nF value for AVCC bypassing.
- `C17` 10 uF and `C18` 1 uF provide adequate local bulk capacitance after R27.

`SH1` creates the intended single connection between `GND` and quiet `UGND`. `SH2` separately joins the crystal capacitor return to `UGND`. These net ties are useful only if relay, power-supply, and pilot-drive currents do not cross the quiet MCU/ADC ground area. Copper-zone and return-path inspection is required after routing is finalized.

## Clock

`Y1` is 16 MHz with two 12 pF load capacitors. For equal capacitors, the effective load is approximately `12 pF / 2 + 2 pF stray = 8 pF`, which matches an 8 pF-load crystal such as XRCGB16M000FXN01R0. The firmware defines 16 MHz and low fuse `0xFF`, selecting the low-power crystal oscillator for the 8–16 MHz range, with CKDIV8 disabled and the longest start-up delay. The oscillator connections are about 5.6 and 6.8 mm from the MCU pads; their load capacitors and `SH2` return form a larger loop than desirable. Keep both traces short, symmetric, free of vias, and away from PWM/relay traces; place the capacitors beside Y1 and connect their common return immediately to the nearest IC2 ground. If relay transients cause clock failures, the full-swing oscillator fuse setting can improve noise margin at the cost of higher consumption, but it must be intentionally programmed and documented.

## AREF and analog integrity

AREF has `C12` 100 nF plus `C20` 1 uF to UGND. This is electrically safe when the firmware uses AVCC as the ADC reference, but 1 uF can slow reference settling when reference modes change. Confirm the firmware never selects the internal 1.1 V reference while an external source drives AREF. The three measurement inputs are assigned correctly; their accuracy will depend mainly on keeping `UGND` quiet and separating pilot PWM and relay return currents.

## Reset and programming

`R10` 10 kohm pulls RESET to +5 V. `C27` 100 nF to ground creates about a 1 ms RC delay and duplicates the original auto-reset arrangement, but it is connected to `GND`, not the MCU's `UGND`, and is physically near the FTDI connector rather than IC2. Return it to UGND or verify that SH1 cannot inject relay noise into RESET. Confirm reliable ISP programming because a large reset capacitor can slow the programmer's reset edge.

The connector named `FTDI1` is not a standard six-pin FTDI cable pinout: it exposes both +12 V and +5 V. Mark pin 1 and voltages clearly on silkscreen and use a keyed mating connector; plugging in a common FTDI adapter by assumption can damage it.

## ERC result and required actions

After adding explicit power flags to VCC and UGND, KiCad 10.0.6 ERC reports 92 project-wide violations and no longer reports undriven power pins on IC2. The remaining findings belong to other project nodes.

Before fabrication, verify VCC-to-AVCC delta during relay/PWM activity and consider shortening the crystal loop. PCB DRC still contains a large pre-existing project-wide backlog; the new C19/C35 connections do not add shorts or unrouted connections.

## References

- Microchip, *ATmega328P Data Sheet*: https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf
- OpenEVSE firmware: https://github.com/OpenEVSE/open_evse

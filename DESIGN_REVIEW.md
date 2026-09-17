# EVSE circuit review

> Superseded by the current Russian-language validation report in `SCHEMATIC_TEST_REPORT.md`. This older document describes an earlier, incomplete schematic state.

## Scope

This review covers the circuitry currently present in `evse.kicad_sch` and compares passive-component intent with `orig/OpenEVSE_PLUS_v6.5.1.sch`. The KiCad conversion is partial: pilot generation/measurement, GFCI, AC sensing, and several protection circuits from the Eagle design are absent, so this is not yet a production-complete EVSE controller.

## Power supplies

PS1 (IRM-10-12) provides 12 V at up to 0.85 A (10.2 W). U1 is the fixed 5 V AP63205 buck. For 12 V input, 5 V output, 1.1 MHz, and L2 = 4.7 uH:

- duty ratio is approximately 0.417;
- inductor ripple is approximately 0.56 A peak-to-peak;
- peak current at a 2 A load is approximately 2.28 A;
- ideal capacitive ripple with C29 + C33 = 44 uF is approximately 1.5 mV, plus capacitor ESR and layout effects.

L2 is therefore specified as Bourns SRP5030T-4R7M (4.7 uH, 53 mOhm maximum DCR, 4.6 A Irms, 6 A Isat). C5 remains 100 nF between BST and SW. C22 is specified for 25 V; C17 for 10 V. The 2 A regulator rating cannot be treated as an available system load: the 10.2 W AC/DC module and any 12 V relay loads set the real limit. Keep the continuous 5 V load at or below approximately 1.5 A until the full power budget and thermal layout are verified.

## Microcontroller and relay drivers

Y1 has an 8 pF load specification. With approximately 2 pF stray capacitance, equal load capacitors calculate to `2 x (8 pF - 2 pF) = 12 pF`; C1 and C2 are set accordingly. C12 (AREF), C19 (VCC), and C27 (RESET) are restored to 100 nF. R10 = 10 kOhm and C27 = 100 nF give an approximately 1 ms reset time constant. L1 and R27 form the intended filtered AVCC/VCC feed.

Each MMBT2222A relay driver uses 330 Ohm base resistance, giving about `(5 V - 0.8 V) / 330 Ohm = 12.7 mA`. K1 and K2 are CHS01-S-112LA2 relays with 12 V, 75 mA, 155 Ohm coils. The resulting forced transistor beta is approximately `75 mA / 12.7 mA = 5.9`, providing ample saturation drive. D2 and D5 provide flyback paths.

The two energized coils consume 150 mA and 1.8 W from the 12 V supply. This leaves approximately 8.4 W of the IRM-10-12 rating for the buck converter and other 12 V loads. The contacts are Form A (SPST-NO), AgSnO2, rated up to 40 A at 277 VAC under the conditions in the manufacturer datasheet. Separate nets `AC_L1_IN/OUT` and `AC_L2_IN/OUT` are provided for the two switched conductors.

The project footprint follows the CHS01-LA2 bottom view: 32.1 x 27.05 mm body, 10.2 mm coil-pin pitch, 18.75 mm contact-pin spacing, and 15.44 mm nominal separation between coil and contact rows. The enlarged 3.2 mm and 2.5 mm contact drills include assembly clearance over the terminal dimensions shown in the drawing.

## Applied changes

| References | Previous | Updated |
| --- | --- | --- |
| C1, C2 | 22 pF | 12 pF |
| C12, C19, C27 | 1 uF | 100 nF |
| L2 | 3.3 uH, 0805, 450 mA | 4.7 uH SRP5030T-4R7M |
| F1 | ambiguous `BEL1.6AFUSE` | 0HAAL1600-05, 1.6 A, 250 VAC, time-lag |
| C17 | 10 uF, 6.3 V metadata | 10 uF, 10 V low-ESR requirement |
| C22 | 10 uF, 16 V metadata | 10 uF, 25 V low-ESR requirement |
| K1, K2 | absent | CHS01-S-112LA2 symbols in the schematic; project footprint assigned but not placed on the PCB |

## Release blockers

ERC currently reports 6 errors and 15 warnings, including undriven power pins and disconnected functional inputs. K1 and K2 are intentionally schematic-only at this stage; their assigned project footprint has not been transferred to the PCB. Before fabrication, complete the schematic connections, update the PCB only when explicitly authorized, verify mains creepage/clearance and fuse safety approvals, then obtain clean ERC/DRC results.

## Primary references

- [Diodes Incorporated, AP63200/AP63201/AP63203/AP63205 datasheet](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf)
- [Microchip, ATmega328P datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-7810-Automotive-Microcontrollers-ATmega328P_Datasheet.pdf)
- [Murata, XRCGB16M000FXN01R0 specification](https://www.murata.com/products/productdata/8801057112094/SPEC-XRCGB16M000FXN01R0.pdf)
- [Bourns, SRP5030T power-inductor datasheet](https://www.bourns.com/docs/Product-Datasheets/SRP5030T.pdf)
- [Bel Fuse, 0HAAL1600-05 product specification](https://www.belfuse.com/products/circuit-protection/fuses/0haal1600-05)
- [Churod, CHS-L series relay datasheet](https://www.churodamericas.com/wp-content/uploads/2021/06/chs01-l-data-sheet-2.pdf)

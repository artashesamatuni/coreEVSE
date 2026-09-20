# JLCPCB manufacturing profile

This project is configured for the following standard rigid-PCB order:

- Layers: 2
- Material: FR-4
- Board thickness: 1.6 mm
- Finished copper: 1 oz outer layers
- Surface finish: HASL with lead (`HAL SnPb` in the KiCad stackup)
- Solder mask: green recommended
- Silkscreen: white
- Minimum routed track / clearance used by the design: 0.20 / 0.20 mm
- Vias used by the design: 0.60 mm diameter / 0.30 mm drill
- Copper-to-routed-edge design rule: 0.30 mm
- Solder-mask expansion: 0 mm (1:1 opening)
- Vias: tented on both sides
- Gerber plotting: subtract solder mask openings from silkscreen
- Component reference text: 1.0 x 1.0 mm, 0.15 mm stroke

## Do not order yet

The manufacturing constraints pass, but the KiCad DRC still reports 15
unrouted electrical connections. Gerber and drill deliverables must not be
treated as release files until the unrouted count is zero and the two intended
solder-jumper net ties (SH1 and SH2) have been reviewed/excluded in DRC.

## MOV assembly note

M1, M2, and M3 use Bourns MOV-20D431K varistors with 1.2 mm finished holes.
The 20 mm discs are packed more tightly than their standard component
courtyards allow, matching the original OpenEVSE assembly. Form and lean the
leads during manual assembly so the three coated bodies do not touch. Do not
install all three bodies perfectly vertical and parallel.

If RoHS compliance is required, select lead-free HASL in JLCPCB and change the
KiCad stackup finish from `HAL SnPb` before generating release files.

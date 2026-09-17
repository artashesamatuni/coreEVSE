import os
import xml.etree.ElementTree as ET

import pcbnew


HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_PATH = os.path.join(HERE, "evse.kicad_pcb")
NETLIST_PATH = os.path.join(os.environ["TEMP"], "evse_current.xml")
STD_FP = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
FP_IO = pcbnew.PCB_IO_KICAD_SEXPR()


def load_fp(lib, name):
    if lib == "OpenEVSE":
        path = os.path.join(HERE, "OpenEVSE.pretty")
    else:
        path = os.path.join(STD_FP, lib + ".pretty")
    fp = FP_IO.FootprintLoad(path, name, False)
    if fp is None:
        raise RuntimeError(f"Cannot load footprint {lib}:{name}")
    return fp


def add_fp(board, ref, value, lib, name, x_mm, y_mm, angle=0):
    fp = load_fp(lib, name)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    fp.SetOrientationDegrees(angle)
    board.Add(fp)
    return fp


board = pcbnew.LoadBoard(BOARD_PATH)
root = ET.parse(NETLIST_PATH).getroot()
components = {c.attrib["ref"]: c for c in root.findall("./components/comp")}

# Preserve the original placement where a component has a direct successor.
rename = {
    "Q1": "Y1",
    "L3": "L1",
    "IC4": "U2",
    "TVS0": "TVS1",
    "FTDI0": "FTDI1",
    "ISP1": "J1",
    "PILOT0": "PILOT1",
    "GFCI_CT0": "GFCI_CT1",
    "AMP_CT0": "J3",
}

remove_refs = {
    "AC0", "C8", "D12", "DC_RELAY0", "I2C0", "IC7", "JP2", "M4",
    "R4", "R12", "R29", "U$3", "U$9",
}

for fp in list(board.GetFootprints()):
    ref = fp.GetReference()
    if ref in remove_refs:
        continue
    if ref in rename:
        fp.SetReference(rename[ref])

# Replace parts whose package or pin count changed.
replacements = {
    "PILOT1": ("TerminalBlock_WAGO", "TerminalBlock_WAGO_2601-1102_1x02_P3.50mm_Horizontal"),
    "U2": ("Package_SO", "SOIC-8_3.9x4.9mm_P1.27mm"),
}

for ref, (lib, name) in replacements.items():
    old = next((f for f in board.GetFootprints() if f.GetReference() == ref), None)
    if old is None:
        continue
    pos = old.GetPosition()
    angle = old.GetOrientationDegrees()
    board.Remove(old)
    fp = load_fp(lib, name)
    fp.SetReference(ref)
    fp.SetValue(components[ref].findtext("value", ""))
    fp.SetPosition(pos)
    fp.SetOrientationDegrees(angle)
    board.Add(fp)

# J2 replaces the removed six-pin cable connector.  Pins are +5V, PP, GND, PILOT.
add_fp(
    board, "J2", "EV cable interface", "Connector_Molex",
    "Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical", 189.0, 100.0, 90,
)

# MCP9808 and its local support network replace the external I2C connector.
add_fp(board, "U3", "MCP9808", "Package_SO", "MSOP-8_3x3mm_P0.65mm", 140.0, 81.8)
add_fp(board, "C34", "100nF", "Capacitor_SMD", "C_0805_2012Metric", 145.5, 81.8, 90)
add_fp(board, "R40", "4.7k", "Resistor_SMD", "R_0805_2012Metric", 149.0, 80.8)
add_fp(board, "R41", "4.7k", "Resistor_SMD", "R_0805_2012Metric", 136.0, 84.5)
add_fp(board, "C24", "1.0uF", "Capacitor_SMD", "C_0805_2012Metric", 136.5, 111.8, 90)

# Update values from the authoritative schematic.
pad_number_maps = {
    "D2": {"C": "1", "A": "2"},
    "D5": {"C": "1", "A": "2"},
    "TVS1": {"A": "1", "C": "2"},
    "L2": {"P$1": "1", "P$2": "2"},
    "C17": {"+": "1", "-": "2"},
    "C22": {"A": "1", "C": "2"},
    "Y1": {"3": "NC1", "4": "NC2"},
    "PS1": {"AC/N": "1", "AC/L": "2", "V-": "3", "V+": "4"},
    "F1": {"IN": "1", "OUT": "2"},
}

for fp in board.GetFootprints():
    comp = components.get(fp.GetReference())
    if comp is not None:
        fp.SetValue(comp.findtext("value", ""))
        footprint_id = comp.findtext("footprint", "")
        if footprint_id:
            library, footprint_name = footprint_id.split(":", 1)
            fp.SetFPID(pcbnew.LIB_ID(library, footprint_name))
        tstamp = comp.findtext("tstamps", "")
        if tstamp:
            fp.SetPath(pcbnew.KIID_PATH("/" + tstamp))
        number_map = pad_number_maps.get(fp.GetReference(), {})
        for pad in fp.Pads():
            old_number = str(pad.GetNumber())
            if old_number in number_map:
                pad.SetNumber(number_map[old_number])
    if fp.GetReference() in {"SH1", "SH2"}:
        fp.ClearNetTiePadGroups()
        fp.AddNetTiePadGroup("1,2")
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)

# Small placement corrections for footprints that are larger than their Eagle
# predecessors or violated the current KiCad clearance rules.
placement_corrections = {
    "PILOT1": (110.0, 94.8448),
    "TVS1": (114.5, 89.0),
    "L1": (123.4, 87.3),
    "C28": (109.4, 105.25),
}
for ref, (x_mm, y_mm) in placement_corrections.items():
    fp = next(f for f in board.GetFootprints() if f.GetReference() == ref)
    fp.SetPosition(pcbnew.VECTOR2I_MM(x_mm, y_mm))

# Reassign pad nets from the current schematic. Existing routed nets with the
# same names remain attached, while new parts receive their correct ratsnest.
net_for_pin = {}
valid_nets = set()
for net in root.findall("./nets/net"):
    name = net.attrib.get("name", "")
    if name.startswith("Net-("):
        name = name.replace("/", "{slash}")
    valid_nets.add(name)
    for node in net.findall("node"):
        net_for_pin[(node.attrib["ref"], node.attrib["pin"])] = name

board_nets = {str(n.GetNetname()): n for n in board.GetNetInfo().NetsByName().values()}
for name in sorted(valid_nets):
    if name not in board_nets:
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
        board_nets[name] = item

for fp in board.GetFootprints():
    for pad in fp.Pads():
        name = net_for_pin.get((fp.GetReference(), str(pad.GetNumber())))
        if name is not None:
            pad.SetNet(board_nets[name])
        elif fp.GetReference() in components:
            pad.SetNetCode(0)

# The imported routes encode the old symbol pin mapping. Keep the mechanical
# layout and placement, but rebuild copper from the current ratsnest.
zones_to_remove = list(board.Zones())
tracks_to_remove = list(board.GetTracks())
footprints_to_remove = [
    fp for fp in list(board.GetFootprints()) if fp.GetReference() in remove_refs
]

for item in zones_to_remove + tracks_to_remove + footprints_to_remove:
    board.Remove(item)

pcbnew.SaveBoard(BOARD_PATH, board)
print(f"Saved {BOARD_PATH}: {len(list(board.GetFootprints()))} footprints")

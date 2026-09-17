"""Generate a KiCad VRML model for the DL-CT08CL19-1000/1 assembly.

The catalogue defines a 29.9 mm body, 15 mm aperture and 13.3 mm depth.
The model also shows the two 3 mm L/N primary jumpers and the external
five-turn self-test winding represented by the footprint.
"""

from math import cos, pi, sin, sqrt
from pathlib import Path


OUT = Path(__file__).with_name("DL_CT.3dshapes") / "DL-CT08CL19-1000-1.wrl"
MM_TO_VRML = 1.0 / 2.54
SEGMENTS = 72


def annulus_mesh(outer_r, inner_r, z0, z1, segments=SEGMENTS):
    points = []
    for z in (z0, z1):
        for radius in (inner_r, outer_r):
            for i in range(segments):
                angle = 2 * pi * i / segments
                points.append((radius * cos(angle), radius * sin(angle), z))
    inner_bottom = 0
    outer_bottom = segments
    inner_top = 2 * segments
    outer_top = 3 * segments
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((outer_bottom + i, outer_bottom + j, inner_bottom + j, inner_bottom + i))
        faces.append((outer_top + j, outer_top + i, inner_top + i, inner_top + j))
        faces.append((outer_bottom + i, outer_top + i, outer_top + j, outer_bottom + j))
        faces.append((inner_bottom + j, inner_top + j, inner_top + i, inner_bottom + i))
    return points, faces


def box_mesh(x0, x1, y0, y1, z0, z1):
    points = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
    ]
    return points, faces


def cylinder_mesh(start, end, radius, segments=28):
    axis = tuple(end[i] - start[i] for i in range(3))
    length = sqrt(sum(value * value for value in axis))
    axis = tuple(value / length for value in axis)
    reference = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = (
        axis[1] * reference[2] - axis[2] * reference[1],
        axis[2] * reference[0] - axis[0] * reference[2],
        axis[0] * reference[1] - axis[1] * reference[0],
    )
    u_length = sqrt(sum(value * value for value in u))
    u = tuple(value / u_length for value in u)
    v = (
        axis[1] * u[2] - axis[2] * u[1],
        axis[2] * u[0] - axis[0] * u[2],
        axis[0] * u[1] - axis[1] * u[0],
    )
    points = []
    for base in (start, end):
        for i in range(segments):
            angle = 2 * pi * i / segments
            offset = tuple(radius * (cos(angle) * u[j] + sin(angle) * v[j]) for j in range(3))
            points.append(tuple(base[j] + offset[j] for j in range(3)))
    points.extend((start, end))
    start_center, end_center = 2 * segments, 2 * segments + 1
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((i, j, segments + j, segments + i))
        faces.append((start_center, j, i))
        faces.append((end_center, segments + i, segments + j))
    return points, faces


def indexed_face_set(points, faces, color, metallic=False):
    coords = ",\n".join(
        f"          {x * MM_TO_VRML:.6f} {-y * MM_TO_VRML:.6f} {z * MM_TO_VRML:.6f}"
        for x, y, z in points
    )
    indices = ",\n".join("          " + ", ".join(map(str, face)) + ", -1" for face in faces)
    specular = "0.75 0.52 0.25" if metallic else "0.08 0.08 0.08"
    shininess = "0.72" if metallic else "0.12"
    return f"""Shape {{
  appearance Appearance {{ material Material {{ diffuseColor {color} specularColor {specular} shininess {shininess} }} }}
  geometry IndexedFaceSet {{
    solid FALSE
    creaseAngle 0.45
    coord Coordinate {{ point [
{coords}
    ] }}
    coordIndex [
{indices}
    ]
  }}
}}"""


def add_cylinder(parts, start, end, radius, color, metallic=False):
    points, faces = cylinder_mesh(start, end, radius)
    parts.append(indexed_face_set(points, faces, color, metallic))


body_points, body_faces = annulus_mesh(14.95, 7.5, 0.0, 13.3)
parts = [indexed_face_set(body_points, body_faces, "0.045 0.048 0.052")]

# Moulded lead-exit neck; the catalogue gives 33 mm overall front-view height.
neck_points, neck_faces = box_mesh(-3.2, 3.2, -16.5, -13.2, 0.0, 13.3)
parts.append(indexed_face_set(neck_points, neck_faces, "0.045 0.048 0.052"))

# Two insulated 3 mm jumpers.  Each rises from an outside pad, crosses the
# toroid and returns through an inside-aperture pad.
for x, color in ((-4.25, "0.55 0.12 0.06"), (4.25, "0.08 0.16 0.55")):
    add_cylinder(parts, (x, 21.0, -1.0), (x, 21.0, 15.8), 1.5, color, True)
    add_cylinder(parts, (x, 21.0, 15.8), (x, 0.0, 15.8), 1.5, color, True)
    add_cylinder(parts, (x, 0.0, 15.8), (x, 0.0, -1.0), 1.5, color, True)

# Five orange test turns, shown as parallel wraps across the lower-right part
# of the core.  The small azimuth offset keeps every turn visible.
test_color = "0.95 0.30 0.03"
for index in range(5):
    x = 7.9 + index * 0.8
    y_inner = -sqrt(max(0.0, 7.0**2 - min(x, 6.9) ** 2))
    y_outer = -sqrt(max(0.0, 15.5**2 - x**2))
    add_cylinder(parts, (x, y_inner, -0.5), (x, y_inner, 14.0), 0.35, test_color)
    add_cylinder(parts, (x, y_inner, 14.0), (x, y_outer, 14.0), 0.35, test_color)
    add_cylinder(parts, (x, y_outer, 14.0), (x, y_outer, -0.5), 0.35, test_color)

# Ends of the test winding terminate at the S3 and S4 footprint pads.
add_cylinder(parts, (7.9, -13.34, 0.6), (3.0, -20.0, 0.6), 0.35, test_color)
add_cylinder(parts, (11.1, -10.78, 0.6), (9.0, -20.0, 0.6), 0.35, test_color)

# Secondary lead stubs matching the catalogue red/black convention.
add_cylinder(parts, (-1.2, -16.5, 6.5), (-9.0, -20.0, 1.0), 0.45, "0.78 0.02 0.02")
add_cylinder(parts, (1.2, -16.5, 6.5), (-3.0, -20.0, 1.0), 0.45, "0.02 0.02 0.02")

OUT.parent.mkdir(exist_ok=True)
OUT.write_text("#VRML V2.0 utf8\n\n" + "\n\n".join(parts) + "\n", encoding="ascii")
print(OUT)

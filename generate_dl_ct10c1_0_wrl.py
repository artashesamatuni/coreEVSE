"""Generate the DL-CT10C1.0 body and its 50 mm primary jumper.

The secondary S1/S2 leads are deliberately omitted from the 3D model.
"""

from math import cos, pi, sin, sqrt
from pathlib import Path


OUT = Path(__file__).with_name("DL_CT.3dshapes") / "DL-CT10C1.0.wrl"
MM_TO_VRML = 1.0 / 2.54
SEGMENTS = 64


def outer_radius(angle: float) -> float:
    """Ray intersection with the 28.8 x 29 mm D-shaped front silhouette."""
    cx, cz = 0.0, 14.75
    dx, dz = cos(angle), sin(angle)
    lo, hi = 0.0, 40.0
    for _ in range(60):
        t = (lo + hi) / 2
        x, z = cx + t * dx, cz + t * dz
        inside = abs(x) <= 14.4 and z >= 0.0
        if inside and z > 14.6:
            inside = x * x + (z - 14.6) ** 2 <= 14.4**2
        if inside:
            lo = t
        else:
            hi = t
    return lo


def body_mesh():
    depth = 15.4
    hole_r = 6.25
    points = []
    for y in (0.0, depth):
        for radius_kind in ("inner", "outer"):
            for i in range(SEGMENTS):
                a = 2 * pi * i / SEGMENTS
                r = hole_r if radius_kind == "inner" else outer_radius(a)
                points.append((r * cos(a), y, 14.75 + r * sin(a)))

    inner_front = 0
    outer_front = SEGMENTS
    inner_back = 2 * SEGMENTS
    outer_back = 3 * SEGMENTS
    faces = []
    for i in range(SEGMENTS):
        j = (i + 1) % SEGMENTS
        faces.append((outer_front + i, outer_front + j, inner_front + j, inner_front + i))
        faces.append((outer_back + j, outer_back + i, inner_back + i, inner_back + j))
        faces.append((outer_front + i, outer_back + i, outer_back + j, outer_front + j))
        faces.append((inner_front + j, inner_back + j, inner_back + i, inner_front + i))
    return points, faces


def cylinder_mesh(start, end, radius, segments=32):
    """Return a capped cylinder mesh between two points, in millimetres."""
    ax, ay, az = (end[i] - start[i] for i in range(3))
    length = sqrt(ax * ax + ay * ay + az * az)
    ax, ay, az = ax / length, ay / length, az / length
    reference = (0.0, 0.0, 1.0) if abs(az) < 0.9 else (1.0, 0.0, 0.0)
    ux = ay * reference[2] - az * reference[1]
    uy = az * reference[0] - ax * reference[2]
    uz = ax * reference[1] - ay * reference[0]
    ulen = sqrt(ux * ux + uy * uy + uz * uz)
    ux, uy, uz = ux / ulen, uy / ulen, uz / ulen
    vx, vy, vz = ay * uz - az * uy, az * ux - ax * uz, ax * uy - ay * ux
    points = []
    for base in (start, end):
        for i in range(segments):
            angle = 2 * pi * i / segments
            radial = (
                radius * (cos(angle) * ux + sin(angle) * vx),
                radius * (cos(angle) * uy + sin(angle) * vy),
                radius * (cos(angle) * uz + sin(angle) * vz),
            )
            points.append(tuple(base[j] + radial[j] for j in range(3)))
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
    specular = "0.80 0.58 0.28" if metallic else "0.08 0.08 0.08"
    shininess = "0.78" if metallic else "0.12"
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


points, faces = body_mesh()
parts = [indexed_face_set(points, faces, "0.055 0.060 0.065")]

# One-turn primary: P2=(0,-5), P1=(0,19), copper diameter 3 mm.
# The 13 + 24 + 13 mm centreline is exactly 50 mm and passes through the aperture.
COPPER = "0.72 0.32 0.10"
for y in (-5.0, 19.0):
    jumper_points, jumper_faces = cylinder_mesh((0.0, y, 0.0), (0.0, y, 13.0), 1.5)
    parts.append(indexed_face_set(jumper_points, jumper_faces, COPPER, metallic=True))
jumper_points, jumper_faces = cylinder_mesh((0.0, -5.0, 13.0), (0.0, 19.0, 13.0), 1.5)
parts.append(indexed_face_set(jumper_points, jumper_faces, COPPER, metallic=True))

OUT.parent.mkdir(exist_ok=True)
OUT.write_text("#VRML V2.0 utf8\n\n" + "\n\n".join(parts) + "\n", encoding="ascii")
print(OUT)

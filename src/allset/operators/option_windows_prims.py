# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 196 (#103): Maya option windows of Create > Polygon Primitives (Disc ... Ultra Shape) and Create > NURBS
Primitives (same spec as operators/option_windows.py; option_windows._extend appends ``WINDOWS``).

Titles, field labels, ranges and factory values: Maya 2022's
option windows with factory settings.
Each window fills the kit's Maya creation node (operators/prim_history.py, prim_shapes*.py, prim_supershape.py) through
``create.create(context, kind, overrides)``: values are Maya values, lengths in Maya units (create() scales them).
Fields Blender / the kit can't follow are listed as ``missing``."""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

from .option_windows import AXIS, UVS, F, Window

_NORM = ("Normalize", "Preserve aspect ratio")
_TOL = "Use tolerance: Local / Global, Positional tolerance (None only: sections and spans are used)"
_VIEW = "Axis: Active view"
_AXES = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}


def _create(context, kind, over):
    from . import create
    create.create(context, kind, overrides=over)
    return {'FINISHED'}


def _poly(kind, attrs, axis=True, uvs=True, extra=None):
    """Run: fields named after the node attribute pass straight through; Axis -> axisX/Y/Z, Create UVs -> createUVs."""
    def run(context, v):
        over = {a: v[a] for a in attrs}
        if axis:
            ax = _AXES[v["axis"]]
            over.update(axisX=ax[0], axisY=ax[1], axisZ=ax[2])
        if uvs:
            over["createUVs"] = int(bool(v["create_uvs"]))
        if extra is not None:
            extra(v, over)
        return _create(context, kind, over)
    return run


# --- polygon primitives -----------------------------------------------------------------------------

_DISC_MODES = ("Quads", "Triangles", "Pie", "Caps", "Circle")
_PLATONIC = ("Tetrahedron", "Cube", "Octahedron", "Dodecahedron", "Icosahedron")
_PLATONIC_MODES = ("Quads", "Triangles", "Pie", "Caps")


def _disc_extra(v, over):
    over["subdivisionMode"] = _DISC_MODES.index(v["subdivision_mode"])


def _platonic_extra(v, over):
    over["primitive"] = _PLATONIC.index(v["primitive"])
    over["subdivisionMode"] = _PLATONIC_MODES.index(v["subdivision_mode"])


def _pyramid_extra(v, over):
    over["numberOfSides"] = int(v["number_of_sides"])     # Maya radio 3 / 4 / 5 (ornsval: -ns 3 / 4 / 5)


def _helix_extra(v, over):
    over["direction"] = ("Clockwise", "Counterclockwise").index(v["direction"])


def _soccer_extra(v, over):
    # Maya links Radius and Side length both ways while editing
    # (Side = Radius x 0.4036); the kit node follows the radius, so a side length typed alone sets the radius
    # (delegated: whichever field differs from the linked value wins)
    from . import prim_shapes_more
    side = prim_shapes_more.SOCCER_SIDE
    if abs(v["sideLength"] - v["radius"] * side) > 1e-4 and abs(v["radius"] - 1.0) < 1e-9:
        over["radius"] = v["sideLength"] / side
    over["sideLength"] = over["radius"] * side


_SUPER_KINDS = {"Super Ellipse": 'SUPER_ELLIPSE', "Spherical Harmonics": 'SPHERICAL_HARMONICS',
                "Ultra Shape": 'ULTRA_SHAPE'}
_SUPER_ATTRS = (["radius", "horizontalDivisions", "verticalDivisions", "mergeVertices", "horizontalRevolutions",
                 "verticalRevolutions", "verticalOffset", "internalRadius", "xOffset", "zOffset",
                 "ellipse0", "ellipse1", "ellipseMirror"] + [f"harmonics{i}" for i in range(8)]
                + [f"ultra{i}" for i in range(16)] + ["ultraMirror"])


def _run_super(context, v):
    # the window's Shape field picks the shape (shape 1 / 2 / 3 -> SuperEllipse /
    # SphericalHarmonics / UltraShape), whichever menu item opened it
    over = {a: v[a] for a in _SUPER_ATTRS}
    over["createUVs"] = int(v["create_uvs"] != "None")
    return _create(context, _SUPER_KINDS[v["shape"]], over)


def _super_fields(shape):
    """Polygon Super Shape Options: General / Helix / Super Ellipse / Spherical Harmonics / Ultra
    frames (Maya factory values; the menu item sets the Shape)."""
    sh = [F(f"harmonics{i}", f"{'V' if i < 4 else 'H'} {'Multiplier' if i % 2 == 0 else 'Exponent'} {i % 4 // 2 + 1}:",
            "float", d, lo=-20.0 if i % 2 == 0 else 0.0, hi=20.0 if i % 2 == 0 else 5.0, translation_context='MWK:operators/option_windows_prims.py:96')
          for i, d in enumerate((0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0))]
    ultra_labels = ("Multiplier 1:", "Exponent 1:", "Exponent 2:", "Mixer:", "Multiplier 2:", "Exponent 3:",
                    "Exponent 4:", "Exponent 5:")
    ultra = [F(f"ultra{i}", f"{'Horizontal' if i < 8 else 'Vertical'} {ultra_labels[i % 8]}", "float", d,
               lo=-30.0 if i % 4 == 0 else 0.0, hi=30.0 if i % 4 == 0 else (1.0 if i % 8 == 3 else 4.0), translation_context='MWK:operators/option_windows_prims.py:101')
             for i, d in enumerate((0.0, 1.0, 1.0, 0.5, 0.0, 1.0, 1.0, 1.0) * 2)]
    return [
        F("shape", "Shape:", "enum", shape, items=tuple(_SUPER_KINDS), translation_context='MWK:operators/option_windows_prims.py:105'),
        F("radius", "Radius:", "length", 1.0, lo=0.001, hi=100, translation_context='MWK:operators/option_windows_prims.py:106'),
        F("horizontalDivisions", "Horizontal Divisions:", "int", 16, lo=1, hi=100, translation_context='MWK:operators/option_windows_prims.py:107'),
        F("verticalDivisions", "Vertical Divisions:", "int", 16, lo=1, hi=100, translation_context='MWK:operators/option_windows_prims.py:108'),
        F("create_uvs", "Create UVs:", "enum", "Sawtooth at pole", items=("None", "Pinched at pole", "Sawtooth at pole"), translation_context='MWK:operators/option_windows_prims.py:109'),
        F("mergeVertices", "Merge Vertices:", "bool", True, translation_context='MWK:operators/option_windows_prims.py:110'),
        F("horizontalRevolutions", "Horizontal Revolutions:", "float", 1.0, lo=0.0, translation_context='MWK:operators/option_windows_prims.py:111'),
        F("verticalRevolutions", "Vertical Revolutions:", "float", 1.0, lo=0.0, translation_context='MWK:operators/option_windows_prims.py:112'),
        F("verticalOffset", "Vertical Offset:", "float", 0.0, lo=0.0, translation_context='MWK:operators/option_windows_prims.py:113'),
        F("internalRadius", "Internal Radius:", "float", 0.0, lo=0.0, translation_context='MWK:operators/option_windows_prims.py:114'),
        F("xOffset", "X Offset:", "float", 0.0, lo=0.0, translation_context='MWK:operators/option_windows_prims.py:115'), F("zOffset", "Z Offset:", "float", 0.0, lo=0.0, translation_context='MWK:operators/option_windows_prims.py:115'),
        F("ellipse0", "V Exponent:", "float", 1.0, lo=0.0, hi=5.0, translation_context='MWK:operators/option_windows_prims.py:116'),
        F("ellipse1", "H Exponent:", "float", 1.0, lo=0.0, hi=5.0, translation_context='MWK:operators/option_windows_prims.py:117'),
        F("ellipseMirror", "Mirror:", "bool", True, translation_context='MWK:operators/option_windows_prims.py:118'),
        *sh, *ultra,
        F("ultraMirror", "Ultra Mirror:", "bool", False, translation_context='MWK:operators/option_windows_prims.py:120'),
    ]


def _super(key, shape):
    return Window(key, "Polygon Super Shape Options", "Create", ("allset.create", {"kind": _SUPER_KINDS[shape]}),
                  _super_fields(shape), _run_super, width=480,
                  missing=("Create UVs: Pinched at pole (built as Sawtooth at pole)",), translation_context='MWK:operators/option_windows_prims.py:125')


# --- NURBS primitives -------------------------------------------------------------------------------

_AXIS_N = ("X", "Y", "Z", "Free")
LINEAR_CUBIC = ("Linear", "Cubic")


def _pivot_fields(label="Pivot:"):
    return [F("pivot", label, "enum", "Object", items=("Object", "User defined"), translation_context='MWK:operators/option_windows_prims.py:137'),
            F("pivot_point", "Pivot point:", "vec3", (0.0, 0.0, 0.0), translation_context='MWK:operators/option_windows_prims.py:138')]


def _axis_fields(label="Axis:", definition="Axis definition:"):
    return [F("axis", label, "enum", "Y", items=_AXIS_N, translation_context='MWK:operators/option_windows_prims.py:142'),
            F("axis_definition", definition, "vec3", (0.0, 1.0, 0.0), translation_context='MWK:operators/option_windows_prims.py:143')]


def _axis_of(v):
    return tuple(v["axis_definition"]) if v["axis"] == "Free" else _AXES[v["axis"]]


def _pivot_of(v):
    return tuple(v["pivot_point"]) if v["pivot"] == "User defined" else (0.0, 0.0, 0.0)


def _degree(label):
    return 1 if label.strip().startswith(("1", "Linear")) else 3


def _nurbs(kind, build):
    """Run: Pivot -> pivotX/Y/Z (Object = origin), Axis -> axisX/Y/Z (Free = Axis definition), then ``build``."""
    def run(context, v):
        p, a = _pivot_of(v), _axis_of(v)
        over = {"pivotX": p[0], "pivotY": p[1], "pivotZ": p[2], "axisX": a[0], "axisY": a[1], "axisZ": a[2]}
        build(v, over)
        return _create(context, kind, over)
    return run


def _sweeps(v, over):
    over.update(startSweep=v["start_sweep"], endSweep=v["end_sweep"], radius=v["radius"],
                degree=_degree(v["degree"]), sections=v["sections"])


def _sphere_build(v, over):
    _sweeps(v, over)
    over["spans"] = v["spans"]


def _cyl_build(v, over):
    # Height field -> heightRatio = height / radius (nurbsRatioConvert)
    _sweeps(v, over)
    over.update(spans=v["spans"], heightRatio=v["height"] / v["radius"] if v["radius"] else 0.0)


def _torus_build(v, over):
    _sweeps(v, over)
    over.update(spans=v["spans"], minorSweep=v["minor_sweep"],
                heightRatio=v["minor_radius"] / v["radius"] if v["radius"] else 0.0)


def _plane_build(v, over):
    w = v["width"]
    over.update(width=w, lengthRatio=v["length"] / w if w else 0.0, patchesU=v["patches_u"],
                patchesV=v["patches_v"], degree=_degree(v["degree"]))
    if "height" in v:
        over["heightRatio"] = v["height"] / w if w else 0.0


def _run_circle(context, v):
    c, n = _pivot_of(v), _axis_of(v)
    over = {"centerX": c[0], "centerY": c[1], "centerZ": c[2], "normalX": n[0], "normalY": n[1], "normalZ": n[2],
            "sweep": v["sweep"], "radius": v["radius"], "degree": _degree(v["degree"]), "sections": v["sections"]}
    return _create(context, 'NURBS_CIRCLE', over)


def _run_square(context, v):
    c, n = tuple(v["center"]), _axis_of(v)
    over = {"centerX": c[0], "centerY": c[1], "centerZ": c[2], "normalX": n[0], "normalY": n[1], "normalZ": n[2],
            "sideLength1": v["side1"], "sideLength2": v["side2"], "spansPerSide": v["spans_per_side"],
            "degree": _degree(v["degree"])}
    return _create(context, 'NURBS_SQUARE', over)


def _sweep_fields():
    return [F("start_sweep", "Start sweep angle:", "float", 0.0, lo=-3600.0, hi=3600.0, translation_context='MWK:operators/option_windows_prims.py:214'),
            F("end_sweep", "End sweep angle:", "float", 360.0, lo=-3600.0, hi=3600.0, translation_context='MWK:operators/option_windows_prims.py:215')]


def _degree_field(label="Surface degree:", items=LINEAR_CUBIC):
    return F("degree", label, "enum", items[-1], items=items, translation_context='MWK:operators/option_windows_prims.py:219')


def _sections(spans_default=None, spans_lo=1):
    out = [F("sections", "Number of sections:", "int", 8, lo=4, hi=200, translation_context='MWK:operators/option_windows_prims.py:223')]
    if spans_default is not None:
        out.append(F("spans", "Number of spans:", "int", spans_default, lo=spans_lo, hi=200, translation_context='MWK:operators/option_windows_prims.py:225'))
    return out


_CAPS = "Caps: None only, Extra transform on caps (no cap surfaces)"
_DEG_MORE = "Surface degree: 2 / 5 / 7 (1 Linear and 3 Cubic only)"

WINDOWS = [
    # Polygon Disc Options: Sides 3, Subdivision Mode Circle, Subdivisions 3, Radius 1 (no axis, no UV option)
    Window("poly_disc", "Polygon Disc Options", "Create", ("allset.create", {"kind": 'DISC'}), [
        F("sides", "Sides:", "int", 3, lo=3, hi=20, translation_context='MWK:operators/option_windows_prims.py:235'),
        F("subdivision_mode", "Subdivision Mode:", "enum", "Circle", items=_DISC_MODES, translation_context='MWK:operators/option_windows_prims.py:236'),
        F("subdivisions", "Subdivisions:", "int", 3, lo=0, hi=40, translation_context='MWK:operators/option_windows_prims.py:237'),
        F("radius", "Radius:", "length", 1.0, lo=0.001, hi=100, translation_context='MWK:operators/option_windows_prims.py:238')],
        _poly('DISC', ("sides", "subdivisions", "radius"), axis=False, uvs=False, extra=_disc_extra), translation_context='MWK:operators/option_windows_prims.py:234'),
    # Polygon Platonic Options: Icosahedron, Quads, 0 subdivisions, radius 1, spherical inflation 1
    Window("poly_platonic", "Polygon Platonic Options", "Create", ("allset.create", {"kind": 'PLATONIC'}), [
        F("primitive", "Primitive:", "enum", "Icosahedron", items=_PLATONIC, translation_context='MWK:operators/option_windows_prims.py:242'),
        F("subdivision_mode", "Subdivision Mode:", "enum", "Quads", items=_PLATONIC_MODES, translation_context='MWK:operators/option_windows_prims.py:243'),
        F("subdivisions", "Subdivisions:", "int", 0, lo=0, hi=40, translation_context='MWK:operators/option_windows_prims.py:244'),
        F("radius", "Radius:", "length", 1.0, lo=0.001, hi=100, translation_context='MWK:operators/option_windows_prims.py:245'),
        F("sphericalInflation", "Spherical Inflation:", "float", 1.0, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_prims.py:246')],
        _poly('PLATONIC', ("subdivisions", "radius", "sphericalInflation"), axis=False, uvs=False,
              extra=_platonic_extra), translation_context='MWK:operators/option_windows_prims.py:241'),
    # Polygon Pyramid Options: side length 1, sides 4, height / cap divisions 1 / 0, axis Y, UVs
    Window("poly_pyramid", "Polygon Pyramid Options", "Create", ("allset.create", {"kind": 'PYRAMID'}), [
        F("sideLength", "Side length:", "length", 1.0, lo=0.0, hi=100, translation_context='MWK:operators/option_windows_prims.py:251'),
        F("number_of_sides", "Number of sides in base:", "enum", "4", items=("3", "4", "5"), translation_context='MWK:operators/option_windows_prims.py:252'),
        F("subdivisionsHeight", "Height divisions:", "int", 1, lo=1, hi=1000, translation_context='MWK:operators/option_windows_prims.py:253'),
        F("subdivisionsCaps", "Cap divisions:", "int", 0, lo=0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:254'), AXIS, UVS],
        _poly('PYRAMID', ("sideLength", "subdivisionsHeight", "subdivisionsCaps"), extra=_pyramid_extra),
        missing=_NORM, translation_context='MWK:operators/option_windows_prims.py:250'),
    # Prism: length 2, side length 1, 3 sides, height / cap divisions 1 / 0
    Window("poly_prism", "Polygon Prism Options", "Create", ("allset.create", {"kind": 'PRISM'}), [
        F("length", "Length:", "length", 2.0, lo=0.0, hi=100, translation_context='MWK:operators/option_windows_prims.py:259'), F("sideLength", "Side length:", "length", 1.0, lo=0.0, hi=100, translation_context='MWK:operators/option_windows_prims.py:259'),
        F("numberOfSides", "Number of sides in base:", "int", 3, lo=3, hi=1000, translation_context='MWK:operators/option_windows_prims.py:260'),
        F("subdivisionsHeight", "Height divisions:", "int", 1, lo=1, hi=1000, translation_context='MWK:operators/option_windows_prims.py:261'),
        F("subdivisionsCaps", "Cap divisions:", "int", 0, lo=0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:262'), AXIS, UVS],
        _poly('PRISM', ("length", "sideLength", "numberOfSides", "subdivisionsHeight", "subdivisionsCaps")),
        missing=_NORM, translation_context='MWK:operators/option_windows_prims.py:258'),
    # Pipe: radius 1, height 2, thickness 0.5, 20 / 1 / 0 divisions, no round cap (no Normalize in Maya's window)
    Window("poly_pipe", "Polygon Pipe Options", "Create", ("allset.create", {"kind": 'PIPE'}), [
        F("radius", "Radius:", "length", 1.0, lo=0.01, hi=100, translation_context='MWK:operators/option_windows_prims.py:267'), F("height", "Height:", "length", 2.0, lo=0.01, hi=100, translation_context='MWK:operators/option_windows_prims.py:267'),
        F("thickness", "Thickness:", "length", 0.5, lo=0.01, hi=100, translation_context='MWK:operators/option_windows_prims.py:268'),
        F("subdivisionsAxis", "Axis divisions:", "int", 20, lo=3, hi=1000, translation_context='MWK:operators/option_windows_prims.py:269'),
        F("subdivisionsHeight", "Height divisions:", "int", 1, lo=1, hi=1000, translation_context='MWK:operators/option_windows_prims.py:270'),
        F("subdivisionsCaps", "Cap divisions:", "int", 0, lo=0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:271'),
        F("roundCap", "", "bool", False, text=_zh_native("Round cap", 'MWK:operators/option_windows_prims.py:272'), translation_context='MWK:operators/option_windows_prims.py:272'), AXIS, UVS],
        _poly('PIPE', ("radius", "height", "thickness", "subdivisionsAxis", "subdivisionsHeight", "subdivisionsCaps",
                       "roundCap")), translation_context='MWK:operators/option_windows_prims.py:266'),
    # Helix: coils 3, height 2, width 2, radius 0.4, 8 / 50 / 0 divisions, Counterclockwise. Maya labels the cap
    # divisions slider "Coils:" too ("C" in Maya's window); kept as Maya shows it
    Window("poly_helix", "Polygon Helix Options", "Create", ("allset.create", {"kind": 'HELIX'}), [
        F("coils", "Coils:", "float", 3.0, lo=0.5, hi=1000, translation_context='MWK:operators/option_windows_prims.py:278'), F("height", "Height:", "length", 2.0, lo=0.01, hi=100, translation_context='MWK:operators/option_windows_prims.py:278'),
        F("width", "Width:", "length", 2.0, lo=0.01, hi=100, translation_context='MWK:operators/option_windows_prims.py:279'), F("radius", "Radius:", "length", 0.4, lo=0.01, hi=100, translation_context='MWK:operators/option_windows_prims.py:279'),
        F("subdivisionsAxis", "Axis divisions:", "int", 8, lo=3, hi=1000, translation_context='MWK:operators/option_windows_prims.py:280'),
        F("subdivisionsCoil", "Coil divisions:", "int", 50, lo=2, hi=1000, translation_context='MWK:operators/option_windows_prims.py:281'),
        F("subdivisionsCaps", "Coils:", "int", 0, lo=0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:282'),
        F("roundCap", "", "bool", False, text=_zh_native("Round cap", 'MWK:operators/option_windows_prims.py:283'), translation_context='MWK:operators/option_windows_prims.py:283'),
        F("direction", "Direction", "enum", "Counterclockwise", items=("Clockwise", "Counterclockwise"), translation_context='MWK:operators/option_windows_prims.py:284'), AXIS, UVS],
        _poly('HELIX', ("coils", "height", "width", "radius", "subdivisionsAxis", "subdivisionsCoil", "subdivisionsCaps",
                        "roundCap"), extra=_helix_extra),
        missing=_NORM, translation_context='MWK:operators/option_windows_prims.py:277'),
    # Polygon Gear Options: no axis, no UV option
    Window("poly_gear", "Polygon Gear Options", "Create", ("allset.create", {"kind": 'GEAR'}), [
        F("sides", "Sides:", "int", 16, lo=3, hi=20, translation_context='MWK:operators/option_windows_prims.py:290'), F("radius", "Radius:", "length", 1.0, lo=0.001, hi=100, translation_context='MWK:operators/option_windows_prims.py:290'),
        F("internalRadius", "Internal Radius:", "length", 0.3, lo=0.0, hi=50, translation_context='MWK:operators/option_windows_prims.py:291'),
        F("height", "Height:", "length", 1.0, lo=0.001, hi=100, translation_context='MWK:operators/option_windows_prims.py:292'),
        F("heightDivisions", "Height Divisions:", "int", 10, lo=1, hi=40, translation_context='MWK:operators/option_windows_prims.py:293'),
        F("gearSpacing", "Gear Spacing:", "float", 0.6, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_prims.py:294'),
        F("gearOffset", "Gear Offset:", "length", 0.2, lo=0.0, hi=20, translation_context='MWK:operators/option_windows_prims.py:295'),
        F("gearTip", "Gear Tip:", "float", 0.5, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_prims.py:296'), F("gearMiddle", "Gear Middle:", "float", 1.2, lo=0.0, hi=2.0, translation_context='MWK:operators/option_windows_prims.py:296'),
        F("twist", "Twist:", "float", 0.0, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_prims.py:297'), F("taper", "Taper:", "float", 1.0, lo=0.001, hi=1.0, translation_context='MWK:operators/option_windows_prims.py:297')],
        _poly('GEAR', ("sides", "radius", "internalRadius", "height", "heightDivisions", "gearSpacing", "gearOffset",
                       "gearTip", "gearMiddle", "twist", "taper"), axis=False, uvs=False), translation_context='MWK:operators/option_windows_prims.py:289'),
    # Polygon Soccer Ball Options: radius 1, side length 0.4036 (linked), axis Y, UVs, Normalize Collectively
    Window("poly_soccer_ball", "Polygon Soccer Ball Options", "Create", ("allset.create", {"kind": 'SOCCER_BALL'}), [
        F("radius", "Radius:", "length", 1.0, lo=0.01, hi=100, translation_context='MWK:operators/option_windows_prims.py:302'),
        F("sideLength", "Side length:", "length", 0.4036, lo=0.01, hi=100, translation_context='MWK:operators/option_windows_prims.py:303'), AXIS, UVS],
        _poly('SOCCER_BALL', ("radius", "sideLength"), extra=_soccer_extra),
        missing=("Normalize", "Collectively / Each face separately", "Preserve aspect ratio"), translation_context='MWK:operators/option_windows_prims.py:301'),
    _super("poly_super_ellipse", "Super Ellipse"),
    _super("poly_spherical_harmonics", "Spherical Harmonics"),
    _super("poly_ultra_shape", "Ultra Shape"),

    # --- NURBS (factory: pivot Object, axis Y, cubic, no tolerance) -------------
    Window("nurbs_sphere", "NURBS Sphere Options", "Create", ("allset.create", {"kind": 'NURBS_SPHERE'}), [
        *_pivot_fields(), *_axis_fields(), *_sweep_fields(),
        F("radius", "Radius:", "length", 1.0, lo=0.0001, hi=1000, translation_context='MWK:operators/option_windows_prims.py:313'), _degree_field(), *_sections(4, 2)],
        _nurbs('NURBS_SPHERE', _sphere_build), missing=(_VIEW, _TOL), translation_context='MWK:operators/option_windows_prims.py:311'),
    Window("nurbs_cube", "NURBS Cube Options", "Create", ("allset.create", {"kind": 'NURBS_CUBE'}), [
        *_pivot_fields(), *_axis_fields(),
        F("width", "Width:", "length", 1.0, lo=0.0001, hi=1000, translation_context='MWK:operators/option_windows_prims.py:317'), F("length", "Length:", "length", 1.0, lo=0.0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:317'),
        F("height", "Height:", "length", 1.0, lo=0.0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:318'), _degree_field(items=("1 Linear", "3 Cubic")),
        F("patches_u", "U patches:", "int", 1, lo=1, hi=500, translation_context='MWK:operators/option_windows_prims.py:319'), F("patches_v", "V patches:", "int", 1, lo=1, hi=500, translation_context='MWK:operators/option_windows_prims.py:319')],
        _nurbs('NURBS_CUBE', _plane_build), missing=(_VIEW, _DEG_MORE), translation_context='MWK:operators/option_windows_prims.py:315'),
    Window("nurbs_cylinder", "NURBS Cylinder Options", "Create", ("allset.create", {"kind": 'NURBS_CYLINDER'}), [
        *_pivot_fields(), *_axis_fields(), *_sweep_fields(),
        F("radius", "Radius:", "length", 1.0, lo=0.0001, hi=1000, translation_context='MWK:operators/option_windows_prims.py:323'), F("height", "Height:", "length", 2.0, lo=0.0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:323'),
        _degree_field(), *_sections(1, 1)],
        _nurbs('NURBS_CYLINDER', _cyl_build), missing=(_VIEW, _CAPS, _TOL), translation_context='MWK:operators/option_windows_prims.py:321'),
    Window("nurbs_cone", "NURBS Cone Options", "Create", ("allset.create", {"kind": 'NURBS_CONE'}), [
        *_pivot_fields(), *_axis_fields(), *_sweep_fields(),
        F("radius", "Radius:", "length", 1.0, lo=0.0001, hi=1000, translation_context='MWK:operators/option_windows_prims.py:328'), F("height", "Height:", "length", 2.0, lo=0.0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:328'),
        _degree_field(), *_sections(1, 1)],
        _nurbs('NURBS_CONE', _cyl_build), missing=(_VIEW, "Caps: None only, Extra transform on caps (no cap surface)",
                                                   _TOL), translation_context='MWK:operators/option_windows_prims.py:326'),
    Window("nurbs_plane", "NURBS Plane Options", "Create", ("allset.create", {"kind": 'NURBS_PLANE'}), [
        *_pivot_fields(), *_axis_fields(),
        F("width", "Width:", "length", 1.0, lo=0.0001, hi=1000, translation_context='MWK:operators/option_windows_prims.py:334'), F("length", "Length:", "length", 1.0, lo=0.0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:334'),
        _degree_field(items=("1 Linear", "3 Cubic")),
        F("patches_u", "U patches:", "int", 1, lo=1, hi=500, translation_context='MWK:operators/option_windows_prims.py:336'), F("patches_v", "V patches:", "int", 1, lo=1, hi=500, translation_context='MWK:operators/option_windows_prims.py:336')],
        _nurbs('NURBS_PLANE', _plane_build), missing=(_VIEW, _DEG_MORE), translation_context='MWK:operators/option_windows_prims.py:332'),
    Window("nurbs_torus", "NURBS Torus Options", "Create", ("allset.create", {"kind": 'NURBS_TORUS'}), [
        *_pivot_fields(), *_axis_fields(), *_sweep_fields(),
        F("minor_sweep", "Minor sweep angle:", "float", 360.0, lo=-3600.0, hi=3600.0, translation_context='MWK:operators/option_windows_prims.py:340'),
        F("radius", "Radius:", "length", 1.0, lo=0.0001, hi=1000, translation_context='MWK:operators/option_windows_prims.py:341'),
        F("minor_radius", "Minor radius:", "length", 0.5, lo=0.0, hi=1000, translation_context='MWK:operators/option_windows_prims.py:342'), _degree_field(), *_sections(4, 4)],
        _nurbs('NURBS_TORUS', _torus_build), missing=(_VIEW, _TOL), translation_context='MWK:operators/option_windows_prims.py:338'),
    # Circle: the pivot point is the circle's centre (circle -c), the normal axis its normal (-nr)
    Window("nurbs_circle", "NURBS Circle Options", "Create", ("allset.create", {"kind": 'NURBS_CIRCLE'}), [
        *_pivot_fields(), *_axis_fields("Normal axis:", "Normal definition:"),
        F("sweep", "Sweep angle:", "float", 360.0, lo=-3600.0, hi=3600.0, translation_context='MWK:operators/option_windows_prims.py:347'),
        F("radius", "Radius:", "length", 1.0, lo=0.0001, hi=1000, translation_context='MWK:operators/option_windows_prims.py:348'), _degree_field("Degree:"), *_sections()],
        _run_circle, missing=("Normal axis: Active view", _TOL), translation_context='MWK:operators/option_windows_prims.py:345'),
    # Square (Maya factory): centre, normal Y, sides 1 x 1, 1 span per side, degree 3
    Window("nurbs_square", "NURBS Square Options", "Create", ("allset.create", {"kind": 'NURBS_SQUARE'}), [
        F("center", "Center:", "vec3", (0.0, 0.0, 0.0), translation_context='MWK:operators/option_windows_prims.py:352'), *_axis_fields("Normal axis:", "Normal definition:"),
        F("side1", "Length of Side 1:", "length", 1.0, lo=0.1, hi=1000, translation_context='MWK:operators/option_windows_prims.py:353'),
        F("side2", "Length of Side 2:", "length", 1.0, lo=0.1, hi=1000, translation_context='MWK:operators/option_windows_prims.py:354'),
        F("spans_per_side", "Spans per side:", "int", 1, lo=1, hi=200, translation_context='MWK:operators/option_windows_prims.py:355'),
        _degree_field("Curve degree:", items=("1", "3"))],
        _run_square, missing=("Normal axis: Active view", "Curve degree: 2 / 5 / 7 (1 and 3 only)"), translation_context='MWK:operators/option_windows_prims.py:351'),
]

# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 196 (issue #103) lane B: Maya option windows that were Blender's Adjust Last Operation ("redo") or the generic
"no settings" window — Create Character Set / Subcharacter Set, Curves Cut / Detach / Reverse Direction / Smooth (both)
/ Straighten, the circular arc tools, UV Merge UVs / Contour Stretch, Set / Assume Preferred Angle, Add Influence.

Same spec as operators/option_windows.py (``F`` fields, ``Window`` = one ``allset.opt_<key>`` operator, bound to its
menu paths; option_windows._extend appends ``WINDOWS``). Titles, buttons, labels and factory values come from Maya
2022's option windows; fields the kit
can't honour are only listed (``missing``), never faked. Every window run with its defaults does what the plain menu
item does; Merge UVs / Smooth (Modify section) run the kit's Maya operators, like their plain menu items
(menu_map, step 196).
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy

from .option_windows import F, Window, _op
from .option_windows_rig import FText

# --- run helpers ---------------------------------------------------------------------------------------

_ATTRS = {"All keyable": 'ALL', "From Channel Box": 'CHANNEL_BOX', "All keyable except:": 'EXCEPT'}


def _character(sub):
    def run(context, v):
        return bpy.ops.allset.character_create(
            'EXEC_DEFAULT', sub=sub, character_name=v["name"], attributes=_ATTRS[v["attributes"]],
            exclude_translate=v["no_translate"], exclude_rotate=v["no_rotate"], exclude_scale=v["no_scale"],
            exclude_visibility=v["no_visibility"], exclude_dynamic=v["no_dynamic"],
            hierarchy=v.get("hierarchy", False))
    return run


def _run_cut(context, v):
    return bpy.ops.allset.curve_cut('EXEC_DEFAULT', last_only=v["cut"] == "Using last curve",
                                    keep_longest=v["keep"] == "Longest segments")


def _run_detach(context, v):
    return bpy.ops.allset.curve_detach('EXEC_DEFAULT')


def _keep_copies(context, suffix):
    """Maya Keep original (object mode): the selected curves are duplicated, the copies — named
    ``<curve><suffix>N`` (``curveAreversedCurve1``, ``curveAsmoothCurve1``) — become the selection and get the
    command; the originals stay unchanged."""
    from . import naming
    if context.mode != 'OBJECT':
        return
    originals = [o for o in context.selected_objects if o.type == 'CURVE']
    for o in context.selected_objects:
        if o.type != 'CURVE':
            o.select_set(False)
    copies = []
    for o in originals:
        c = o.copy()
        c.data = o.data.copy()
        for coll in o.users_collection:
            coll.objects.link(c)
        naming.apply_maya_name(c, f"{o.name}{suffix}")
        o.select_set(False)
        c.select_set(True)
        copies.append(c)
    if copies:
        context.view_layer.objects.active = copies[-1]


def _run_reverse(context, v):
    """Curves > Reverse Direction: Blender's Switch Direction in edit mode (the plain item); in object mode every
    selected curve is reversed whole (CVs reversed, knots mirrored)."""
    if v["keep_original"]:
        _keep_copies(context, "reversedCurve")
    if context.mode == 'EDIT_CURVE':
        return _op("curve.switch_direction")
    from . import curves_maya as cmaya
    from . import curves_math as cm
    obs = [o for o in context.selected_objects if o.type == 'CURVE']
    if not obs:
        raise RuntimeError("Select curves to reverse")
    for ob in obs:
        out = []
        for sp in ob.data.splines:
            c = cmaya.read_spline(sp)
            if sp.type != 'BEZIER':
                res = cm.reverse(c.cvs, c.knots, c.weights)
                c = cmaya.MCurve(res[0], res[1], c.degree, res[2] if len(res) > 2 else None, c.periodic)
            out.append(c)
        cmaya._replace_splines(ob, out)
    return {'FINISHED'}


def _run_smooth_curves(context, v):
    return bpy.ops.allset.curve_smooth_curves('EXEC_DEFAULT', factor=v["factor"])


def _run_smooth_curve(context, v):
    """Curves > Smooth (Edit section): Blender's curve Smooth on the selected points (the plain item); Keep original
    smooths copies (all their points)."""
    if not v["keep_original"] or context.mode != 'OBJECT':
        return _op("curve.smooth")
    _keep_copies(context, "smoothCurve")
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bpy.ops.curve.select_all(action='SELECT')
        return _op("curve.smooth")
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')


def _run_straighten(context, v):
    return bpy.ops.allset.curve_straighten('EXEC_DEFAULT', straightness=v["straightness"],
                                           preserve_length=v["preserve_length"])


def _arc(op_name):
    def run(context, v):
        op = getattr(bpy.ops.allset, op_name)
        return op('INVOKE_DEFAULT', degree=1 if v["degree"].startswith("1") else 3, sections=v["sections"])
    return run


def _run_merge_uvs(context, v):
    return bpy.ops.allset.uv_merge('EXEC_DEFAULT', distance=v["threshold"])


def _run_contour(context, v):
    return bpy.ops.allset.uv_contour('EXEC_DEFAULT')


def _preferred(op_name):
    def run(context, v):
        return getattr(bpy.ops.allset, op_name)('EXEC_DEFAULT', hierarchy=v["options"] == "Hierarchy")
    return run


def _run_add_influence(context, v):
    return bpy.ops.allset.add_influence('EXEC_DEFAULT', lock_weights=v["lock_weights"],
                                        default_weight=v["default_weight"])


# --- windows -------------------------------------------------------------------------------------------

_INCLUDE = ("All keyable", "From Channel Box", "All keyable except:")
_KEEP_ORIGINAL = "Keep original (Maya keeps the input curve and makes new ones)"

WINDOWS = [
    # Create Character Set Options (factory values, window)
    Window("character_set", "Create Character Set Options", "Create Character Set", None, [
        FText("name", "Name:", "character1"),
        F("hierarchy", "Include:", "bool", False, text=_zh_native("Hierarchy below selected node", 'MWK:operators/option_windows_misc196.py:152'), translation_context='MWK:operators/option_windows_misc196.py:152'),
        F("attributes", "Include:", "enum", "All keyable except:", items=_INCLUDE, translation_context='MWK:operators/option_windows_misc196.py:153'),
        F("no_translate", "", "bool", False, text=_zh_native("Translate", 'MWK:operators/option_windows_misc196.py:154'), translation_context='MWK:operators/option_windows_misc196.py:154'),
        F("no_rotate", "", "bool", False, text=_zh_native("Rotate", 'MWK:operators/option_windows_misc196.py:155'), translation_context='MWK:operators/option_windows_misc196.py:155'),
        F("no_scale", "", "bool", True, text=_zh_native("Scale", 'MWK:operators/option_windows_misc196.py:156'), translation_context='MWK:operators/option_windows_misc196.py:156'),
        F("no_visibility", "", "bool", True, text=_zh_native("Visibility", 'MWK:operators/option_windows_misc196.py:157'), translation_context='MWK:operators/option_windows_misc196.py:157'),
        F("no_dynamic", "", "bool", False, text=_zh_native("Dynamic", 'MWK:operators/option_windows_misc196.py:158'), translation_context='MWK:operators/option_windows_misc196.py:158'),
    ], _character(False), paths=("Control/Create Character Set", "Key/Create Character Set"),
        missing=("Redirection: Redirect character (Rotation and translation / Rotation only / Translation only)",), translation_context='MWK:operators/option_windows_misc196.py:150'),
    # Create Subcharacter Set Options (no hierarchy, no redirection)
    Window("subcharacter_set", "Create Subcharacter Set Options", "Create Subcharacter Set", None, [
        FText("name", "Name:", "subCharacter1"),
        F("attributes", "Subcharacter set attributes:", "enum", "All keyable except:", items=_INCLUDE, translation_context='MWK:operators/option_windows_misc196.py:164'),
        F("no_translate", "", "bool", False, text=_zh_native("No translate", 'MWK:operators/option_windows_misc196.py:165'), translation_context='MWK:operators/option_windows_misc196.py:165'),
        F("no_rotate", "", "bool", False, text=_zh_native("No rotate", 'MWK:operators/option_windows_misc196.py:166'), translation_context='MWK:operators/option_windows_misc196.py:166'),
        F("no_scale", "", "bool", True, text=_zh_native("No scale", 'MWK:operators/option_windows_misc196.py:167'), translation_context='MWK:operators/option_windows_misc196.py:167'),
        F("no_visibility", "", "bool", True, text=_zh_native("No visibility", 'MWK:operators/option_windows_misc196.py:168'), translation_context='MWK:operators/option_windows_misc196.py:168'),
        F("no_dynamic", "", "bool", False, text=_zh_native("No dynamic", 'MWK:operators/option_windows_misc196.py:169'), translation_context='MWK:operators/option_windows_misc196.py:169'),
    ], _character(True), paths=("Control/Create Subcharacter Set", "Key/Create Subcharacter Set"), translation_context='MWK:operators/option_windows_misc196.py:162'),
    # Cut Curve Options (factory 1 / 2, Cut / Keep radios, title)
    Window("cut_curve", "Cut Curve Options", "Cut", None, [
        F("cut", "Cut:", "enum", "At all intersections", items=("At all intersections", "Using last curve"), translation_context='MWK:operators/option_windows_misc196.py:173'),
        F("keep", "Keep:", "enum", "All curve segments", items=("Longest segments", "All curve segments"), translation_context='MWK:operators/option_windows_misc196.py:174'),
    ], _run_cut, paths=("Curves/Cut",),
        missing=("Find intersections: In 2D and 3D / In 3D only / Use direction (the kit finds 3D crossings)",
                 "Keep: Segments with curve points", "Use tolerance: Global / Local, Tolerance 0.0001",
                 _KEEP_ORIGINAL), translation_context='MWK:operators/option_windows_misc196.py:172'),
    # Detach Curves Options
    Window("detach_curves", "Detach Curves Options", "Detach", None, [], _run_detach, paths=("Curves/Detach",),
           missing=(_KEEP_ORIGINAL,), translation_context='MWK:operators/option_windows_misc196.py:180'),
    # Reverse Curve Options
    Window("reverse_curve", "Reverse Curve Options", "Reverse", None, [
        F("keep_original", "", "bool", False, text=_zh_native("Keep original", 'MWK:operators/option_windows_misc196.py:184'), translation_context='MWK:operators/option_windows_misc196.py:184'),
    ], _run_reverse, paths=("Curves/Reverse Direction",), translation_context='MWK:operators/option_windows_misc196.py:183'),
    # Smooth Curves Options (factor 4)
    Window("smooth_curves", "Smooth Curves Options", "Smooth Curves", None, [
        F("factor", "Smooth factor:", "int", 4, lo=1, hi=100, translation_context='MWK:operators/option_windows_misc196.py:188'),
    ], _run_smooth_curves, paths=("Curves/Smooth", "nHair/Modify Curves/Smooth"), translation_context='MWK:operators/option_windows_misc196.py:187'),
    # Smooth Curve Options (Edit section Smooth = smoothCurve)
    Window("smooth_curve", "Smooth Curve Options", "Smooth", None, [
        F("keep_original", "", "bool", False, text=_zh_native("Keep original", 'MWK:operators/option_windows_misc196.py:192'), translation_context='MWK:operators/option_windows_misc196.py:192'),
    ], _run_smooth_curve, paths=("Curves/Smooth#2",),
        missing=("Smoothness: 10.0 (Maya's smoothCurve; the kit runs Blender's curve Smooth)",), translation_context='MWK:operators/option_windows_misc196.py:191'),
    # Straighten Curves Options
    Window("straighten_curves", "Straighten Curves Options", "Straighten Curves", None, [
        F("straightness", "Straightness:", "float", 1.0, lo=0.0, hi=2.0, translation_context='MWK:operators/option_windows_misc196.py:197'),
        F("preserve_length", "", "bool", True, text=_zh_native("Preserve length", 'MWK:operators/option_windows_misc196.py:198'), translation_context='MWK:operators/option_windows_misc196.py:198'),
    ], _run_straighten, paths=("Curves/Straighten", "nHair/Modify Curves/Straighten"), translation_context='MWK:operators/option_windows_misc196.py:196'),
    # Tool Settings "Three / Two Point Arc Settings" (window = tool name,
    # its button starts the tool, like step 140's tool boxes)
    Window("arc3_tool", "Three Point Arc Settings", "Create Arc", None, [
        F("degree", "Circular arc degree:", "enum", "3", items=("1 Linear", "3"), translation_context='MWK:operators/option_windows_misc196.py:203'),
        F("sections", "Sections:", "int", 8, lo=4, hi=200, translation_context='MWK:operators/option_windows_misc196.py:204'),
    ], _arc("arc3_tool"), paths=("Create/Curve Tools/Three Point Circular Arc",), translation_context='MWK:operators/option_windows_misc196.py:202'),
    Window("arc2_tool", "Two Point Arc Settings", "Create Arc", None, [
        F("degree", "Circular arc degree:", "enum", "3", items=("1 Linear", "3"), translation_context='MWK:operators/option_windows_misc196.py:207'),
        F("sections", "Sections:", "int", 8, lo=4, hi=200, translation_context='MWK:operators/option_windows_misc196.py:208'),
    ], _arc("arc2_tool"), paths=("Create/Curve Tools/Two Point Circular Arc",), translation_context='MWK:operators/option_windows_misc196.py:206'),
    # Merge UVs Options (factory 0.01)
    Window("merge_uvs", "Merge UVs Options", "Merge UVs", None, [
        F("threshold", "Threshold:", "float", 0.01, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_misc196.py:212'),
    ], _run_merge_uvs, paths=("UV/Merge UVs",), translation_context='MWK:operators/option_windows_misc196.py:211'),
    # Contour Stretch Mapping Options
    Window("contour_stretch", "Contour Stretch Mapping Options", "Project", None, [], _run_contour,
           paths=("UV/Contour Stretch",),
           missing=("Method: Walk Contours / NURBS Projection (the kit follows the quad grid)",
                    "Smoothness 0-3, Offset 0-3", "User defined corner vertices",
                    "Insert projection before deformers", "Create new UV Set"), translation_context='MWK:operators/option_windows_misc196.py:215'),
    # Set Preferred Angle Options (factory Hierarchy)
    Window("set_preferred_angle", "Set Preferred Angle Options", "Set", None, [
        F("options", "Options:", "enum", "Hierarchy", items=("Selected joint", "Hierarchy"), translation_context='MWK:operators/option_windows_misc196.py:222'),
    ], _preferred("set_preferred_angle"), paths=("Skeleton/Set Preferred Angle",), translation_context='MWK:operators/option_windows_misc196.py:221'),
    Window("assume_preferred_angle", "Assume Preferred Angle Options", "Assume", None, [
        F("options", "Options:", "enum", "Hierarchy", items=("Selected joint", "Hierarchy"), translation_context='MWK:operators/option_windows_misc196.py:225'),
    ], _preferred("assume_preferred_angle"), paths=("Skeleton/Assume Preferred Angle",), translation_context='MWK:operators/option_windows_misc196.py:224'),
    # Add Influence Options
    Window("add_influence", "Add Influence Options", "Add", None, [
        F("lock_weights", "Weight locking:", "bool", False, text=_zh_native("Lock weights", 'MWK:operators/option_windows_misc196.py:229'), translation_context='MWK:operators/option_windows_misc196.py:229'),
        F("default_weight", "Default weight:", "float", 0.0, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_misc196.py:230'),
    ], _run_add_influence, paths=("Skin/Edit Influences/Add Influence",),
        missing=("Geometry: Use geometry", "Dropoff: 4.0 (Maya weighs an unlocked influence by distance; the kit adds "
                 "it at 0)", "Polygon smoothness: 0.0", "NURBS samples: 10"), translation_context='MWK:operators/option_windows_misc196.py:228'),
]

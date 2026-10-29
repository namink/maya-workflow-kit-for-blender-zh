# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 140 Maya option windows: modeling, parenting and key commands (issues #33, #35).

Same spec as operators/option_windows.py (``F`` fields, ``Window`` = one ``allset.opt_<key>`` operator); labels and
factory defaults are Maya 2022's; what the values do matches Maya.
option_windows.py appends ``WINDOWS`` to its own list, so this
module only imports ``F`` / ``Window`` / helpers from it. Maya fields Blender can't honour are listed in ``missing``
(drawn greyed), never as fields. Plan / decisions: docs/steps/step_140.md, docs/steps/step_140_edit.md.
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import math

import bpy
from mathutils import Vector

from .option_windows import F, Window, _components, _k  # noqa: F401  (option_windows imports this module at its end)

# --- key commands (Key / Edit > Keys) -------------------------------

_OBJECTS = F("objects", "Objects:", "enum", "Selected", items=("Selected", "All"), translation_context='MWK:operators/option_windows_edit.py:22')


def _scope_fields(objects=True):
    """The rows every Maya key command window starts with."""
    return ([_OBJECTS] if objects else []) + [
        F("hierarchy", "Hierarchy:", "enum", "Selected", items=("Selected", "Below"), translation_context='MWK:operators/option_windows_edit.py:28'),
        F("channels", "Channels:", "enum", "All keyable", items=("All keyable", "From Channel Box"), translation_context='MWK:operators/option_windows_edit.py:29'),
        F("driven", "Driven channels:", "bool", False, translation_context='MWK:operators/option_windows_edit.py:30'),
        F("shapes", "Shapes:", "bool", True, translation_context='MWK:operators/option_windows_edit.py:31'),
        F("time_range", "Time range:", "enum", "All", items=("All", "Start/End", "Time Slider"), translation_context='MWK:operators/option_windows_edit.py:32'),
        F("start", "Start time:", "float", 0.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:33'),
        F("end", "End time:", "float", 10.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:34')]


# Control points (keys on CVs / vertices) have no Blender counterpart: a mesh vertex isn't an animatable channel
_CONTROL_POINTS = "Control points (Blender animates no vertices: shape keys are the Shapes)"


def _tk():
    from . import time_keys
    return time_keys


def _scope(context, v):
    tk = _tk()
    scope = tk.KeyScope.of(v)
    if not tk.scope_nodes(context, scope):
        raise RuntimeError("Nothing selected.")
    return scope


def _done(context):
    for area in context.screen.areas if context.screen else ():
        area.tag_redraw()
    return {'FINISHED'}


def _gkm():
    from . import graph_key_menu
    return graph_key_menu


def _on_selected(context, v):
    """Maya fromGraphEditor rule (Cut / Copy / Paste Keys & co.): a key window opened from a Graph Editor / Dope Sheet
    menu with keys selected and Method Keys acts on those keys, not on the nodes' time range (step 157)."""
    g = _gkm()
    return g.in_key_editor(context) and v.get("method", "Keys") == "Keys" and g.has_selected_keys(context)


def _run_delete(context, v):
    if _on_selected(context, v):
        _gkm().delete_selected(context)
        return _done(context)
    _tk().delete_scope(context, _scope(context, v), v["method"], v["adjustment"], v["connect"])
    return _done(context)


def _run_cut(context, v):
    if _on_selected(context, v):
        _gkm().cut_selected(context)
        return _done(context)
    _tk().delete_scope(context, _scope(context, v), v["method"], v["adjustment"], v["connect"], clipboard=True)
    return _done(context)


def _run_copy(context, v):
    if _on_selected(context, v):
        _gkm().copy_selected(context)
        return _done(context)
    _tk().copy_scope(context, _scope(context, v), v["method"])
    return _done(context)


def _run_paste(context, v):
    g = _gkm()
    if g.in_key_editor(context) and g.editor_clipboard():
        # the editor's own key buffer (Edit > Copy / Cut there); Start / Start/End paste at the current time too
        if not g.paste_editor(context, time_range=v["time_range"], time_offset=v["time_offset"],
                              value_offset=v["value_offset"], copies=v["copies"], method=v["method"]):
            raise RuntimeError("Nothing to paste: copy or cut keys first.")
        return _done(context)
    tk = _tk()
    if not tk._CLIPBOARD.get("nodes"):
        raise RuntimeError("The animation clipboard is empty: copy or cut keys first.")
    if not tk.nodes(context):
        raise RuntimeError("Nothing selected.")
    tk.paste_scope(context, time_range=v["time_range"], start=v["start"], end=v["end"], time_offset=v["time_offset"],
                   value_offset=v["value_offset"], copies=v["copies"], method=v["method"],
                   replace_region=v["replace_region"])
    return _done(context)


def _run_scale(context, v):
    if _gkm().in_key_editor(context) and _gkm().has_selected_keys(context):
        _gkm().scale_selected(context, v["method"], v["time_scale"], v["time_pivot"], v["value_scale"],
                              v["value_pivot"], v["new_start"], v["new_end"])
        return _done(context)
    _tk().scale_scope(context, _scope(context, v), v["method"], v["only_specified"], v["time_scale"], v["time_pivot"],
                      v["value_scale"], v["value_pivot"], v["new_start"], v["new_end"])
    return _done(context)


def _run_snap(context, v):
    if _gkm().in_key_editor(context) and _gkm().has_selected_keys(context):
        _gkm().snap_selected(context, v["snap"], v["time_multiple"], v["value_multiple"])
        return _done(context)
    _tk().snap_scope(context, _scope(context, v), v["snap"], v["time_multiple"], v["value_multiple"])
    return _done(context)


def _paths(command, edit):
    """Main-menu paths of a key window + the Graph Editor / Dope Sheet Edit menu box (step 157)."""
    return (f"Key/{command}", f"Edit/Keys/{command}", f"Graph Editor/Edit/{edit}", f"Dope Sheet/Edit/{edit}")


_DELETE_TAIL = [
    F("method", "Method:", "enum", "Keys", items=("Keys", "Segments"), translation_context='MWK:operators/option_windows_edit.py:139'),
    F("adjustment", "Adjustment:", "enum", "None", items=("None", "Collapse"), translation_context='MWK:operators/option_windows_edit.py:140'),
    F("connect", "Connect:", "bool", False, translation_context='MWK:operators/option_windows_edit.py:141')]

KEY_WINDOWS = [
    Window("delete_keys", "Delete Keys Options", "Delete Keys", None, _scope_fields() + _DELETE_TAIL, _run_delete,
           paths=_paths("Delete Keys", "Delete"), missing=(_CONTROL_POINTS,), translation_context='MWK:operators/option_windows_edit.py:144'),
    Window("cut_keys", "Cut Keys Options", "Cut Keys", None, _scope_fields(objects=False) + _DELETE_TAIL, _run_cut,
           paths=_paths("Cut Keys", "Cut"),
           missing=(_CONTROL_POINTS, "Method: Range (cutKey has no area option)"), translation_context='MWK:operators/option_windows_edit.py:146'),
    Window("copy_keys", "Copy Keys Options", "Copy Keys", None, _scope_fields(objects=False) + [
        F("method", "Method:", "enum", "Keys", items=("Keys", "Segments"), translation_context='MWK:operators/option_windows_edit.py:150')], _run_copy,
        paths=_paths("Copy Keys", "Copy"),
        missing=(_CONTROL_POINTS, "Method: Range (copyKey has no area option)"), translation_context='MWK:operators/option_windows_edit.py:149'),
    Window("paste_keys", "Paste Keys Options", "Paste Keys", None, [
        F("time_range", "Time range:", "enum", "Current", items=("Start", "Start/End", "Current", "Clipboard"), translation_context='MWK:operators/option_windows_edit.py:154'),
        F("start", "Start time:", "float", 0.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:155'), F("end", "End time:", "float", 10.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:155'),
        F("time_offset", "Time offset:", "float", 0.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:156'),
        F("value_offset", "Value offset:", "float", 0.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:157'),
        F("copies", "Copies:", "int", 1, lo=1, hi=100, translation_context='MWK:operators/option_windows_edit.py:158'),
        F("method", "Paste method:", "enum", "Merge", items=("Insert", "Replace", "Merge"), translation_context='MWK:operators/option_windows_edit.py:159'),
        F("replace_region", "Replace region:", "enum", "Time range", items=("Time range", "Entire curve"), translation_context='MWK:operators/option_windows_edit.py:160')],
        _run_paste, paths=_paths("Paste Keys", "Paste"),
        missing=("Selected keys override specified time range", "Clipboard adjustment: Scale / Fit (Preserve only)",
                 "Connect"), translation_context='MWK:operators/option_windows_edit.py:153'),
    Window("scale_keys", "Scale Keys Options", "Scale Keys", None, _scope_fields() + [
        F("method", "Method:", "enum", "Scale/Pivot", items=("Scale/Pivot", "Start/End"), translation_context='MWK:operators/option_windows_edit.py:165'),
        F("only_specified", "", "bool", True, text=_zh_native("Only scale specified keys", 'MWK:operators/option_windows_edit.py:166'), translation_context='MWK:operators/option_windows_edit.py:166'),
        F("time_scale", "Time scale:", "float", 1.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:167'),
        F("time_pivot", "Time pivot:", "float", 0.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:168'),
        F("value_scale", "Value scale:", "float", 1.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:169'),
        F("value_pivot", "Value pivot:", "float", 0.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:170'),
        F("new_start", "New start time:", "float", 1.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:171'),
        F("new_end", "New end time:", "float", 10.0, lo=-1e6, hi=1e6, translation_context='MWK:operators/option_windows_edit.py:172')], _run_scale,
        paths=_paths("Scale Keys", "Scale"), missing=(_CONTROL_POINTS,), translation_context='MWK:operators/option_windows_edit.py:164'),
    Window("snap_keys", "Snap Keys Options", "Snap Keys", None, _scope_fields() + [
        F("snap", "Snap:", "enum", "Times", items=("Times", "Values", "Both"), translation_context='MWK:operators/option_windows_edit.py:175'),
        F("time_multiple", "Snap times to multiple of:", "float", 1.0, lo=0.0, hi=1000.0, translation_context='MWK:operators/option_windows_edit.py:176'),
        F("value_multiple", "Snap values to multiple of:", "float", 1.0, lo=0.0, hi=1000.0, translation_context='MWK:operators/option_windows_edit.py:177')], _run_snap,
        paths=_paths("Snap Keys", "Snap"), missing=(_CONTROL_POINTS,), translation_context='MWK:operators/option_windows_edit.py:174'),
]


# --- Edit menu --------------------------------------------------------------

def _run_parent(context, v):
    return bpy.ops.allset.parent('EXEC_DEFAULT', preserve_position=v["preserve"])


def _run_unparent(context, v):
    return bpy.ops.allset.unparent('EXEC_DEFAULT', preserve_position=v["preserve"])


def _run_ungroup(context, v):
    if not any(ob.children for ob in context.selected_objects):
        raise RuntimeError("Select a group to ungroup.")
    return bpy.ops.allset.ungroup('EXEC_DEFAULT', under='WORLD' if v["under"] == "World" else 'PARENT',
                                  preserve_position=v["preserve"])


def _run_duplicate_special(context, v):
    if v["smart"]:
        # Smart transform: each copy repeats the transform between the last duplicate and its source (the kit's
        # Duplicate with Transform, Shift+D); the offsets below are Maya's for non-smart copies only
        res = {'CANCELLED'}
        for _i in range(max(1, v["copies"])):
            res = bpy.ops.allset.duplicate_with_transform('EXEC_DEFAULT')
            if res != {'FINISHED'}:
                break
        return res
    k = _k(context)
    return bpy.ops.allset.duplicate_special(
        'EXEC_DEFAULT', geometry_type=v["geometry_type"].upper(),
        group_under={"Parent": 'PARENT', "World": 'WORLD', "New group": 'NEW_GROUP'}[v["group_under"]],
        # Maya Y up: Maya Y -> Blender Z, Maya Z -> Blender -Y (CLAUDE.md step 57)
        translate=Vector((v["translate"][0], -v["translate"][2], v["translate"][1])) * k,
        rotate=tuple(math.radians(a) for a in (v["rotate"][0], -v["rotate"][2], v["rotate"][1])),
        scale=(v["scale"][0], v["scale"][2], v["scale"][1]), copies=v["copies"])


_PRESERVE = F("preserve", "", "bool", True, text=_zh_native("Preserve position", 'MWK:operators/option_windows_edit.py:219'), translation_context='MWK:operators/option_windows_edit.py:219')

EDIT_WINDOWS = [
    Window("parent", "Parent Options", "Parent", ("allset.parent", {}), [_PRESERVE], _run_parent,
           paths=("Edit/Parent",), missing=("Parent method: Add instance (Blender objects have one parent)",), translation_context='MWK:operators/option_windows_edit.py:222'),
    Window("unparent", "Unparent Options", "Unparent", ("allset.unparent", {}), [_PRESERVE], _run_unparent,
           paths=("Edit/Unparent",), missing=("Unparent method: Remove instance",), translation_context='MWK:operators/option_windows_edit.py:224'),
    Window("ungroup", "Ungroup Options", "Ungroup", ("allset.ungroup", {}), [
        F("under", "Ungroup under:", "enum", "Parent", items=("Parent", "World"), translation_context='MWK:operators/option_windows_edit.py:227'), _PRESERVE], _run_ungroup,
        paths=("Edit/Ungroup",), translation_context='MWK:operators/option_windows_edit.py:226'),
    # step 103's window (option_windows.py "duplicate_special") plus Smart transform, which the kit has
    # too; the main loop deletes the old spec at merge
    Window("duplicate_special_maya", "Duplicate Special Options", "Duplicate Special", None, [
        F("geometry_type", "Geometry type:", "enum", "Copy", items=("Copy", "Instance"), translation_context='MWK:operators/option_windows_edit.py:232'),
        F("group_under", "Group under:", "enum", "Parent", items=("Parent", "World", "New group"), translation_context='MWK:operators/option_windows_edit.py:233'),
        F("smart", "", "bool", False, text=_zh_native("Smart transform", 'MWK:operators/option_windows_edit.py:234'), translation_context='MWK:operators/option_windows_edit.py:234'),
        F("translate", "Translate:", "vec3", (0.0, 0.0, 0.0), translation_context='MWK:operators/option_windows_edit.py:235'), F("rotate", "Rotate:", "vec3", (0.0, 0.0, 0.0), translation_context='MWK:operators/option_windows_edit.py:235'),
        F("scale", "Scale:", "vec3", (1.0, 1.0, 1.0), translation_context='MWK:operators/option_windows_edit.py:236'), F("copies", "Number of copies:", "int", 1, lo=1, hi=1000, translation_context='MWK:operators/option_windows_edit.py:236')],
        _run_duplicate_special, paths=("Edit/Duplicate Special",),
        missing=("Duplicate input graph", "Duplicate input connections", "Instance leaf nodes",
                 "Assign unique name to children nodes"), translation_context='MWK:operators/option_windows_edit.py:231'),
]


# --- Edit Mesh / Mesh Tools ------------------------------------------------

def _edit_only(context):
    from .poly_maya import CONNECT_WARNING
    if context.mode != 'EDIT_MESH':
        raise RuntimeError(CONNECT_WARNING)       # Maya warns on an object (menu_map.OBJECT_MODE)


def _run_connect(context, v):
    _edit_only(context)
    return bpy.ops.allset.connect('EXEC_DEFAULT', insert_with_edge_flow=v["edge_flow"],
                                  adjust_edge_flow=v["adjust_edge_flow"])


def _run_connect_tool(context, v):
    _edit_only(context)
    return bpy.ops.allset.connect('EXEC_DEFAULT', segments=v["segments"], slide=v["slide"])


def _run_circularize(context, v):
    k = _k(context)
    return _components(context, "allset.circularize", 'VERT', normal_offset=v["normal_offset"] * k,
                       radial_offset=v["radial_offset"] * k, twist=math.radians(v["twist"]),
                       evenly_distribute=v["evenly"], divisions=v["divisions"])


def _run_make_hole(context, v):
    if context.mode != 'EDIT_MESH':
        raise RuntimeError("Select the face to cut, then the face whose shape makes the hole.")
    return bpy.ops.allset.make_hole('EXEC_DEFAULT', merge_mode=v["merge_mode"])


_MAINTAIN = {"Relative distance from edge": 'RELATIVE', "Equal distance from edge": 'EQUAL',
             "Multiple edge loops": 'MULTIPLE'}


def insert_edge_loop_options(context, v):
    """Put the Insert Edge Loop window's values on the kit tool's settings (Scene.allset_loop_tools, step 144 LOOP;
    step 140 put them on Blender's Loop Cut tool). Returns the settings."""
    from . import edge_loops
    s = edge_loops.settings(context)
    s.iel_position = _MAINTAIN[v["maintain"]]
    s.iel_loops = v["loops"]
    s.iel_edge_flow = v["edge_flow"]
    s.iel_adjust_flow = v["adjust_edge_flow"]
    s.iel_smoothing = v["smoothing"]
    return s


def offset_edge_loop_options(context, v):
    """The Offset Edge Loop Options values on the kit tool's settings (step 144 LOOP)."""
    from . import edge_loops
    s = edge_loops.settings(context)
    s.oel_delete_edge = v["delete_edge"]
    s.oel_edge_flow = v["edge_flow"]
    s.oel_adjust_flow = v["adjust_edge_flow"]
    s.oel_smoothing = v["smoothing"]
    s.oel_position = _MAINTAIN[v["maintain"]]
    return s


def _run_insert_edge_loop(context, v):
    from . import edge_loops
    insert_edge_loop_options(context, v)
    return bpy.ops.allset.menu_tool('EXEC_DEFAULT', tool=edge_loops.INSERT_TOOL, edit=True)


def _run_offset_edge_loop(context, v):
    """Maya "Enter Tool": the values go to the tool, then the tool starts."""
    from . import edge_loops
    offset_edge_loop_options(context, v)
    return bpy.ops.allset.menu_tool('EXEC_DEFAULT', tool=edge_loops.OFFSET_TOOL, edit=True)


MESH_WINDOWS = [
    Window("connect", "Connect Components Options", "Connect", None, [
        F("edge_flow", "", "bool", False, text=_zh_native("Insert with edge flow", 'MWK:operators/option_windows_edit.py:319'), translation_context='MWK:operators/option_windows_edit.py:319'),
        F("adjust_edge_flow", "Adjust Edge Flow:", "float", 1.0, lo=-1.0, hi=2.0, translation_context='MWK:operators/option_windows_edit.py:320')], _run_connect,
        paths=("Edit Mesh/Connect",), translation_context='MWK:operators/option_windows_edit.py:318'),
    Window("connect_tool", "Connect Tool", "Connect", None, [
        F("slide", "Slide:", "float", 0.5, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_edit.py:323'), F("segments", "Segments:", "int", 1, lo=1, hi=10, translation_context='MWK:operators/option_windows_edit.py:323')],
        _run_connect_tool, paths=("Mesh Tools/Connect",),
        missing=("Pinch", "Active option (MMB drag) / Keyboard and mouse shortcuts"), translation_context='MWK:operators/option_windows_edit.py:322'),
    Window("circularize", "Polygon Circularize Options", "Circularize", ("allset.circularize", {}), [
        F("normal_offset", "Normal Offset:", "length", 0.0, lo=-100.0, hi=100.0, translation_context='MWK:operators/option_windows_edit.py:327'),
        F("radial_offset", "Radial Offset:", "length", 0.0, lo=-100.0, hi=100.0, translation_context='MWK:operators/option_windows_edit.py:328'),
        F("twist", "Twist:", "float", 0.0, lo=-360.0, hi=360.0, translation_context='MWK:operators/option_windows_edit.py:329'),
        F("evenly", "Evenly Distribute:", "bool", True, translation_context='MWK:operators/option_windows_edit.py:330'),
        F("divisions", "Add Divisions:", "int", 0, lo=0, hi=50, translation_context='MWK:operators/option_windows_edit.py:331')], _run_circularize,
        paths=("Edit Mesh/Circularize",),
        missing=("Relax Interior", "Alignment: Automatic / Surface", "Smoothing Angle", "Supporting Edges"), translation_context='MWK:operators/option_windows_edit.py:326'),
    Window("make_hole", "Make Hole Tool", "Make Hole", None, [
        F("merge_mode", "Merge mode:", "enum", "None",
          items=("First", "Middle", "Second", "Project First", "Project Middle", "Project Second", "None"), translation_context='MWK:operators/option_windows_edit.py:335')],
        _run_make_hole, paths=("Mesh Tools/Make Hole",), translation_context='MWK:operators/option_windows_edit.py:334'),
    Window("insert_edge_loop", "Insert Edge Loop Tool", "Insert Edge Loop", None, [
        F("maintain", "Maintain position:", "enum", "Relative distance from edge",
          items=("Relative distance from edge", "Equal distance from edge", "Multiple edge loops"), translation_context='MWK:operators/option_windows_edit.py:339'),
        F("loops", "Number of edge loops:", "int", 2, lo=1, hi=100, translation_context='MWK:operators/option_windows_edit.py:341'),
        F("edge_flow", "", "bool", False, text=_zh_native("Insert with edge flow", 'MWK:operators/option_windows_edit.py:342'), translation_context='MWK:operators/option_windows_edit.py:342'),
        F("adjust_edge_flow", "Adjust Edge Flow:", "float", 1.0, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_edit.py:343'),
        F("smoothing", "Smoothing angle:", "float", 30.0, lo=0.0, hi=180.0, translation_context='MWK:operators/option_windows_edit.py:344')], _run_insert_edge_loop,
        paths=("Mesh Tools/Insert Edge Loop",),
        missing=("Use Equal Multiplier (always on)", "Auto complete (always on)", "Fix Quads (always on)"), translation_context='MWK:operators/option_windows_edit.py:338'),
    # step 144 LOOP: Maya's box is a window with Enter Tool And Close / Enter Tool / Close
    Window("offset_edge_loop", "Offset Edge Loop Options", "Enter Tool And Close", None, [
        F("delete_edge", "", "bool", True, text=_zh_native("Delete edge (maintain 4-sided polygons)", 'MWK:operators/option_windows_edit.py:349'), translation_context='MWK:operators/option_windows_edit.py:349'),
        F("edge_flow", "", "bool", False, text=_zh_native("Insert with edge flow", 'MWK:operators/option_windows_edit.py:350'), translation_context='MWK:operators/option_windows_edit.py:350'),
        F("adjust_edge_flow", "Adjust Edge Flow:", "float", 1.0, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_edit.py:351'),
        F("smoothing", "Smoothing angle:", "float", 180.0, lo=0.0, hi=180.0, translation_context='MWK:operators/option_windows_edit.py:352'),
        F("maintain", "Maintain position:", "enum", "Relative distance from edge",
          items=("Relative distance from edge", "Equal distance from edge"), translation_context='MWK:operators/option_windows_edit.py:353')], _run_offset_edge_loop,
        paths=("Mesh Tools/Offset Edge Loop",), apply_text="Enter Tool",
        missing=("Start/End vertex offset (0)", "Tool completion: Press enter (the loops are made on release)"), translation_context='MWK:operators/option_windows_edit.py:348'),
]

# --- Edit > Delete by Type > Non-Deformer History ❒ (step 162) ---------------------------------------------------
# Maya 2022 "Delete Non Deformer History Options": Delete: All non-deformer history (factory, optionVar
# bakePreDefHistory 0) /
# History before deformers only; buttons Delete / Apply / Close.
NONDEF_ALL = "All non-deformer history"
NONDEF_PRE = "History before deformers only"


def _run_non_deformer(context, v):
    return bpy.ops.allset.delete_history('EXEC_DEFAULT', non_deformer=True, before_only=v["delete"] == NONDEF_PRE)


HISTORY_WINDOWS = [
    Window("non_deformer_history", "Delete Non Deformer History Options", "Delete", None, [
        F("delete", "Delete:", "enum", NONDEF_ALL, items=(NONDEF_ALL, NONDEF_PRE), translation_context='MWK:operators/option_windows_edit.py:373')], _run_non_deformer,
        paths=("Edit/Delete by Type/Non-Deformer History",), translation_context='MWK:operators/option_windows_edit.py:372'),
]

WINDOWS = KEY_WINDOWS + EDIT_WINDOWS + MESH_WINDOWS + HISTORY_WINDOWS

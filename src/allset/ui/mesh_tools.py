# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Target Weld and Crease Tool as Blender tools, and Maya's Multi-Cut Tool Settings (docs/steps/step_64.md 「계획」).

- Target Weld (Maya Mesh Tools > Target Weld): LMB press on a
  vertex / edge starts ``allset.target_weld``; a press away from them falls back to the select tool.
- Crease Tool (Mesh Tools > Crease Tool): MMB drag = ``allset.crease_drag``; LMB selects (fallback).
- Multi-Cut (step 129, docs/steps/step_129_multicut.md): the kit tool ``allset.multi_cut_tool`` running
  ``allset.multi_cut`` (operators/multi_cut.py); its Tool Settings are Maya's.
Settings live in ``Scene.allset_mesh_tools`` (operators/mesh_tools.py).
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy

from . import notices
from ..operators import cut_sew, mesh_tools, multi_cut

# Greyed Maya settings: (notice key, label) -> (substitute, one line)
GREY = {
    "Multi-Cut/Edge Flow": (
        "Edge Slide", "New loops are straight: Blender has no edge flow; slide them with G G (Edge Slide)."),
    "Multi-Cut/Color Settings": (
        "Preferences > Themes", "The cut colours are the kit's (yellow points, grey preview, orange loop)."),
    "Multi-Cut/Live Constraint Options": (
        "Snap to Face", "No live surface in Blender: snap with the Face snap while moving the new vertices."),
    "Crease Tool/Extend to creased components": (
        "Select Similar", "Select the creased edges with Select > Select Similar > Crease first."),
}


def _grey(layout, key, text):
    row = layout.row()
    row.enabled = False
    row.operator("allset.menu_unavailable", text=_zh(text, 'MWK:ui/mesh_tools.py:35'), emboss=False).item = key


class ALLSET_TL_target_weld(bpy.types.WorkSpaceTool):
    bl_translation_context = 'MWK:ui/mesh_tools.py:42'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = mesh_tools.TARGET_WELD_TOOL
    bl_label = _zh_native("Target Weld", 'MWK:ui/mesh_tools.py:42')
    bl_description = (_zh_native("Drag a vertex or edge onto the target to merge them (Maya Target Weld). "
                      "A selected vertex takes every selected vertex with it", 'MWK:ui/mesh_tools.py:42'))
    bl_icon = "ops.transform.vert_slide"
    bl_widget = None
    bl_options = {'KEYMAP_FALLBACK'}
    bl_keymap = (("allset.target_weld", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),)

    @staticmethod
    def draw_settings(context, layout, tool):
        s = mesh_tools.settings(context)
        layout.prop(s, "weld_merge_to", expand=True)
        layout.prop(s, "weld_preserve_uvs")


class ALLSET_TL_crease(bpy.types.WorkSpaceTool):
    bl_translation_context = 'MWK:ui/mesh_tools.py:61'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = mesh_tools.CREASE_TOOL
    bl_label = _zh_native("Crease Tool", 'MWK:ui/mesh_tools.py:61')
    bl_description = (_zh_native("Crease the selected edges (vertices in vertex mode): middle-drag left = less, "
                      "right = more (Maya Crease Tool)", 'MWK:ui/mesh_tools.py:61'))
    bl_icon = "ops.transform.shrink_fatten"
    bl_widget = None
    bl_options = {'KEYMAP_FALLBACK'}
    bl_keymap = (("allset.crease_drag", {"type": 'MIDDLEMOUSE', "value": 'PRESS'}, None),)

    @staticmethod
    def draw_settings(context, layout, tool):
        layout.prop(mesh_tools.settings(context), "crease_mode", expand=True)
        if context.region.type != 'TOOL_HEADER':
            _grey(layout, "Crease Tool/Extend to creased components", "Extend to creased components")


class ALLSET_TL_cut_sew(bpy.types.WorkSpaceTool):
    """Maya 3D Cut and Sew UV Tool (docs/steps/step_79.md): drag = cut, Ctrl+drag = sew, Shift+drag = select;
    x / s / d = Cut / Sew / Unfold + Layout (Maya factory hotkeys, tool context polyCutUV)."""
    bl_translation_context = 'MWK:ui/mesh_tools.py:82'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = cut_sew.TOOL
    bl_label = _zh_native("3D Cut and Sew UV Tool", 'MWK:ui/mesh_tools.py:82')
    bl_description = (_zh_native("Drag along edges to cut the UVs there, Ctrl+drag to sew them, Shift+drag to select edges. "
                      "x = Cut, s = Sew, d = Unfold and Layout (Maya 3D Cut and Sew UV Tool)", 'MWK:ui/mesh_tools.py:82'))
    bl_icon = "ops.mesh.knife_tool"
    bl_widget = None
    bl_options = {'KEYMAP_FALLBACK'}
    bl_keymap = (
        ("allset.cut_sew_stroke", {"type": 'LEFTMOUSE', "value": 'PRESS'}, {"properties": [("action", 'CUT')]}),
        ("allset.cut_sew_stroke", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True},
         {"properties": [("action", 'SEW')]}),
        ("allset.cut_sew_stroke", {"type": 'LEFTMOUSE', "value": 'PRESS', "shift": True},
         {"properties": [("action", 'SELECT')]}),
        ("allset.uv_cut", {"type": 'X', "value": 'PRESS'}, {"properties": [("mesh_select", True)]}),
        ("allset.uv_sew", {"type": 'S', "value": 'PRESS'}, {"properties": [("mesh_select", True)]}),
        ("allset.uv_unfold_layout", {"type": 'D', "value": 'PRESS'}, None),
    )

    @staticmethod
    def draw_settings(context, layout, tool):
        layout.label(text=_zh("Drag: Cut  ·  Ctrl+drag: Sew  ·  Shift+drag: Select", 'MWK:ui/mesh_tools.py:101'), icon='INFO')
        row = layout.row(align=True)
        row.operator("allset.uv_cut", text=_zh("Cut (x)", 'MWK:ui/mesh_tools.py:103')).mesh_select = True
        row.operator("allset.uv_sew", text=_zh("Sew (s)", 'MWK:ui/mesh_tools.py:104')).mesh_select = True
        row.operator("allset.uv_unfold_layout", text=_zh("Unfold + Layout (d)", 'MWK:ui/mesh_tools.py:105'))


MULTI_CUT_SHORTCUTS = (
    ("Click edge / face / vertex", "place a cut point (drag: slide it along the edge)"),
    ("Shift", "snap the point to the Snap Step %"),
    ("Ctrl+click", "insert an edge loop (Ctrl+Shift: at the Snap Step)"),
    ("Ctrl+middle-click", "edge loop in the middle of the edge"),
    ("Backspace", "remove the last point"),
    ("Enter / right-click", "complete the cut (the tool stays)"),
    ("Esc", "drop the points; with none, leave the tool"),
    ("Drag across faces", "slice"),
)


def _hover_items():
    items = [("allset.multi_cut_hover", {"type": 'MOUSEMOVE', "value": 'ANY', "any": True}, None)]
    for key in ('LEFT_CTRL', 'RIGHT_CTRL', 'LEFT_SHIFT', 'RIGHT_SHIFT'):
        for value in ('PRESS', 'RELEASE'):
            items.append(("allset.multi_cut_hover", {"type": key, "value": value, "any": True}, None))
    return tuple(items)


class ALLSET_TL_multi_cut(bpy.types.WorkSpaceTool):
    """Maya Multi-Cut (docs/steps/step_129_multicut.md): points on edges / faces / vertices, Enter or RMB cuts,
    Ctrl = edge loop, Shift = Snap Step, Backspace, drag = slice. No select fallback: Maya's Multi-Cut LMB doesn't
    select."""
    bl_translation_context = 'MWK:ui/mesh_tools.py:135'
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'
    bl_idname = multi_cut.TOOL
    bl_label = _zh_native("Multi-Cut", 'MWK:ui/mesh_tools.py:135')
    bl_description = (_zh_native("Click edges, faces or vertices to place cut points, Enter or right-click to cut. "
                      "Ctrl+click = edge loop, Shift = Snap Step %, Backspace = remove the last point, "
                      "drag across faces = slice (Maya Multi-Cut)", 'MWK:ui/mesh_tools.py:135'))
    bl_icon = "ops.mesh.knife_tool"
    bl_widget = None
    bl_keymap = (
        # loops first: one undo step each and Adjust Last Operation Position (step 64's operator); they pass
        # through when no edge is under the mouse
        ("allset.multicut_loop", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True}, None),
        ("allset.multicut_loop", {"type": 'LEFTMOUSE', "value": 'PRESS', "ctrl": True, "shift": True},
         {"properties": [("snap", True)]}),
        ("allset.multicut_loop", {"type": 'MIDDLEMOUSE', "value": 'PRESS', "ctrl": True},
         {"properties": [("center", True)]}),
        ("allset.multi_cut", {"type": 'LEFTMOUSE', "value": 'PRESS', "any": True}, None),
        ("allset.multi_cut_exit", {"type": 'ESC', "value": 'PRESS'}, None),
        *_hover_items(),
    )

    @staticmethod
    def draw_settings(context, layout, tool):
        s = mesh_tools.settings(context)
        if context.region.type == 'TOOL_HEADER':
            layout.prop(s, "snap_step", slider=True)
            return
        draw_multi_cut(layout, s)


def draw_multi_cut(layout, s):
    """Maya's Multi-Cut Tool Settings, Maya's order and factory values."""
    layout.prop(s, "snap_step", slider=True)
    box = layout.box()
    box.label(text=_zh("Cut / Insert Edge Loop Tool", 'MWK:ui/mesh_tools.py:167'))
    box.prop(s, "smoothing_angle", slider=True)
    _grey(box, "Multi-Cut/Edge Flow", "Edge Flow")
    box.prop(s, "subdivisions", slider=True)
    box = layout.box()
    box.label(text=_zh("Slice Tool", 'MWK:ui/mesh_tools.py:172'))
    box.prop(s, "ignore_backfaces")
    box.prop(s, "delete_faces")
    box.prop(s, "extract_faces")
    row = box.row(align=True)
    row.enabled = s.extract_faces          # Maya greys the offset while Extract Faces is off
    row.prop(s, "extract_offset", text="")
    box.label(text=_zh("Slice Along Plane:", 'MWK:ui/mesh_tools.py:179'))
    box.row(align=True).prop(s, "slice_plane", expand=True)
    _grey(layout, "Multi-Cut/Color Settings", "Color Settings")
    _grey(layout, "Multi-Cut/Live Constraint Options", "Live Constraint Options")
    box = layout.box()
    box.label(text=_zh("Keyboard/Mouse Shortcuts", 'MWK:ui/mesh_tools.py:184'))
    col = box.column(align=True)
    for key, what in MULTI_CUT_SHORTCUTS:
        col.label(text=_zh(f"{key}: {what}", 'MWK:ui/mesh_tools.py:187'))


TOOLS = (ALLSET_TL_multi_cut, ALLSET_TL_target_weld, ALLSET_TL_crease, ALLSET_TL_cut_sew)


def active_tool_id(context):
    try:
        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    except (AttributeError, TypeError, RuntimeError):
        return ""
    return tool.idname if tool is not None else ""


def register():
    notices.PANEL_NOTICES.update(GREY)
    for tool in TOOLS:
        bpy.utils.register_tool(tool, after={"builtin.knife"})


def unregister():
    for tool in reversed(TOOLS):
        bpy.utils.unregister_tool(tool)
    for key in GREY:
        notices.PANEL_NOTICES.pop(key, None)

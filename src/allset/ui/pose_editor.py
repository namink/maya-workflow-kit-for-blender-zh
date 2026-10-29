# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's Pose Editor window (step 227 L16, Issue #137).

Maya: Windows > Animation Editors > Pose Editor / Deform > Pose Space Deformation > Pose Editor — pose interpolators on
the left, the current interpolator's poses on the right (Add Pose, Add Shape, Edit, Go to Pose, Delete, the pose
weights). The window's exact layout isn't known [U]: the kit layout (delegated) = toolbar row, then two columns
(interpolators | poses with their read-only weight), then the interpolation (Linear; Gaussian greyed with a notice).
Logic in ``operators/pose_space_227.py``; the window is ``marked_window`` kind POSE_EDITOR.
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy

from . import marked_window

KIND = "POSE_EDITOR"

# greyed rows (notices.PANEL_NOTICES while registered; drawn through allset.menu_unavailable)
NOTICES = {
    "Pose Editor/Interpolation/Gaussian": (
        "Linear", "The kit's pose weights are Maya's Linear interpolation (a shape key driver per pose); Blender "
        "drivers can't solve Maya's Gaussian RBF."),
}


def _ps():
    from ..operators import pose_space_227
    return pose_space_227


def redraw(context):
    marked_window.redraw(context, KIND)


def _grey(layout, key, text):
    row = layout.row()
    row.enabled = False
    row.operator("allset.menu_unavailable", text=_zh(text, 'MWK:ui/pose_editor.py:39'), emboss=False).item = key


def draw_toolbar(layout, context):
    ps = _ps()
    interp, pose = ps.current(context)
    row = layout.row(align=True)
    row.operator("allset.pose_interpolator_create", text=_zh("Create Pose Interpolator", 'MWK:ui/pose_editor.py:46'))
    sub = row.row(align=True)
    sub.enabled = interp is not None
    op = sub.operator("allset.pose_add", text=_zh("Add Pose", 'MWK:ui/pose_editor.py:49'))
    op.interpolator = interp.name if interp is not None else ""
    for idname, text in (("allset.pose_add_shape", "Add Shape"), ("allset.pose_go", "Go to Pose"),
                         ("allset.pose_delete", "Delete")):
        op = sub.operator(idname, text=_zh(text, 'MWK:ui/pose_editor.py:53'))
        op.interpolator = interp.name if interp is not None else ""
        op.pose = pose


def draw_lists(layout, context):
    ps = _ps()
    interp, pose = ps.current(context)
    split = layout.split(factor=0.4)
    left = split.column(align=True)
    left.label(text=_zh("Pose Interpolators", 'MWK:ui/pose_editor.py:63'))
    box = left.box().column(align=True)
    items = ps.interpolators()
    if not items:
        box.label(text=_zh("Select a joint, then Create Pose Interpolator", 'MWK:ui/pose_editor.py:67'))
    for ob in items:
        op = box.operator("allset.pose_pick", text=ob.name, depress=(ob == interp and not pose), emboss=True,
                          icon='DRIVER')
        op.interpolator, op.pose = ob.name, ""
    right = split.column(align=True)
    right.label(text=_zh("Poses" + (f" ({interp.name})" if interp is not None else ""), 'MWK:ui/pose_editor.py:73'))
    box = right.box().column(align=True)
    if interp is None:
        return
    arm, pb = ps.driver_of(interp)
    box.label(text=_zh(f"Driver: {pb.name if pb is not None else '(missing)'}", 'MWK:ui/pose_editor.py:78'), icon='BONE_DATA')
    head = box.row()
    head.label(text=_zh("Pose", 'MWK:ui/pose_editor.py:80'))
    head.label(text=_zh("Weight", 'MWK:ui/pose_editor.py:81'))
    head.label(text=_zh("Shape", 'MWK:ui/pose_editor.py:82'))
    for name in [ps.NEUTRAL, *ps.poses(interp)]:
        row = box.row(align=True)
        op = row.operator("allset.pose_pick", text=name, depress=(name == pose))
        op.interpolator, op.pose = interp.name, name
        row.label(text=_zh("" if name == ps.NEUTRAL else f"{ps.weight(interp, name):.3f}", 'MWK:ui/pose_editor.py:87'))
        if name == ps.NEUTRAL:
            row.label(text="")
            continue
        shapes = ps.shapes_of(interp, name)
        if shapes:
            op = row.operator("allset.pose_edit", text=_zh("Edit", 'MWK:ui/pose_editor.py:93'), depress=ps.editing(interp, name) is not None)
        else:
            op = row.operator("allset.pose_add_shape", text=_zh("Add Shape", 'MWK:ui/pose_editor.py:95'))
        op.interpolator, op.pose = interp.name, name


def draw_settings(layout, context):
    ps = _ps()
    interp, _pose = ps.current(context)
    if interp is None:
        return
    row = layout.row(align=True)
    row.label(text=_zh("Interpolation", 'MWK:ui/pose_editor.py:105'))
    row.operator("allset.pose_pick", text=_zh("Linear", 'MWK:ui/pose_editor.py:106'), depress=True).interpolator = interp.name
    _grey(row, "Pose Editor/Interpolation/Gaussian", "Gaussian")
    axis = ("X", "Y", "Z")[int(interp.get(ps.P_AXIS, 0))]
    layout.label(text=_zh(f"Driver twist axis: {axis}", 'MWK:ui/pose_editor.py:109'))


class ALLSET_PT_pose_editor(bpy.types.Panel):
    """Maya's Pose Editor (a marked Properties Tool tab in its own window)"""
    bl_translation_context = 'MWK:ui/pose_editor.py:117'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"            # = drawn by the Properties Tool tab (step 106 mechanism)
    bl_label = _zh_native("Pose Editor", 'MWK:ui/pose_editor.py:117')
    bl_options = {'HIDE_HEADER'}
    bl_order = -300

    @classmethod
    def poll(cls, context):
        return marked_window.context_kind(context) == KIND

    def draw(self, context):
        layout = self.layout
        draw_toolbar(layout, context)
        draw_lists(layout, context)
        draw_settings(layout, context)
        layout.operator("allset.marked_window_close", text=_zh("Close", 'MWK:ui/pose_editor.py:130'))


classes = (ALLSET_PT_pose_editor,)

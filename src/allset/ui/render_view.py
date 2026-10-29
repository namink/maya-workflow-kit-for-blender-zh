# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Render View = Blender's Image Editor showing Render Result (docs/steps/step_67.md 「계획」 3, 4).

Maya's Render View toolbar has Render, IPR,
Keep Image and Remove Image: kept images stay in a strip to compare with the next render. Blender's Render
Result has render slots (J / Alt+J switch between them), and a render goes into the active slot, so:

- Keep Image = record the shown slot as kept (``allset_kept`` on the Render Result image) and make the first
  slot that isn't kept active (a new slot when all are), so the next render doesn't replace the kept one;
- Remove Image = clear the shown slot and forget it.

The buttons are drawn at the start of the Image Editor header when it shows Render Result (``ui/shelf.py`` already
wraps ``IMAGE_HT_header.draw`` and calls ``draw_header`` first). ``ALLSET_MT_render_using`` = Render > Render Using
(the scene's render engine).
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy

from .. import results

KEPT_PROP = "allset_kept"
KEEP_TIP = "Maya Keep Image = Blender Render Slot (J / Alt+J to compare)"


def render_result():
    return next((i for i in bpy.data.images if i.type == 'RENDER_RESULT'), None)


def kept(image):
    return {int(i) for i in image.get(KEPT_PROP, [])}


def keep(image):
    """Keep the active slot; the slot the next render goes into (its index)."""
    slots = image.render_slots
    done = kept(image) | {slots.active_index}
    image[KEPT_PROP] = sorted(done)
    free = next((i for i in range(len(slots)) if i not in done), None)
    if free is None:
        slots.new()
        free = len(slots) - 1
    slots.active_index = free
    return free


def remove(image, image_user=None):
    """Clear the active slot (when the editor's image user is known) and forget that it was kept."""
    slots = image.render_slots
    index = slots.active_index
    if image_user is not None:
        slots[index].clear(image_user)
    done = kept(image) - {index}
    image[KEPT_PROP] = sorted(done)
    return index


class ALLSET_OT_render_keep_image(bpy.types.Operator):
    """Keep this image: the next render goes into a new render slot (Maya Render View Keep Image).
Blender: Render Slots, J / Alt+J to compare"""
    bl_translation_context = 'MWK:ui/render_view.py:63'
    bl_idname = "allset.render_keep_image"
    bl_label = _zh_native("Keep Image", 'MWK:ui/render_view.py:63')
    bl_description = _zh_native('Keep this image: the next render goes into a new render slot (Maya Render View Keep Image).\nBlender: Render Slots, J / Alt+J to compare', 'MWK:ui/render_view.py:63')

    @classmethod
    def poll(cls, context):
        return render_result() is not None

    def execute(self, context):
        image = render_result()
        index = keep(image)
        results.result(self, _zh(f"Kept; next render goes to {image.render_slots[index].name}", 'MWK:ui/render_view.py:72'))
        _redraw(context)
        return {'FINISHED'}


class ALLSET_OT_render_remove_image(bpy.types.Operator):
    """Remove the shown image (clear this render slot) (Maya Render View Remove Image)"""
    bl_translation_context = 'MWK:ui/render_view.py:80'
    bl_idname = "allset.render_remove_image"
    bl_label = _zh_native("Remove Image", 'MWK:ui/render_view.py:80')
    bl_description = _zh_native('Remove the shown image (clear this render slot) (Maya Render View Remove Image)', 'MWK:ui/render_view.py:80')

    @classmethod
    def poll(cls, context):
        return render_result() is not None

    def execute(self, context):
        space = context.space_data
        user = space.image_user if space is not None and space.type == 'IMAGE_EDITOR' else None
        remove(render_result(), user)
        _redraw(context)
        return {'FINISHED'}


def _redraw(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.tag_redraw()


class ALLSET_MT_render_using(bpy.types.Menu):
    """Render engine of the scene (Maya Render > Render Using)"""
    bl_translation_context = 'MWK:ui/render_view.py:104'
    bl_idname = "ALLSET_MT_render_using"
    bl_label = _zh_native("Render Using", 'MWK:ui/render_view.py:104')

    def draw(self, context):
        self.layout.props_enum(context.scene.render, "engine")


def draw_header(layout, context):
    """Maya Render View toolbar buttons for an Image Editor showing Render Result."""
    space = context.space_data
    image = getattr(space, "image", None)
    if image is None or image.type != 'RENDER_RESULT':
        return
    row = layout.row(align=True)
    row.operator("allset.render_current_frame", text=_zh("Render", 'MWK:ui/render_view.py:117'), icon='RENDER_STILL')   # step 137
    row.operator("allset.render_keep_image", text=_zh("Keep Image", 'MWK:ui/render_view.py:118'), icon='PINNED')
    row.operator("allset.render_remove_image", text=_zh("Remove Image", 'MWK:ui/render_view.py:119'), icon='X')
    slots = image.render_slots
    done = kept(image)
    row.label(text=_zh(f"{slots.active.name}{' (kept)' if slots.active_index in done else ''} · {len(done)} kept", 'MWK:ui/render_view.py:122'))
    layout.separator()


classes = (ALLSET_OT_render_keep_image, ALLSET_OT_render_remove_image, ALLSET_MT_render_using)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

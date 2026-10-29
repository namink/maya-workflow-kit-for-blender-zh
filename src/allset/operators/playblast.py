# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Playblast: viewport capture of the playback range, then the player (docs/steps/step_70.md 「계획」 5).

Maya's Windows > Playblast records the Time Slider range from the active view into a temporary movie and plays it
in a player (View on); its option box sets Time range, Format, Quality and Scale
Blender: ``render.opengl``
(animation) already records the playback (preview) range (measured in step 48), into the scene's render output;
``render.play_rendered_anim`` opens Blender's player on it. The kit points the output at a temporary folder with
the playblast's format and scale, plays it, and puts the scene's render settings back.
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import os

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty

from .. import results
from .. import compat

MAYA_QUALITY = 70          # Maya Playblast option defaults
MAYA_SCALE = 0.5


def output_dir():
    return os.path.join(bpy.app.tempdir or bpy.path.abspath("//"), "playblast")


def output_path(scene):
    return os.path.join(output_dir(), f"{bpy.path.clean_name(scene.name)}_")


def _crf(quality):
    return 'HIGH' if quality >= 85 else 'MEDIUM' if quality >= 55 else 'LOW'


SETTINGS = ("render.filepath", "render.resolution_percentage", "render.image_settings.file_format",
            "render.image_settings.quality", "render.ffmpeg.format", "render.ffmpeg.codec",
            "render.ffmpeg.constant_rate_factor", "use_preview_range", "frame_preview_start", "frame_preview_end",
            *(("render.image_settings.media_type",) if compat.MEDIA_TYPE else ()))


def _get(scene, path):
    owner = scene
    *head, attr = path.split(".")
    for part in head:
        owner = getattr(owner, part)
    return owner, attr


def save_settings(scene):
    return {path: getattr(*_get(scene, path)) for path in SETTINGS}


def restore_settings(scene, saved):
    # media type (5.x), then file format: the ffmpeg values only stick while the format is FFMPEG
    first = ("render.image_settings.media_type", "render.image_settings.file_format")
    order = sorted(saved, key=lambda p: first.index(p) if p in first else len(first))
    for path in order:
        owner, attr = _get(scene, path)
        try:
            setattr(owner, attr, saved[path])
        except (TypeError, ValueError):
            pass


def apply_settings(scene, fmt, quality, scale, frames=None):
    """Point the scene's render output at the playblast: temp folder, format, scale, optional frame range."""
    r = scene.render
    r.filepath = output_path(scene)
    r.resolution_percentage = max(1, min(100, round(scale * 100)))
    if fmt == 'MOVIE':
        compat.set_file_format(r.image_settings, 'FFMPEG')
        r.ffmpeg.format = 'MPEG4'
        r.ffmpeg.codec = 'H264'
        r.ffmpeg.constant_rate_factor = _crf(quality)
    else:
        compat.set_file_format(r.image_settings, 'JPEG')
        r.image_settings.quality = quality
    if frames is not None:
        scene.use_preview_range = True
        scene.frame_preview_start, scene.frame_preview_end = frames


def playback_range(scene):
    if scene.use_preview_range:
        return scene.frame_preview_start, scene.frame_preview_end
    return scene.frame_start, scene.frame_end


def _view3d(context):
    if context.area is not None and context.area.type == 'VIEW_3D':
        region = context.region if context.region and context.region.type == 'WINDOW' else None
        return context.area, region or next(r for r in context.area.regions if r.type == 'WINDOW')
    from ..ui.status_line import main_view3d
    return main_view3d(context.screen)


class ALLSET_OT_playblast(bpy.types.Operator):
    """Record the playback range from the viewport and play it (Maya Playblast)"""
    bl_translation_context = 'MWK:operators/playblast.py:103'
    bl_idname = "allset.playblast"
    bl_label = _zh_native("Playblast", 'MWK:operators/playblast.py:103')
    bl_description = _zh_native('Record the playback range from the viewport and play it (Maya Playblast)', 'MWK:operators/playblast.py:103')

    time_range: EnumProperty(name=_zh_native("Time Range", 'MWK:operators/playblast.py:105'), items=_zh_enum((('TIME_SLIDER', "Time Slider", "The playback range"),
                                                       ('START_END', "Start/End", "")), 'MWK:operators/playblast.py:105'), default='TIME_SLIDER', translation_context='MWK:operators/playblast.py:105')
    start: IntProperty(name=_zh_native("Start Time", 'MWK:operators/playblast.py:107'), default=1, translation_context='MWK:operators/playblast.py:107')
    end: IntProperty(name=_zh_native("End Time", 'MWK:operators/playblast.py:108'), default=120, translation_context='MWK:operators/playblast.py:108')
    format: EnumProperty(name=_zh_native("Format", 'MWK:operators/playblast.py:109'), items=_zh_enum((('MOVIE', "Movie (MPEG-4)", "Maya avi / qt"),
                                               ('IMAGE', "Image (JPEG sequence)", "")), 'MWK:operators/playblast.py:109'), default='MOVIE', translation_context='MWK:operators/playblast.py:109')
    quality: IntProperty(name=_zh_native("Quality", 'MWK:operators/playblast.py:111'), default=MAYA_QUALITY, min=1, max=100, subtype='PERCENTAGE', translation_context='MWK:operators/playblast.py:111')
    scale: FloatProperty(name=_zh_native("Scale", 'MWK:operators/playblast.py:112'), default=MAYA_SCALE, min=0.1, max=1.0, translation_context='MWK:operators/playblast.py:112')
    view: BoolProperty(name=_zh_native("View", 'MWK:operators/playblast.py:113'), default=True, description=_zh_native("Play the playblast when it is done", 'MWK:operators/playblast.py:113'), translation_context='MWK:operators/playblast.py:113')
    option_box: BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, translation_context='MWK:operators/playblast.py:114')

    def invoke(self, context, event):
        if self.option_box:
            a, b = playback_range(context.scene)
            self.start, self.end = a, b
            return context.window_manager.invoke_props_dialog(self, width=360, title=_zh("Playblast Options", 'MWK:operators/playblast.py:120'),
                                                              confirm_text=_zh("Playblast", 'MWK:operators/playblast.py:121'))
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "time_range", expand=True)
        col = layout.column(align=True)
        col.active = self.time_range == 'START_END'
        col.prop(self, "start")
        col.prop(self, "end")
        layout.prop(self, "view")
        layout.prop(self, "format")
        layout.prop(self, "quality", slider=True)
        layout.prop(self, "scale", slider=True)

    def execute(self, context):
        scene = context.scene
        area, region = _view3d(context)
        if area is None:
            self.report({'ERROR'}, _zh("Playblast needs a 3D View", 'MWK:operators/playblast.py:141'))
            return {'CANCELLED'}
        saved = save_settings(scene)
        frames = (self.start, self.end) if self.time_range == 'START_END' else None
        os.makedirs(output_dir(), exist_ok=True)
        try:
            apply_settings(scene, self.format, self.quality, self.scale, frames)
            with context.temp_override(area=area, region=region):
                bpy.ops.render.opengl(animation=True)
                if self.view:
                    bpy.ops.render.play_rendered_anim()
            a, b = playback_range(scene)
        finally:
            restore_settings(scene, saved)
        results.result(self, _zh(f"Playblast frames {a}-{b} in {output_dir()}", 'MWK:operators/playblast.py:155'))
        return {'FINISHED'}


classes = (ALLSET_OT_playblast,)

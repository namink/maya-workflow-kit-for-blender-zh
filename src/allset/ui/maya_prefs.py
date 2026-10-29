# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's Preferences window (Windows > Settings/Preferences > Preferences; step 215, Issue #121).

Maya 2022: an 817 x 531 window — menu bar Edit (Revert to Saved, Restore Default
Settings) / Help, a "Categories" list on the left (38 rows, children indented), the page "<Category>: <description>"
on the right in sections, Save / Cancel at the bottom; closing the window by its OS button saves.

The kit's window is a ``marked_window`` kind (a Properties Tool tab in its own window) drawing the pages of
``maya_prefs_data.PAGES``: kit add-on preferences and the values the kit keeps in the scene, grouped by Maya's
categories. Blender preferences are never written by the kit (docs/user_decisions.md decisions 13 / 14): those rows
show Blender's value read-only with the Recommended setup note and a button that opens that Preferences section.

Save / Cancel (delegated): the window takes a snapshot of every row's value when it opens; Save keeps the changes and
closes (the add-on preferences are kept by Blender's Auto-Save Preferences or File > Save Preferences, like every
add-on), Cancel and Edit > Revert to Saved write the snapshot back; Edit > Restore Default Settings = the add-on
preferences' defaults and Maya's factory scene values (``maya_prefs_data.MAYA_FACTORY``). Closing by the OS button keeps
the changes (Maya saves).
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy
from bpy.props import CollectionProperty, EnumProperty, IntProperty, StringProperty

from . import marked_window
from . import maya_prefs_data as data

KIND = "PREFERENCES"
_snapshot = {}        # (kind, path) -> value at window open


def _prefs(context):
    from .. import preferences
    try:
        return preferences.get(context)
    except KeyError:
        return None


def resolve(owner, path):
    """(object, attribute) for a dotted path under ``owner``, or (None, None)."""
    parts = path.split(".")
    for name in parts[:-1]:
        owner = getattr(owner, name, None)
        if owner is None:
            return None, None
    return (owner, parts[-1]) if hasattr(owner, parts[-1]) else (None, None)


def _target(context, row):
    if row[0] == "pref":
        prefs = _prefs(context)
        return (prefs, row[1]) if prefs is not None and hasattr(prefs, row[1]) else (None, None)
    if row[0] == "scene":
        return resolve(context.scene, row[1])
    if row[0] == "blender":
        return resolve(context.preferences, row[3])
    return None, None


def editable_rows():
    """The rows the window can change (kit preferences and scene values), without duplicates."""
    seen, out = set(), []
    for _key, _section, row in data.rows():
        if row[0] in {"pref", "scene"} and (row[0], row[1]) not in seen:
            seen.add((row[0], row[1]))
            out.append(row)
    return out


def take_snapshot(context):
    _snapshot.clear()
    for row in editable_rows():
        owner, attr = _target(context, row)
        if owner is not None:
            _snapshot[(row[0], row[1])] = getattr(owner, attr)


def _write(owner, attr, value):
    try:
        if getattr(owner, attr) != value:
            setattr(owner, attr, value)
    except (AttributeError, TypeError, ValueError):
        pass


def revert(context):
    """Write the values of the window's opening back (Cancel / Revert to Saved); number of rows written."""
    n = 0
    for row in editable_rows():
        key = (row[0], row[1])
        owner, attr = _target(context, row)
        if owner is not None and key in _snapshot and getattr(owner, attr) != _snapshot[key]:
            _write(owner, attr, _snapshot[key])
            n += 1
    return n


def restore_defaults(context):
    """Kit preferences back to their defaults, scene rows to Maya's factory values (Restore Default Settings)."""
    for row in editable_rows():
        owner, attr = _target(context, row)
        if owner is None:
            continue
        if row[0] == "pref":
            owner.property_unset(attr)
        elif row[1] in data.MAYA_FACTORY:
            _write(owner, attr, data.MAYA_FACTORY[row[1]])
    scene = context.scene
    if scene is not None:
        # the playback (preview) range is kept inside the animation range: write it after the animation range
        for path in ("frame_preview_start", "frame_preview_end"):
            _write(scene, path, data.MAYA_FACTORY[path])
        scene.use_preview_range = True      # Maya: playback range 1-120 inside the animation range 1-200


# --- window ------------------------------------------------------------------------------------------------------

# Static list: Blender keeps only references to enum item strings (a callback's fresh strings can be freed)
CATEGORY_ITEMS = [(key, ("    " * depth) + label, title, i) for i, (key, label, depth, title, _s) in enumerate(data.PAGES)]


def _wm(context):
    return context.window_manager


# The Categories list: a scrolling UIList (38 Maya rows don't fit the window, Maya's list scrolls too) over a
# WindowManager collection filled when the window opens (never in draw / register).
class ALLSET_PG_prefs_category(bpy.types.PropertyGroup):
    key: StringProperty(translation_context='MWK:ui/maya_prefs.py:130')
    depth: IntProperty(translation_context='MWK:ui/maya_prefs.py:131')


def fill_categories(context):
    wm = _wm(context)
    if len(wm.allset_prefs_cats) == len(data.PAGES):
        return
    wm.allset_prefs_cats.clear()
    for key, label, depth, _title, _s in data.PAGES:
        item = wm.allset_prefs_cats.add()
        item.name, item.key, item.depth = label, key, depth
    wm.allset_prefs_cat_index = data.KEYS.index(wm.allset_prefs_category)


def _cat_index_update(self, _context):
    if 0 <= self.allset_prefs_cat_index < len(data.KEYS):
        key = data.KEYS[self.allset_prefs_cat_index]
        if self.allset_prefs_category != key:
            self.allset_prefs_category = key


def _category_update(self, _context):
    i = data.KEYS.index(self.allset_prefs_category)
    if self.allset_prefs_cat_index != i and len(self.allset_prefs_cats) == len(data.KEYS):
        self.allset_prefs_cat_index = i


class ALLSET_UL_prefs_categories(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_propname, index=0):
        layout.label(text=_zh(("    " * item.depth) + item.name, 'MWK:ui/maya_prefs.py:160'))


def _draw_row(layout, context, row):
    kind = row[0]
    if kind in {"pref", "scene"}:
        owner, attr = _target(context, row)
        if owner is None:
            return
        layout.prop(owner, attr, text=_zh(row[2], 'MWK:ui/maya_prefs.py:169'))
    elif kind == "blender":
        _k, label, section, path, note = row
        owner, attr = resolve(context.preferences, path)
        line = layout.row(align=True)
        value = getattr(owner, attr) if owner is not None else "?"
        if isinstance(value, bool):
            value = "On" if value else "Off"
        text = line.row()
        text.enabled = False
        text.label(text=_zh(f"{label}: {value}  (Blender)", 'MWK:ui/maya_prefs.py:179'))
        line.operator("allset.prefs_open_blender", text=_zh("Blender Preferences", 'MWK:ui/maya_prefs.py:180'), icon='PREFERENCES').section = section
        note_row = layout.row()
        note_row.enabled = False
        note_row.label(text=_zh(note, 'MWK:ui/maya_prefs.py:183'), icon='INFO')
    elif kind == "missing":
        _k, label, note = row
        sub = layout.row()
        sub.enabled = False
        sub.label(text=_zh(f"{label}: {note}", 'MWK:ui/maya_prefs.py:188'))


def draw_page(layout, context, key):
    _key, _label, _depth, title, sections = data.BY_KEY[key]
    layout.label(text=_zh(title, 'MWK:ui/maya_prefs.py:193'))
    for section, items in sections:
        box = layout.box()
        box.label(text=_zh(section, 'MWK:ui/maya_prefs.py:196'))
        col = box.column()
        for row in items:
            _draw_row(col, context, row)


class ALLSET_MT_prefs_edit(bpy.types.Menu):
    bl_translation_context = 'MWK:ui/maya_prefs.py:203'
    bl_label = _zh_native("Edit", 'MWK:ui/maya_prefs.py:203')

    def draw(self, _context):
        self.layout.operator("allset.prefs_revert", text=_zh("Revert to Saved", 'MWK:ui/maya_prefs.py:206'))
        self.layout.operator("allset.prefs_restore_defaults", text=_zh("Restore Default Settings", 'MWK:ui/maya_prefs.py:207'))


class ALLSET_MT_prefs_help(bpy.types.Menu):
    bl_translation_context = 'MWK:ui/maya_prefs.py:211'
    bl_label = _zh_native("Help", 'MWK:ui/maya_prefs.py:211')

    def draw(self, _context):
        from .editor_menu_map import _MANUAL
        self.layout.operator("wm.url_open", text=_zh("Help on Preferences...", 'MWK:ui/maya_prefs.py:215')).url = _MANUAL + "editors/preferences/index.html"


class ALLSET_PT_maya_prefs(bpy.types.Panel):
    """Maya's Preferences window (a marked Properties Tool tab in its own window)"""
    bl_translation_context = 'MWK:ui/maya_prefs.py:223'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = _zh_native("Preferences", 'MWK:ui/maya_prefs.py:223')
    bl_options = {'HIDE_HEADER'}
    bl_order = -300

    @classmethod
    def poll(cls, context):
        return marked_window.context_kind(context) == KIND

    def draw(self, context):
        layout = self.layout
        bar = layout.row(align=True)
        bar.alignment = 'LEFT'
        bar.emboss = 'PULLDOWN_MENU'
        bar.menu("ALLSET_MT_prefs_edit")
        bar.menu("ALLSET_MT_prefs_help")
        split = layout.split(factor=0.24)
        left = split.box()
        left.label(text=_zh("Categories", 'MWK:ui/maya_prefs.py:240'))
        wm = _wm(context)
        if len(wm.allset_prefs_cats) == len(data.PAGES):
            left.template_list("ALLSET_UL_prefs_categories", "", wm, "allset_prefs_cats", wm,
                               "allset_prefs_cat_index", rows=16)
        else:
            left.prop(wm, "allset_prefs_category", text="")
        draw_page(split.box().column(), context, _wm(context).allset_prefs_category)
        bottom = layout.row(align=True)
        bottom.operator("allset.prefs_save", text=_zh("Save", 'MWK:ui/maya_prefs.py:249'))
        bottom.operator("allset.prefs_cancel", text=_zh("Cancel", 'MWK:ui/maya_prefs.py:250'))


class ALLSET_OT_maya_preferences(bpy.types.Operator):
    """Open Maya's Preferences window: the kit's settings in Maya's categories
    (Windows > Settings/Preferences > Preferences)"""
    bl_translation_context = 'MWK:ui/maya_prefs.py:257'
    bl_idname = "allset.maya_preferences"
    bl_label = _zh_native("Preferences", 'MWK:ui/maya_prefs.py:257')
    bl_description = _zh_native("Open Maya's Preferences window: the kit's settings in Maya's categories\n(Windows > Settings/Preferences > Preferences)", 'MWK:ui/maya_prefs.py:257')

    category: EnumProperty(name=_zh_native("Category", 'MWK:ui/maya_prefs.py:259'), items=_zh_enum(CATEGORY_ITEMS, 'MWK:ui/maya_prefs.py:259'), options={'SKIP_SAVE'}, translation_context='MWK:ui/maya_prefs.py:259')

    def execute(self, context):
        if self.properties.is_property_set("category"):
            _wm(context).allset_prefs_category = self.category
        fill_categories(context)
        if marked_window.find_window(context, KIND) is None:
            take_snapshot(context)
        if marked_window.open_window(context, KIND) is None:
            self.report({'WARNING'}, _zh("Couldn't open the Preferences window", 'MWK:ui/maya_prefs.py:268'))
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_prefs_save(bpy.types.Operator):
    """Keep the changes and close the window (Maya's Save; Blender's Auto-Save Preferences or File > Save
    Preferences keeps the kit's settings)"""
    bl_translation_context = 'MWK:ui/maya_prefs.py:277'
    bl_idname = "allset.prefs_save"
    bl_label = _zh_native("Save", 'MWK:ui/maya_prefs.py:277')
    bl_description = _zh_native("Keep the changes and close the window (Maya's Save; Blender's Auto-Save Preferences or File > Save\nPreferences keeps the kit's settings)", 'MWK:ui/maya_prefs.py:277')
    bl_options = {'INTERNAL'}

    def execute(self, context):
        _snapshot.clear()
        if context.window is not None and context.window != context.window_manager.windows[0]:
            marked_window.close_later(context.window)
        return {'FINISHED'}


class ALLSET_OT_prefs_cancel(bpy.types.Operator):
    """Put back the values the window opened with and close it (Maya's Cancel)"""
    bl_translation_context = 'MWK:ui/maya_prefs.py:290'
    bl_idname = "allset.prefs_cancel"
    bl_label = _zh_native("Cancel", 'MWK:ui/maya_prefs.py:290')
    bl_description = _zh_native("Put back the values the window opened with and close it (Maya's Cancel)", 'MWK:ui/maya_prefs.py:290')
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        revert(context)
        _snapshot.clear()
        if context.window is not None and context.window != context.window_manager.windows[0]:
            marked_window.close_later(context.window)
        return {'FINISHED'}


class ALLSET_OT_prefs_revert(bpy.types.Operator):
    """Put back the values the window opened with (Maya's Edit > Revert to Saved)"""
    bl_translation_context = 'MWK:ui/maya_prefs.py:304'
    bl_idname = "allset.prefs_revert"
    bl_label = _zh_native("Revert to Saved", 'MWK:ui/maya_prefs.py:304')
    bl_description = _zh_native("Put back the values the window opened with (Maya's Edit > Revert to Saved)", 'MWK:ui/maya_prefs.py:304')
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        revert(context)
        marked_window.redraw(context, KIND)
        return {'FINISHED'}


class ALLSET_OT_prefs_restore_defaults(bpy.types.Operator):
    """Kit settings back to their defaults and the scene values to Maya's factory settings (Maya's Edit > Restore
    Default Settings)"""
    bl_translation_context = 'MWK:ui/maya_prefs.py:317'
    bl_idname = "allset.prefs_restore_defaults"
    bl_label = _zh_native("Restore Default Settings", 'MWK:ui/maya_prefs.py:317')
    bl_description = _zh_native("Kit settings back to their defaults and the scene values to Maya's factory settings (Maya's Edit > Restore\nDefault Settings)", 'MWK:ui/maya_prefs.py:317')
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        restore_defaults(context)
        marked_window.redraw(context, KIND)
        return {'FINISHED'}


SECTIONS = ('INTERFACE', 'VIEWPORT', 'NAVIGATION', 'SYSTEM', 'SAVE_LOAD', 'FILE_PATHS', 'KEYMAP', 'EDITING')


class ALLSET_OT_prefs_open_blender(bpy.types.Operator):
    """Open Blender's Preferences on this section: the kit doesn't change Blender's preferences,
    choose the value there (Recommended setup)"""
    bl_translation_context = 'MWK:ui/maya_prefs.py:333'
    bl_idname = "allset.prefs_open_blender"
    bl_label = _zh_native("Blender Preferences", 'MWK:ui/maya_prefs.py:333')
    bl_description = _zh_native("Open Blender's Preferences on this section: the kit doesn't change Blender's preferences,\nchoose the value there (Recommended setup)", 'MWK:ui/maya_prefs.py:333')
    bl_options = {'INTERNAL'}

    section: EnumProperty(items=_zh_enum([(s, s.title(), "") for s in SECTIONS], 'MWK:ui/maya_prefs.py:336'), translation_context='MWK:ui/maya_prefs.py:336')

    def execute(self, _context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT', section=self.section)
        return {'FINISHED'}


classes = (ALLSET_PG_prefs_category, ALLSET_UL_prefs_categories, ALLSET_MT_prefs_edit, ALLSET_MT_prefs_help, ALLSET_PT_maya_prefs, ALLSET_OT_maya_preferences,
           ALLSET_OT_prefs_save, ALLSET_OT_prefs_cancel, ALLSET_OT_prefs_revert, ALLSET_OT_prefs_restore_defaults,
           ALLSET_OT_prefs_open_blender)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.types.WindowManager
    wm.allset_prefs_category = EnumProperty(name=_zh_native("Category", 'MWK:ui/maya_prefs.py:352'), items=_zh_enum(CATEGORY_ITEMS, 'MWK:ui/maya_prefs.py:352'), update=_category_update, translation_context='MWK:ui/maya_prefs.py:352')
    wm.allset_prefs_cats = CollectionProperty(type=ALLSET_PG_prefs_category, translation_context='MWK:ui/maya_prefs.py:353')
    wm.allset_prefs_cat_index = IntProperty(name=_zh_native("Category", 'MWK:ui/maya_prefs.py:354'), default=0, update=_cat_index_update, translation_context='MWK:ui/maya_prefs.py:354')


def unregister():
    for name in ("allset_prefs_category", "allset_prefs_cats", "allset_prefs_cat_index"):
        if hasattr(bpy.types.WindowManager, name):
            delattr(bpy.types.WindowManager, name)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    _snapshot.clear()

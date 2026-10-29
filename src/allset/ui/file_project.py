# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya file dialog's left column in every Blender file browser: Current Project + the project's folders + Set
Project (Maya's file dialog: under Folder Bookmarks, "Current Project:"
drop-down, the project folder list, "Set Project..." button). Blender's own bookmarks stay above it.
docs/steps/step_102.md 「계획」 1."""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import os

import bpy

from ..operators import project


class ALLSET_PT_file_project(bpy.types.Panel):
    bl_translation_context = 'MWK:ui/file_project.py:20'
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_category = "Bookmarks"
    bl_label = _zh_native("Current Project", 'MWK:ui/file_project.py:20')

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and space.type == 'FILE_BROWSER' and space.browse_mode == 'FILES'

    def draw(self, context):
        layout = self.layout
        root = project.current_root(context)
        layout.menu("ALLSET_MT_recent_projects", text=_zh(os.path.basename(root) or root, 'MWK:ui/file_project.py:30'), icon='DOWNARROW_HLT')
        col = layout.column(align=True)
        rows = [("Workspace Root", root)] + [(name, os.path.join(root, name)) for name in project.FOLDERS
                                              if os.path.isdir(os.path.join(root, name))]
        for text, path in rows:
            row = col.row(align=True)
            row.alignment = 'LEFT'
            row.operator("allset.file_goto", text=_zh(text, 'MWK:ui/file_project.py:37'), icon='FILE_FOLDER', emboss=False).path = path
        layout.operator("allset.file_set_project", text=_zh("Set Project...", 'MWK:ui/file_project.py:38'))


classes = (ALLSET_PT_file_project,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 171 Maya windows of the Visualize menu: Create Animation Snapshot ❒ and the Ghosting Editor.

Same spec as operators/option_windows.py (``F`` fields, ``Window`` = one ``allset.opt_<key>`` operator;
option_windows._extend appends ``WINDOWS``). Titles, labels, buttons and factory values are Maya 2022's
with factory prefs (Snapshot options, Ghosting Editor; labels as Maya shows them).

The Ghosting Editor is a panel in Maya, not an option box: here it is a window whose command button is Maya's
"Create Ghost from Selection" and whose Apply puts the display values on every current ghost (Maya's editor applies
each change to all ghosts). Visualize > Ghost Selected uses its saved values (ui/ghosting.editor_values).
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy
from bpy.props import FloatVectorProperty

from .option_windows import F, Window
from .option_windows_modify import FString

RANGES = ("Start/End", "Time Slider")
UPDATES = ("On demand", "Fast (update only when keyframes change)", "Slow (always update)")
UPDATE_STYLES = ("demand", "animCurve", "force")


class FMayaColor(F):
    """A Maya colour swatch: Maya's own numbers (rendering space), not converted."""

    def __init__(self, name, label, default):
        super().__init__(name, label, "vec3color", default)

    def prop(self):
        return FloatVectorProperty(name=_zh_native(self.label.rstrip(":"), 'MWK:operators/option_windows_visualize.py:33'), default=self.default, size=3, subtype='COLOR',
                                   min=0.0, max=1.0, translation_context='MWK:operators/option_windows_visualize.py:33')


def _run_snapshot(context, v):
    return bpy.ops.allset.animation_snapshot('EXEC_DEFAULT', time_slider=v["time_range"] == RANGES[1],
                                             start=v["start"], end=v["end"], increment=v["increment"],
                                             update=UPDATE_STYLES[UPDATES.index(v["update"])])


def _run_ghost_editor(context, v):
    """Create Ghost from Selection with the window's values."""
    from ..ui import ghosting
    obs = ghosting.ghost(list(context.selected_objects), {**ghosting.FACTORY, **v})
    ghosting._changed()
    return {'FINISHED'} if obs else {'CANCELLED'}


def _apply_ghost_editor(context, v):
    """Apply (= Maya's live editor): every current ghost takes the display values; nothing is ghosted."""
    from ..ui import ghosting
    ghosting.apply_to_all(context.scene, {**ghosting.FACTORY, **v})
    ghosting._changed()
    return {'FINISHED'}


WINDOWS = [
    Window("animation_snapshot", "Animation Snapshot Options", "Snapshot", ("allset.animation_snapshot", {}), [
        F("time_range", "Time range:", "enum", RANGES[0], items=RANGES, translation_context='MWK:operators/option_windows_visualize.py:61'),
        F("start", "Start time:", "float", 1.0, translation_context='MWK:operators/option_windows_visualize.py:62'),
        F("end", "End time:", "float", 10.0, translation_context='MWK:operators/option_windows_visualize.py:63'),
        F("increment", "Increment:", "float", 1.0, lo=0.0001, translation_context='MWK:operators/option_windows_visualize.py:64'),
        F("update", "Update:", "enum", UPDATES[1], items=UPDATES, translation_context='MWK:operators/option_windows_visualize.py:65')], _run_snapshot,
        paths=("Visualize/Create Animation Snapshot",), translation_context='MWK:operators/option_windows_visualize.py:60'),
    Window("ghosting_editor", "Ghosting Editor", "Create Ghost from Selection", None, [
        F("hierarchy", "", "bool", True, text=_zh_native("Include Hierarchy", 'MWK:operators/option_windows_visualize.py:68'), translation_context='MWK:operators/option_windows_visualize.py:68'),
        F("mode", "Ghosting Mode:", "enum", "Pre And Post Frames",
          items=("Pre And Post Frames", "Pre Frames", "Post Frames", "Custom Frames", "Pre And Post Keyframes",
                 "All Keyframes"), translation_context='MWK:operators/option_windows_visualize.py:69'),
        F("preset", "Presets:", "enum", "1s", items=("1s", "2s", "4s", "5s", "10s", "Custom"), translation_context='MWK:operators/option_windows_visualize.py:72'),
        F("custom_pre", "Pre Frames (Custom):", "int", 3, lo=0, hi=20, translation_context='MWK:operators/option_windows_visualize.py:73'),
        F("custom_post", "Post Frames (Custom):", "int", 3, lo=0, hi=20, translation_context='MWK:operators/option_windows_visualize.py:74'),
        F("custom_step", "Step (Custom):", "int", 1, lo=1, hi=20, translation_context='MWK:operators/option_windows_visualize.py:75'),
        FString("custom_frames", "Custom Frames:"),
        FMayaColor("color_pre", "Pre Frame Color:", (0.447, 1.0, 1.0)),
        FMayaColor("color_post", "Post Frame Color:", (0.878, 0.678, 0.663)),
        F("near_opacity", "Near Opacity:", "float", 0.5, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_visualize.py:79'),
        F("far_opacity", "Far Opacity:", "float", 0.15, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_visualize.py:80')], _run_ghost_editor,
        missing=("Object type filters (Geometry / Joint / Locator)", "Ghosted Objects list, Show/Hide Ghosts",
                 "Ghost Driver"),
        apply_text="Apply to All Ghosts", click_saved=False, translation_context='MWK:operators/option_windows_visualize.py:67'),
]
WINDOWS[-1].apply_run = _apply_ghost_editor   # option_windows._apply_update: Apply acts on the ghosts

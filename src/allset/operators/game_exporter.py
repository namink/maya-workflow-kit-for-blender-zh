# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya File > Game Exporter (step 225, Issue #135; ATTACH_PLAN L24): the Model / Animation export window with
Maya's Animation Clips list, written with the kit's Maya FBX preset (operators/file_io.py, step 222 rig post-process).

Maya 2026 (the Game Exporter window):

- settings live on a ``gameFbxExporter`` node; factory values (createNode, ``FACTORY``): Export All, Model tab,
  one file, Bake Animation on, Skinning / Blend Shapes on, Smoothing Groups / Tangents and Binormals on, Triangulate /
  Move to Origin / Embed Media / Include Children / Input Connections off, Up Axis Y, Cameras / Lights on;
- a new clip starts with the playback range, an empty name, export on; a typed name
  that exists gets the next number (walk -> walk1, run09 -> run10);
- clips export as FBX takes (``FBXExportSplitAnimationIntoTakes`` name start end): **one file** = the file name
  (``.fbx`` added) with a take per exported clip; **a file per clip** = file name used as a prefix + clip name +
  ``.fbx``. Maya's files also carry the FBX plug-in's own ``Take 001`` and its
  per-clip loop never clears the take list, so a later clip file repeats the earlier clips' takes — the
  kit writes only the clip's own takes (delegated: engines would import those extra clips).

Blender (step 231, Issue #140): each clip is the scene's timeline take written by the kit's Maya FBX preset (the
step 222 rig rewrite included, so a clip file has Export Selection's joints), one write per clip with the scene's
range set to the clip; several clips of one file are merged into it as takes (``merge_takes``). Blender's NLA-strip
takes are not used: they evaluate one object at a time (``_ClipTimeline``).
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import os
import re

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, \
    StringProperty

from .. import results

FACTORY = {"export_type": 'MODEL', "export_set": 'ALL', "model_file_mode": 'SINGLE', "file_split": 'SINGLE',
           "bake_animation": True, "skinning": True, "blendshapes": True, "smoothing_groups": True,
           "tangents": True, "triangulate": False, "move_to_origin": False, "embed_media": False,
           "include_children": False, "input_connections": False, "up_axis": 'Y', "include_cameras": True,
           "include_lights": True}
# What a user sees: the window applies its default presets the first time it opens
# — Model tab "Model Default", Animation Clips tab "Anim Default" (step 266 independent
# check, both presets applied to a fresh node). The kit keeps the per-tab values.
PRESET_MODEL = {"embed_media": True, "include_children": True, "input_connections": True}
PRESET_ANIM = {"file_split": 'PER_CLIP', "embed_media": True, "include_cameras": False, "include_children": False,
               "input_connections": False}
TAB_PROPS = ("embed_media", "include_children", "input_connections", "include_cameras")


class ALLSET_PG_game_clip(bpy.types.PropertyGroup):
    name: StringProperty(name=_zh_native("Clip Name", 'MWK:operators/game_exporter.py:50'), translation_context='MWK:operators/game_exporter.py:50')
    start: FloatProperty(name=_zh_native("Start", 'MWK:operators/game_exporter.py:51'), default=1.0, translation_context='MWK:operators/game_exporter.py:51')
    end: FloatProperty(name=_zh_native("End", 'MWK:operators/game_exporter.py:52'), default=24.0, translation_context='MWK:operators/game_exporter.py:52')
    export: BoolProperty(name=_zh_native("Export", 'MWK:operators/game_exporter.py:53'), default=True, translation_context='MWK:operators/game_exporter.py:53')


class ALLSET_PG_game_exporter(bpy.types.PropertyGroup):
    export_type: EnumProperty(name=_zh_native("Export", 'MWK:operators/game_exporter.py:57'), items=_zh_enum([('MODEL', "Model", "Export the models (no animation)"),
                                                  ('ANIMATION', "Animation Clips", "Export the animation clips")], 'MWK:operators/game_exporter.py:57'),
                              default='MODEL', translation_context='MWK:operators/game_exporter.py:57')
    export_set: EnumProperty(name=_zh_native("Export", 'MWK:operators/game_exporter.py:60'), items=_zh_enum([('ALL', "Export All", ""), ('SELECTION', "Export Selection", "")], 'MWK:operators/game_exporter.py:60'),
                             default='ALL', translation_context='MWK:operators/game_exporter.py:60')
    model_file_mode: EnumProperty(name=_zh_native("File Type", 'MWK:operators/game_exporter.py:62'), items=_zh_enum([('SINGLE', "Single File", ""),
                                                          ('PER_ROOT', "Multiple Files", "A file per root object")], 'MWK:operators/game_exporter.py:62'),
                                  default='SINGLE', translation_context='MWK:operators/game_exporter.py:62')
    file_split: EnumProperty(name=_zh_native("File Type", 'MWK:operators/game_exporter.py:65'), items=_zh_enum([('SINGLE', "Multiple Clips to Single File", ""),
                                                     ('PER_CLIP', "Clips to Multiple Files", "")], 'MWK:operators/game_exporter.py:65'), default='PER_CLIP', translation_context='MWK:operators/game_exporter.py:65')
    clips: CollectionProperty(type=ALLSET_PG_game_clip, translation_context='MWK:operators/game_exporter.py:67')
    clip_index: IntProperty(default=0, translation_context='MWK:operators/game_exporter.py:68')
    bake_animation: BoolProperty(name=_zh_native("Bake Animation", 'MWK:operators/game_exporter.py:69'), default=True, translation_context='MWK:operators/game_exporter.py:69')
    skinning: BoolProperty(name=_zh_native("Skinning", 'MWK:operators/game_exporter.py:70'), default=True, translation_context='MWK:operators/game_exporter.py:70')
    blendshapes: BoolProperty(name=_zh_native("Blend Shapes", 'MWK:operators/game_exporter.py:71'), default=True, translation_context='MWK:operators/game_exporter.py:71')
    smoothing_groups: BoolProperty(name=_zh_native("Smoothing Groups", 'MWK:operators/game_exporter.py:72'), default=True, translation_context='MWK:operators/game_exporter.py:72')
    tangents: BoolProperty(name=_zh_native("Tangents and Binormals", 'MWK:operators/game_exporter.py:73'), default=True, translation_context='MWK:operators/game_exporter.py:73')
    triangulate: BoolProperty(name=_zh_native("Triangulate", 'MWK:operators/game_exporter.py:74'), default=False, translation_context='MWK:operators/game_exporter.py:74')
    move_to_origin: BoolProperty(name=_zh_native("Move to Origin", 'MWK:operators/game_exporter.py:75'), default=False, translation_context='MWK:operators/game_exporter.py:75')
    embed_media: BoolProperty(name=_zh_native("Embed Media", 'MWK:operators/game_exporter.py:76'), default=True, translation_context='MWK:operators/game_exporter.py:76')
    include_children: BoolProperty(name=_zh_native("Include Children", 'MWK:operators/game_exporter.py:77'), default=True, translation_context='MWK:operators/game_exporter.py:77')
    input_connections: BoolProperty(name=_zh_native("Input Connections", 'MWK:operators/game_exporter.py:78'), default=True, translation_context='MWK:operators/game_exporter.py:78')
    up_axis: EnumProperty(name=_zh_native("Up Axis", 'MWK:operators/game_exporter.py:79'), items=_zh_enum([('Y', "Y", ""), ('Z', "Z", "")], 'MWK:operators/game_exporter.py:79'), default='Y', translation_context='MWK:operators/game_exporter.py:79')
    include_cameras: BoolProperty(name=_zh_native("Cameras", 'MWK:operators/game_exporter.py:80'), default=True, translation_context='MWK:operators/game_exporter.py:80')
    include_lights: BoolProperty(name=_zh_native("Lights", 'MWK:operators/game_exporter.py:81'), default=True, translation_context='MWK:operators/game_exporter.py:81')
    # the Animation Clips tab's own values (Maya "Anim Default" preset)
    anim_embed_media: BoolProperty(name=_zh_native("Embed Media", 'MWK:operators/game_exporter.py:83'), default=True, translation_context='MWK:operators/game_exporter.py:83')
    anim_include_children: BoolProperty(name=_zh_native("Include Children", 'MWK:operators/game_exporter.py:84'), default=False, translation_context='MWK:operators/game_exporter.py:84')
    anim_input_connections: BoolProperty(name=_zh_native("Input Connections", 'MWK:operators/game_exporter.py:85'), default=False, translation_context='MWK:operators/game_exporter.py:85')
    anim_include_cameras: BoolProperty(name=_zh_native("Cameras", 'MWK:operators/game_exporter.py:86'), default=False, translation_context='MWK:operators/game_exporter.py:86')
    export_path: StringProperty(name=_zh_native("Path", 'MWK:operators/game_exporter.py:87'), subtype='DIR_PATH', translation_context='MWK:operators/game_exporter.py:87')
    export_filename: StringProperty(name=_zh_native("File Name", 'MWK:operators/game_exporter.py:88'), translation_context='MWK:operators/game_exporter.py:88')


def settings(context):
    return context.scene.allset_game_exporter


def tab_prop(s, name):
    """The property holding ``name`` for the tab in use (the Animation Clips tab keeps its own values)."""
    return "anim_" + name if s.export_type == 'ANIMATION' and name in TAB_PROPS else name


def value(s, name):
    return getattr(s, tab_prop(s, name))


# --- clips -------------------------------------------------------------------------------------------------------

def playback_range(scene):
    """Maya's playback range = the kit's preview range when it is on, else the scene range (step 20)."""
    if scene.use_preview_range:
        return float(scene.frame_preview_start), float(scene.frame_preview_end)
    return float(scene.frame_start), float(scene.frame_end)


def add_clip(scene):
    s = scene.allset_game_exporter
    clip = s.clips.add()
    clip.name = ""
    clip.start, clip.end = playback_range(scene)
    clip.export = True
    s.clip_index = len(s.clips) - 1
    return clip


def unique_name(name, taken):
    """Maya Game Exporter clip names: count up a trailing number (keeping its zeros), else append 1."""
    while name in taken:
        m = re.search(r"\d+$", name)
        if m:
            digits = m.group(0)
            number = int(digits) + 1
            width = len(digits) if len(str(number)) <= len(digits) else len(str(number))
            name = name[:m.start()] + str(number).zfill(width)
        else:
            name = name + "1"
    return name


def clip_files(s, folder):
    """[(path, [clips])] Maya writes for the exported clips."""
    clips = [c for c in s.clips if c.export]
    stem = s.export_filename
    if s.file_split == 'SINGLE':
        name = stem if os.path.splitext(stem)[1] else stem + ".fbx"
        return [(os.path.join(folder, name), clips)] if clips and stem else []
    base = stem[:-4] if stem.lower().endswith(".fbx") else stem
    out = []
    for c in clips:
        name = base + c.name
        out.append((os.path.join(folder, name if os.path.splitext(name)[1] else name + ".fbx"), [c]))
    return out


def model_files(s, folder, roots):
    stem = s.export_filename
    if s.model_file_mode == 'SINGLE':
        return [(os.path.join(folder, stem if os.path.splitext(stem)[1] else stem + ".fbx"), roots)] if stem else []
    base = stem[:-4] if stem.lower().endswith(".fbx") else stem
    return [(os.path.join(folder, base + r.name + ".fbx"), [r]) for r in roots]


# --- FBX ---------------------------------------------------------------------------------------------------------

def fbx_args(context, s, selection):
    from . import file_io, units
    _op, args = file_io.export_args('FBX', units.maya_unit(context.scene), selection)
    types = {'MESH', 'EMPTY', 'OTHER'}
    if s.skinning:
        types.add('ARMATURE')
    if value(s, "include_cameras"):
        types.add('CAMERA')
    if s.include_lights:
        types.add('LIGHT')
    args.update(object_types=types, mesh_smooth_type='FACE' if s.smoothing_groups else 'OFF',
                use_tspace=s.tangents, use_triangles=s.triangulate,
                axis_up=s.up_axis, axis_forward='-Z' if s.up_axis == 'Y' else 'Y')
    if value(s, "embed_media"):
        args.update(embed_textures=True, path_mode='COPY')
    return args


KTIME = 46186158000            # FBX ticks per second
ANIM_IDS = (b"AnimationStack", b"AnimationLayer", b"AnimationCurveNode", b"AnimationCurve")


class _ClipTimeline:
    """The scene's timeline = one clip while Blender's writer bakes it (its scene take, not NLA strips).

    Step 231 (Issue #140): the writer's NLA-strip takes evaluate one object's strip at a time (export_fbx_bin.py
    ``bake_anim_use_nla_strips``: every other strip muted, every active action removed), so a joint chain driven
    by another object (an IK handle's keys, a constraint target) was written without that object's animation —
    the audit's 21 cm IK arm. The timeline take evaluates the whole scene, like Maya's exporter, and leaves the
    kit's animation-layer NLA tracks out of the take list (they evaluate into the result instead). The scene gets
    a unique name while it writes: Blender derives a take's element ids from the scene name, so the takes of
    several clips can be merged into one file (``merge_takes``)."""

    def __init__(self, scene, clip, index):
        self.scene, self.clip, self.index = scene, clip, index

    def __enter__(self):
        sc = self.scene
        self.saved = (sc.name, sc.frame_start, sc.frame_end, sc.frame_current)
        start, end = int(round(self.clip.start)), int(round(self.clip.end))
        if end < start:
            raise ValueError(f"Clip {self.clip.name}: the end is before the start")
        name, n = f"{sc.name}.clip{self.index}", 0
        while name in bpy.data.scenes:
            n += 1
            name = f"{self.saved[0]}.clip{self.index}.{n}"
        sc.name = name
        _set_range(sc, start, end)
        return self

    def __exit__(self, *exc):
        sc = self.scene
        name, start, end, current = self.saved
        sc.name = name
        _set_range(sc, start, end)
        sc.frame_set(current)


def _set_range(sc, start, end):
    # Blender clamps frame_start to frame_end and back: widen first, then narrow
    sc.frame_end = max(end, sc.frame_end)
    sc.frame_start = start
    sc.frame_end = end


def _rename(elem, name):
    """An FBX object name is ``<name>\x00\x01<class>``."""
    old = elem.props[1]
    tail = old[old.index(b"\x00\x01"):] if b"\x00\x01" in old else b""
    elem.props[1] = name.encode("utf-8") + tail


def _text(v):
    return v.decode("utf-8", "replace") if isinstance(v, bytes) else v


def _same_kind(old, new):
    return new.encode("utf-8") if isinstance(old, bytes) else new


def merge_takes(path, parts, clips):
    """One file with a take per clip: ``path`` holds clip 0's take, ``parts[i]`` clip i+1's (the same objects
    written again, so the same object ids). Takes are renamed after their clips. Returns the take names."""
    from . import fbx_rig
    tree, version = fbx_rig.load(path)
    objects, conns = tree.first(b"Objects"), tree.first(b"Connections")
    takes = tree.first(b"Takes")
    have = {e.props[0] for e in objects.elems if e.props}
    added = {}
    for part in parts:
        other, _v = fbx_rig.load(part)
        anim = [e for e in other.first(b"Objects").elems if e.id in ANIM_IDS]
        ids = {e.props[0] for e in anim}
        if ids & have:
            raise RuntimeError("Game Exporter: two clips wrote the same take ids")
        objects.elems.extend(anim)
        have |= ids
        for e in anim:
            added[e.id] = added.get(e.id, 0) + 1
        conns.elems.extend(c for c in other.first(b"Connections").elems if c.props[1] in ids)
        o_takes = other.first(b"Takes")
        if takes is not None and o_takes is not None:
            takes.elems.extend(t for t in o_takes.elems if t.id == b"Take")
    defs = tree.first(b"Definitions")
    if defs is not None and added:
        for ot in defs.find(b"ObjectType"):
            n, cnt = added.get(ot.props[0]), ot.first(b"Count")
            if n and cnt is not None:
                cnt.props[0] += n
        total = defs.first(b"Count")
        if total is not None:
            total.props[0] += sum(added.values())
    stacks = objects.find(b"AnimationStack")
    children = {}
    for c in conns.elems:
        if c.props[0] == b"OO":
            children.setdefault(c.props[2], []).append(c.props[1])
    layers = {e.props[0]: e for e in objects.find(b"AnimationLayer")}
    names = []
    for st, clip in zip(stacks, clips):
        old = fbx_rig.name_of(st)
        _rename(st, clip.name)
        for lid in children.get(st.props[0], ()):
            if lid in layers:
                _rename(layers[lid], clip.name)
        for t in (takes.find(b"Take") if takes is not None else ()):
            if _text(t.props[0]) == old:
                t.props[0] = _same_kind(t.props[0], clip.name)
                for sub in t.elems:
                    if sub.id == b"FileName":
                        sub.props[0] = _same_kind(sub.props[0], clip.name + ".tak")
        names.append(clip.name)
    if takes is not None and names:
        cur = takes.first(b"Current")
        if cur is not None:
            cur.props[0] = _same_kind(cur.props[0], names[0])
    fbx_rig.save(path, tree, version)
    return names


class _Scope:
    """What a kit export leaves out (file_io ``_FileDialog``, steps 164 / 211 / 226): Export All = no startup
    cameras, never control shapes; Export Selection with Include Children = the selection with its hierarchy."""

    def __init__(self, context, selection, children):
        self.context, self.selection, self.children = context, selection, children
        self.stack = []

    def __enter__(self):
        from . import dag, startup_cameras
        from .control_shapes import excluded as shapes_excluded
        sc, vl = self.context.scene, self.context.view_layer
        cms = [shapes_excluded(sc, vl)]
        if not self.selection:
            cms.append(startup_cameras.excluded(sc, vl))
        elif self.children:
            cms.append(dag.selected_hierarchy(self.context))
        for cm in cms:
            cm.__enter__()
            self.stack.append(cm)
        return self

    def __exit__(self, *exc):
        while self.stack:
            self.stack.pop().__exit__(*exc)


def export(context, s):
    """Write the files; returns [(path, take names)]."""
    from . import file_io, units
    folder = bpy.path.abspath(s.export_path) or ""
    if not folder:
        raise ValueError("The file path is empty")            # Maya's error text
    if not os.path.isdir(folder):
        raise ValueError(f"The directory doesn't exist: {folder}")
    selection = s.export_set == 'SELECTION'
    view_layer = context.view_layer
    obs = list(context.selected_objects) if selection else [o for o in context.scene.objects
                                                            if o.name in view_layer.objects]
    if selection and not obs:
        raise ValueError("Nothing selected to export.")
    k = units.maya_unit(context.scene)
    out = []
    if s.export_type == 'ANIMATION':
        files = clip_files(s, folder)
        if not files:
            raise ValueError("Choose a file name to export" if not s.export_filename
                             else "The file name is empty or no clip is checked for export")
        names = [c.name for c in s.clips if c.export]
        if any(not n for n in names):
            raise ValueError("Cannot export a clip without a name.")         # Maya's text (B6)
        if len(set(names)) != len(names):
            raise ValueError("Every exported clip needs a unique name")
        for path, clips in files:
            args = dict(fbx_args(context, s, selection), bake_anim=True, bake_anim_use_nla_strips=False,
                        bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True)
            parts = []
            try:
                with _Scope(context, selection, value(s, "include_children")):
                    for i, clip in enumerate(clips):
                        part = path if i == 0 else os.path.splitext(path)[0] + f".clip{i}.tmp.fbx"
                        if i:
                            parts.append(part)
                        with _ClipTimeline(context.scene, clip, i):
                            file_io.write(context, 'FBX', part, "export_scene.fbx", args, True, k)
                out.append((path, merge_takes(path, parts, clips)))
            finally:
                for part in parts:                 # written beside the user's file, deleted at once
                    if os.path.exists(part):
                        os.remove(part)
        return out
    roots = [o for o in obs if o.parent is None or o.parent not in obs]
    files = model_files(s, folder, roots)
    if not files:
        raise ValueError("Choose a file name to export")            # Maya's text (B6)
    for path, part in files:
        args = dict(fbx_args(context, s, True), bake_anim=False)
        keep = list(context.selected_objects)
        try:
            for o in context.selected_objects:
                o.select_set(False)
            for r in part:
                for o in [r, *r.children_recursive]:
                    if o in obs and o.name in view_layer.objects:
                        o.select_set(True)
            file_io.write(context, 'FBX', path, "export_scene.fbx", args, True, k)
        finally:
            for o in context.selected_objects:
                o.select_set(False)
            for o in keep:
                o.select_set(True)
        out.append((path, []))
    return out


# --- window ------------------------------------------------------------------------------------------------------

class ALLSET_UL_game_clips(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        row = layout.row(align=True)
        row.prop(item, "export", text="")
        row.prop(item, "name", text="", emboss=True, placeholder="Clip Name")
        row.prop(item, "start", text="")
        row.prop(item, "end", text="")


class ALLSET_OT_game_clip(bpy.types.Operator):
    """Add a clip with the playback range, or delete the picked clip"""
    bl_translation_context = 'MWK:operators/game_exporter.py:411'
    bl_idname = "allset.game_clip"
    bl_label = _zh_native("Animation Clip", 'MWK:operators/game_exporter.py:411')
    bl_description = _zh_native('Add a clip with the playback range, or delete the picked clip', 'MWK:operators/game_exporter.py:411')
    bl_options = {'INTERNAL', 'UNDO'}

    action: EnumProperty(items=_zh_enum([('ADD', "Add", ""), ('REMOVE', "Delete", "")], 'MWK:operators/game_exporter.py:414'), options={'SKIP_SAVE'}, translation_context='MWK:operators/game_exporter.py:414')

    def execute(self, context):
        s = settings(context)
        if self.action == 'ADD':
            add_clip(context.scene)
        elif 0 <= s.clip_index < len(s.clips):
            s.clips.remove(s.clip_index)
            s.clip_index = max(0, min(s.clip_index, len(s.clips) - 1))
        return {'FINISHED'}


KIND = "GAME_EXPORTER"      # ui/marked_window.KINDS (step 263)


def _row(layout, label):
    """A Maya form row: the label left, the field right."""
    split = layout.split(factor=0.32)
    split.alignment = 'RIGHT'
    split.label(text=_zh(label, 'MWK:operators/game_exporter.py:433'))
    return split


def draw(layout, context):
    """The Game Exporter window (Maya's Game Exporter: tabs, export set, settings, Up Axis, Path / file name)."""
    s = settings(context)
    layout.row().prop(s, "export_type", expand=True)
    box = layout.box()
    box.row().prop(s, "export_set", expand=True)
    if s.export_type == 'MODEL':
        box.row().prop(s, "model_file_mode", expand=True)
    else:
        box.label(text=_zh("Animation Clips", 'MWK:operators/game_exporter.py:446'))
        row = box.row()
        row.template_list("ALLSET_UL_game_clips", "", s, "clips", s, "clip_index", rows=4)
        col = row.column(align=True)
        col.operator("allset.game_clip", text="", icon='ADD').action = 'ADD'
        col.operator("allset.game_clip", text="", icon='REMOVE').action = 'REMOVE'
        box.row().prop(s, "file_split", expand=True)
        box.prop(s, "bake_animation")
    col = layout.box().column(align=True)
    col.label(text=_zh("Export Settings", 'MWK:operators/game_exporter.py:455'))
    grid = col.grid_flow(columns=2, align=True)
    for name in ("skinning", "blendshapes", "smoothing_groups", "tangents", "triangulate", "move_to_origin",
                 "embed_media", "include_children", "include_cameras", "include_lights"):
        sub = grid.row()
        sub.enabled = name not in {"blendshapes", "move_to_origin"}
        sub.prop(s, tab_prop(s, name))
    # Maya: the "Up Axis" label, then Y / Z
    _row(col, "Up Axis").row().prop(s, "up_axis", expand=True)
    box = layout.box()
    _row(box, "Path").prop(s, "export_path", text="", placeholder="Choose an export directory")
    _row(box, "File Name").prop(s, "export_filename", text="", placeholder=filename_placeholder(s))
    folder = bpy.path.abspath(s.export_path)
    files = clip_files(s, folder) if s.export_type == 'ANIMATION' else []
    for path, clips in files[:4]:
        box.label(text=_zh(os.path.basename(path) + ("   " + ", ".join(c.name for c in clips) if clips else ""), 'MWK:operators/game_exporter.py:470'),
                  icon='FILE')
    layout.separator()
    layout.operator("allset.game_export", text=_zh("Export", 'MWK:operators/game_exporter.py:473'))


def filename_placeholder(s):
    """Maya's grey hint in the empty file name field (B6): one file vs a prefix for several files."""
    if s.export_type == 'MODEL':
        return "Enter a filename" if s.model_file_mode == 'SINGLE' else "Multi File Prefix"
    return "Enter a filename" if s.file_split == 'SINGLE' else "Clip File Prefix"


class ALLSET_OT_game_exporter(bpy.types.Operator):
    """Maya Game Exporter: export models or animation clips (one FBX take per clip) for a game engine"""
    bl_translation_context = 'MWK:operators/game_exporter.py:486'
    bl_idname = "allset.game_exporter"
    bl_label = _zh_native("Game Exporter", 'MWK:operators/game_exporter.py:486')
    bl_description = _zh_native('Maya Game Exporter: export models or animation clips (one FBX take per clip) for a game engine', 'MWK:operators/game_exporter.py:486')

    def execute(self, context):
        # step 263 (Issue #154): Maya's Game Exporter is an ordinary floating window that stays open while you work
        # (a floating Maya window, B6) — a kit window, no longer a popup a click outside closed
        from ..ui import marked_window
        s = settings(context)
        if not s.export_path:
            from . import project
            s.export_path = project.ensure_root(context)   # the default project's folders exist (step 240 QA H1-1)
        if context.window is None:
            return {'CANCELLED'}
        if marked_window.open_window(context, KIND) is None:
            self.report({'ERROR'}, _zh("Could not open the Game Exporter window", 'MWK:operators/game_exporter.py:499'))
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_game_export(bpy.types.Operator):
    """Export with the Game Exporter's settings"""
    bl_translation_context = 'MWK:operators/game_exporter.py:507'
    bl_idname = "allset.game_export"
    bl_label = _zh_native("Export", 'MWK:operators/game_exporter.py:507')
    bl_description = _zh_native("Export with the Game Exporter's settings", 'MWK:operators/game_exporter.py:507')
    bl_options = {'UNDO'}

    def execute(self, context):
        try:
            done = export(context, settings(context))
        except (ValueError, RuntimeError) as ex:
            self.report({'ERROR'}, _zh(str(ex).strip().splitlines()[-1], 'MWK:operators/game_exporter.py:514'))
            return {'CANCELLED'}
        results.result(self, _zh("Exported " + ", ".join(os.path.basename(p) for p, _t in done), 'MWK:operators/game_exporter.py:516'))
        return {'FINISHED'}


class ALLSET_PT_game_exporter(bpy.types.Panel):
    bl_translation_context = 'MWK:operators/game_exporter.py:525'
    bl_idname = "ALLSET_PT_game_exporter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"            # = drawn by the Properties Tool tab (step 106 mechanism)
    bl_label = _zh_native("Game Exporter", 'MWK:operators/game_exporter.py:525')
    bl_options = {'HIDE_HEADER'}
    bl_order = -300

    @classmethod
    def poll(cls, context):
        from ..ui import marked_window
        return marked_window.context_kind(context) == KIND

    def draw(self, context):
        draw(self.layout, context)


classes = (ALLSET_PG_game_clip, ALLSET_PG_game_exporter, ALLSET_UL_game_clips, ALLSET_OT_game_clip,
           ALLSET_OT_game_exporter, ALLSET_OT_game_export, ALLSET_PT_game_exporter)


def register_props():
    bpy.types.Scene.allset_game_exporter = PointerProperty(type=ALLSET_PG_game_exporter, translation_context='MWK:operators/game_exporter.py:543')


def unregister_props():
    del bpy.types.Scene.allset_game_exporter

# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya Render Settings window (docs/steps/step_105.md 「계획」 2).

Maya 2022 (menus and factory values): a window with the menu bar Edit / Presets / Help, the rows
Render Layer and Render Using, then the tabs Common | <renderer>. Common holds the output: Path / File name / Image
size lines, Color Management, File Output (file name prefix, image format, Frame/Animation ext, frame padding),
Frame Range, Renderable Cameras, Image Size (presets, HD 540 = 960 x 540 by default).

Blender: ``allset.render_settings`` opens a Properties window on the Render tab only, marked as the kit's (window
pointer, like the Light Editor). Its header draws the Maya menus, ``ALLSET_PT_rs_head`` the two rows and the tabs.
Common = ``ALLSET_PT_rs_common`` drawn over ``scene.render`` through Scene properties with get / set (a UI edit
pushes an undo step, step 38); the renderer tab = Blender's own Render panels. Those are hidden in the Common tab by
wrapping their poll (the ``ui/dock_tabs.py`` technique), only in the marked window.
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import os

import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty

_WINDOWS = set()        # window pointers of kit Render Settings windows
_wrapped = []           # (panel class, its own poll or None, child panels)

# Maya image size presets (Render Settings Presets labels; sizes [K] Maya presets, HD 540 = 960 x 540 is the
# factory default): key -> (label, width, height, pixel aspect)
SIZES = (
    ("320x240", "320x240", 320, 240, 1.0), ("640x480", "640x480", 640, 480, 1.0),
    ("1K_SQUARE", "1k Square", 1024, 1024, 1.0), ("2K_SQUARE", "2k Square", 2048, 2048, 1.0),
    ("3K_SQUARE", "3k Square", 3072, 3072, 1.0), ("4K_SQUARE", "4k Square", 4096, 4096, 1.0),
    ("CCIR_PAL", "CCIR PAL/Quantel PAL", 720, 576, 1.067), ("CCIR_601", "CCIR 601/Quantel NTSC", 720, 486, 0.9),
    ("FULL_1024", "Full 1024", 1024, 768, 1.0), ("FULL_1280", "Full 1280/Screen", 1280, 1024, 1.0),
    ("HD_540", "HD 540", 960, 540, 1.0), ("HD_720", "HD 720", 1280, 720, 1.0), ("HD_1080", "HD 1080", 1920, 1080, 1.0),
    ("NTSC_4D", "NTSC 4d", 646, 485, 1.0), ("PAL_768", "PAL 768", 768, 576, 1.0), ("PAL_780", "PAL 780", 780, 576, 1.0),
    ("TARGA_486", "Targa 486 (tga)", 512, 486, 1.0), ("TARGA_NTSC", "Targa NTSC (tga)", 512, 482, 1.0),
    ("TARGA_PAL", "Targa PAL (tga)", 512, 576, 1.0),
)
SIZE_ITEMS = [("CUSTOM", "Custom", "Width and height of your own")] + [
    (k, label, f"{w} x {h}") for k, label, w, h, _a in SIZES]
# Maya Frame/Animation ext choices Blender can write (render.filepath patterns); the Maya label first
EXTS = (("SINGLE", "name.ext (Single Frame)", ""), ("DOT", "name.#.ext", "."), ("PLAIN", "name#.ext", ""),
        ("UNDERSCORE", "name_#.ext", "_"))
# Maya factory values (defaultResolution 960 x 540, imageFormat 32 = PNG, extensionPadding 4, animation off)
DEFAULTS = {"size": "HD_540", "file_format": 'PNG', "padding": 4, "ext": "SINGLE"}


def mark(window):
    _WINDOWS.add(window.as_pointer())


def is_render_settings(context):
    window, space = context.window, context.space_data
    return (window is not None and space is not None and space.type == 'PROPERTIES'
            and window.as_pointer() in _WINDOWS)


# --- render.filepath <-> Maya Path / File name prefix / ext / padding ----------------------------------------------

def split_path(filepath):
    """(directory, prefix, ext key, padding) of a Blender output path ("//../images/shot.####")."""
    head, tail = os.path.split(filepath)
    if filepath.endswith(("/", "\\")):
        head, tail = filepath, ""
    n = len(tail) - len(tail.rstrip("#"))
    stem = tail[:len(tail) - n] if n else tail
    ext = "SINGLE"
    if n:
        if stem.endswith("."):
            ext, stem = "DOT", stem[:-1]
        elif stem.endswith("_"):
            ext, stem = "UNDERSCORE", stem[:-1]
        else:
            ext = "PLAIN"
    return head, stem, ext, n


def join_path(directory, prefix, ext, padding):
    sep = dict((k, s) for k, _l, s in EXTS)[ext]
    tail = prefix + ("" if ext == "SINGLE" else sep + "#" * max(1, padding))
    if not directory:
        return tail
    return directory + ("" if directory.endswith(("/", "\\")) else os.sep) + tail


def _rw(field):
    def get(scene):
        d, p, e, n = split_path(scene.render.filepath)
        # a single-frame name has no frame number: Maya still shows its padding (4, greyed)
        return {"dir": d, "prefix": p, "ext": e, "padding": n or DEFAULTS["padding"]}[field]

    def set_(scene, value):
        d, p, e, n = split_path(scene.render.filepath)
        parts = {"dir": d, "prefix": p, "ext": e, "padding": n or DEFAULTS["padding"]}
        if field == "ext":
            value = [k for k, _l, _s in EXTS][value]
        parts[field] = value
        scene.render.filepath = join_path(parts["dir"], parts["prefix"], parts["ext"], parts["padding"])
    return get, set_


def _ext_get(scene):
    return [k for k, _l, _s in EXTS].index(split_path(scene.render.filepath)[2])


def size_key(render):
    for k, _label, w, h, a in SIZES:
        if (render.resolution_x, render.resolution_y) == (w, h) and abs(render.pixel_aspect_x / render.pixel_aspect_y
                                                                      - a) < 1e-3:
            return k
    return "CUSTOM"


def _size_get(scene):
    return [k for k, _l, _d in SIZE_ITEMS].index(size_key(scene.render))


def apply_size(render, key):
    for k, _label, w, h, a in SIZES:
        if k == key:
            render.resolution_x, render.resolution_y = w, h
            render.resolution_percentage = 100
            # Blender's pixel aspect fields start at 1: an aspect below 1 is written as 1 : 1/a
            render.pixel_aspect_x, render.pixel_aspect_y = (a, 1.0) if a >= 1.0 else (1.0, 1.0 / a)
            return True
    return False


def _size_set(scene, index):
    apply_size(scene.render, SIZE_ITEMS[index][0])


def apply_defaults(scene):
    """Maya Presets > Import Render Settings > Default Settings: HD 540, PNG, single frame, padding 4 (the frame range
    stays: Blender has one range for the Time Slider and the render)."""
    r = scene.render
    apply_size(r, DEFAULTS["size"])
    from .. import compat
    compat.set_file_format(r.image_settings, DEFAULTS["file_format"])
    d, p, _e, _n = split_path(r.filepath)
    r.filepath = join_path(d, p, DEFAULTS["ext"], DEFAULTS["padding"])


def info_lines(scene):
    """Maya's three lines over the Common tab: Path, File name, Image size."""
    r = scene.render
    d, p, _e, _n = split_path(r.filepath)
    name = os.path.basename(r.frame_path(frame=scene.frame_start)) if p or _e != "SINGLE" else \
        f"{bpy.path.display_name_from_filepath(bpy.data.filepath) or 'untitled'}{r.file_extension}"
    w = r.resolution_x * r.resolution_percentage // 100
    h = r.resolution_y * r.resolution_percentage // 100
    return (f"Path: {bpy.path.abspath(d) if d else '(scene folder)'}", f"File name: {name}",
            f"Image size: {w} x {h} ({w / 72:.1f} x {h / 72:.1f} inches 72 pixels/inch)")


# --- panels ------------------------------------------------------------------------------------------------------

def _tab_items(self, context):
    scene = context.scene if context else bpy.context.scene
    engine = scene.render.engine
    try:
        label = scene.render.bl_rna.properties["engine"].enum_items[engine].name
    except (KeyError, AttributeError):
        label = engine.title()
    return [("COMMON", "Common", "Maya Common tab: output path, frame range, cameras, image size"),
            ("RENDERER", label, "The renderer's settings (Blender's Render properties)")]


class _Panel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    @classmethod
    def poll(cls, context):
        return is_render_settings(context)


class ALLSET_PT_rs_head(_Panel, bpy.types.Panel):
    bl_translation_context = 'MWK:ui/render_settings.py:180'
    bl_label = _zh_native("Render Settings", 'MWK:ui/render_settings.py:180')
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        window, scene = context.window, context.scene
        layout.template_search(window, "view_layer", scene, "view_layers", text=_zh("Render Layer", 'MWK:ui/render_settings.py:188'))
        layout.prop(scene.render, "engine", text=_zh("Render Using", 'MWK:ui/render_settings.py:189'))
        layout.use_property_split = False
        layout.row(align=True).prop(context.window_manager, "allset_rs_tab", expand=True)


class ALLSET_PT_rs_common(_Panel, bpy.types.Panel):
    bl_translation_context = 'MWK:ui/render_settings.py:195'
    bl_label = _zh_native("Common", 'MWK:ui/render_settings.py:195')
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return is_render_settings(context) and context.window_manager.allset_rs_tab == 'COMMON'

    def draw(self, context):
        draw_common(self.layout, context)


def draw_common(layout, context):
    scene = context.scene
    r = scene.render
    col = layout.column(align=True)
    for line in info_lines(scene):
        col.label(text=_zh(line, 'MWK:ui/render_settings.py:211'))
    header, body = layout.panel("ALLSET_rs_color", default_closed=True)
    header.label(text=_zh("Color Management", 'MWK:ui/render_settings.py:213'))
    if body:
        body.use_property_split = True
        body.prop(scene.view_settings, "view_transform", text=_zh("View Transform", 'MWK:ui/render_settings.py:216'))
        body.prop(scene.display_settings, "display_device", text=_zh("Display", 'MWK:ui/render_settings.py:217'))
    header, body = layout.panel("ALLSET_rs_file_output", default_closed=False)
    header.label(text=_zh("File Output", 'MWK:ui/render_settings.py:219'))
    if body:
        body.use_property_split = True
        body.prop(scene, "allset_rs_dir", text=_zh("Path", 'MWK:ui/render_settings.py:222'))
        body.prop(scene, "allset_rs_prefix", text=_zh("File name prefix", 'MWK:ui/render_settings.py:223'))
        if not scene.allset_rs_prefix:
            body.label(text=_zh("(not set; using scene name)", 'MWK:ui/render_settings.py:225'))
        body.prop(r.image_settings, "file_format", text=_zh("Image format", 'MWK:ui/render_settings.py:226'))
        body.prop(scene, "allset_rs_ext", text=_zh("Frame/Animation ext", 'MWK:ui/render_settings.py:227'))
        sub = body.row()
        sub.enabled = scene.allset_rs_ext != 'SINGLE'
        sub.prop(scene, "allset_rs_padding", text=_zh("Frame padding", 'MWK:ui/render_settings.py:230'))
    header, body = layout.panel("ALLSET_rs_frames", default_closed=False)
    header.label(text=_zh("Frame Range", 'MWK:ui/render_settings.py:232'))
    if body:
        body.use_property_split = True
        body.prop(scene, "frame_start", text=_zh("Start frame", 'MWK:ui/render_settings.py:235'))
        body.prop(scene, "frame_end", text=_zh("End frame", 'MWK:ui/render_settings.py:236'))
        body.prop(scene, "frame_step", text=_zh("By frame", 'MWK:ui/render_settings.py:237'))
    header, body = layout.panel("ALLSET_rs_cameras", default_closed=False)
    header.label(text=_zh("Renderable Cameras", 'MWK:ui/render_settings.py:239'))
    if body:
        body.use_property_split = True
        body.prop(scene, "camera", text=_zh("Renderable Camera", 'MWK:ui/render_settings.py:242'))
    header, body = layout.panel("ALLSET_rs_size", default_closed=False)
    header.label(text=_zh("Image Size", 'MWK:ui/render_settings.py:244'))
    if body:
        body.use_property_split = True
        body.prop(scene, "allset_rs_size", text=_zh("Presets", 'MWK:ui/render_settings.py:247'))
        body.prop(r, "resolution_x", text=_zh("Width", 'MWK:ui/render_settings.py:248'))
        body.prop(r, "resolution_y", text=_zh("Height", 'MWK:ui/render_settings.py:249'))
        body.prop(r, "resolution_percentage", text=_zh("Scale (Blender)", 'MWK:ui/render_settings.py:250'))
        aspect = r.resolution_x * r.pixel_aspect_x / max(1.0, r.resolution_y * r.pixel_aspect_y)
        body.label(text=_zh(f"Device aspect ratio: {aspect:.3f}", 'MWK:ui/render_settings.py:252'))
        body.label(text=_zh(f"Pixel aspect ratio: {r.pixel_aspect_x / r.pixel_aspect_y:.3f}", 'MWK:ui/render_settings.py:253'))
        row = body.row(align=True)
        row.prop(r, "pixel_aspect_x", text=_zh("Pixel aspect X", 'MWK:ui/render_settings.py:255'))
        row.prop(r, "pixel_aspect_y", text=_zh("Y", 'MWK:ui/render_settings.py:256'))
    # Maya Common > Render Options (step 152): Enable Default Light, factory on (operators/default_light.py)
    header, body = layout.panel("ALLSET_rs_options", default_closed=False)
    header.label(text=_zh("Render Options", 'MWK:ui/render_settings.py:259'))
    if body and hasattr(scene, "allset_default_light"):
        body.use_property_split = True
        body.prop(scene, "allset_default_light", text=_zh("Enable Default Light", 'MWK:ui/render_settings.py:262'))


class ALLSET_OT_rs_defaults(bpy.types.Operator):
    """Maya Presets > Import Render Settings > Default Settings: HD 540 (960 x 540), PNG, single frame, padding 4"""
    bl_translation_context = 'MWK:ui/render_settings.py:268'
    bl_idname = "allset.rs_defaults"
    bl_label = _zh_native("Default Render Settings", 'MWK:ui/render_settings.py:268')
    bl_description = _zh_native('Maya Presets > Import Render Settings > Default Settings: HD 540 (960 x 540), PNG, single frame, padding 4', 'MWK:ui/render_settings.py:268')
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        apply_defaults(context.scene)
        return {'FINISHED'}


# --- window -----------------------------------------------------------------------------------------------------

def open_window(context):
    """A new Properties window on the Render tab only, marked as the kit's Render Settings."""
    from ..operators import menu_extras
    area = max(context.window.screen.areas, key=lambda a: a.width * a.height, default=None)
    if area is None:
        return None
    window = menu_extras.open_window(context, area)
    if window is None:
        return None
    target = window.screen.areas[0]
    target.ui_type = 'PROPERTIES'
    space = target.spaces.active
    for prop in space.bl_rna.properties:
        if prop.identifier.startswith("show_properties_"):
            setattr(space, prop.identifier, prop.identifier == "show_properties_render")
    try:
        space.context = 'RENDER'
    except TypeError:
        pass
    mark(window)
    context.window_manager.allset_rs_tab = 'COMMON'
    return window


def _header_draw(self, context):
    if not is_render_settings(context):
        return _orig["header"](self, context)
    from . import editor_chrome
    layout = self.layout
    layout.template_header()
    editor_chrome.draw_menus(layout, context, "Render Settings")


_orig = {}


# --- hiding Blender's Render panels in the Common tab (ui/dock_tabs.py technique) ------------------------------

def _hidden(context):
    if not is_render_settings(context):
        return False
    return context.window_manager.allset_rs_tab == 'COMMON'


def _make_poll(original, always=False):
    def poll(cls, context):
        if (always and is_render_settings(context)) or _hidden(context):
            return False
        return original(context) if original is not None else True
    return classmethod(poll)


def _subclasses(cls):
    for sub in cls.__subclasses__():
        yield sub
        yield from _subclasses(sub)


def _module_names(cls):
    """Global names of the module that defined ``cls``, read from one of its own functions (draw / poll ...) — no
    lookup in the module table (step 130); {} when the class defines no function itself."""
    for attr in vars(cls).values():
        func = getattr(attr, "__func__", attr)          # classmethod / staticmethod
        names = getattr(func, "__globals__", None)
        if isinstance(names, dict) and names.get("__name__") == cls.__module__:
            return names
    return {}


def _class_order(cls):
    """The defining module's ``classes`` sequence, or [] when it isn't a tuple / list. Third-party render panels
    can come from modules whose global ``classes`` is something else — a submodule (``from . import classes``),
    a dict, a generator — which made Maya mode fail to switch on (#79, 'module' object is not iterable)."""
    seq = _module_names(cls).get("classes", ())
    if not isinstance(seq, (tuple, list)):
        return []
    return list(seq)


def registration_key(cls):
    """Blender lists panels in registration order, and re-registering moves a panel to the end: re-register them in
    the order they were registered — bl_ui modules in ``bl_ui._modules`` order, each module's ``classes`` tuple
    order, add-ons (Cycles) after them (measured: subclass order put EEVEE's Motion Blur above Sampling)."""
    seq = _class_order(cls)
    index = seq.index(cls) if cls in seq else len(seq)
    if cls.__module__.startswith("bl_ui."):
        import bl_ui
        names = list(getattr(bl_ui, "_modules", ()))
        name = cls.__module__.split(".", 1)[1]
        return (0, names.index(name) if name in names else len(names), "", index)
    return (1, 0, cls.__module__, index)


def render_panels():
    """Top-level Properties > Render panels that aren't the kit's, registered now, in registration order."""
    seen, out = set(), []
    for cls in _subclasses(bpy.types.Panel):
        if cls in seen or cls.__name__.startswith("ALLSET_"):
            continue
        seen.add(cls)
        if (getattr(cls, "bl_space_type", None) == 'PROPERTIES' and getattr(cls, "bl_context", "") == "render"
                and not getattr(cls, "bl_parent_id", "") and cls.is_registered):
            out.append(cls)
    return sorted(out, key=registration_key)


def _children(parent, panels):
    pid = getattr(parent, "bl_idname", "") or parent.__name__
    for cls in sorted(panels, key=registration_key):
        if getattr(cls, "bl_parent_id", "") == pid and cls.is_registered:
            yield cls
            yield from _children(cls, panels)


def _reregister(cls, kids, poll):
    for kid in reversed(kids):
        if kid.is_registered:
            bpy.utils.unregister_class(kid)
    if cls.is_registered:
        bpy.utils.unregister_class(cls)
    if poll is not None:
        cls.poll = poll
    elif "poll" in cls.__dict__:
        del cls.poll
    bpy.utils.register_class(cls)
    for kid in kids:
        bpy.utils.register_class(kid)


def wrap_panels():
    everything = [c for c in _subclasses(bpy.types.Panel) if getattr(c, "bl_space_type", None) == 'PROPERTIES']
    for cls in render_panels():
        raw = cls.__dict__.get("poll")
        kids = list(_children(cls, everything))
        # RENDER_PT_context = Blender's engine row: the kit's Render Using row replaces it in the window
        _reregister(cls, kids, _make_poll(getattr(cls, "poll", None), always=cls.__name__ == "RENDER_PT_context"))
        _wrapped.append((cls, raw, kids))


def unwrap_panels():
    """Original polls back. A class its owner already unregistered (an add-on going away first, e.g. Cycles while a
    template load re-enables add-ons) only gets its poll back: registering it again would make the owner's own
    register fail ("already registered")."""
    for cls, raw, kids in _wrapped:     # forward: the registration order again
        if cls.is_registered:
            _reregister(cls, [k for k in kids if k.is_registered], raw)
        elif raw is not None:
            cls.poll = raw
        elif "poll" in cls.__dict__:
            del cls.poll
    _wrapped.clear()


classes = (ALLSET_PT_rs_head, ALLSET_PT_rs_common, ALLSET_OT_rs_defaults)


def register():
    sc = bpy.types.Scene
    get, set_ = _rw("dir")
    sc.allset_rs_dir = StringProperty(name=_zh_native("Path", 'MWK:ui/render_settings.py:437'), subtype='DIR_PATH', get=get, set=set_,
                                        description=_zh_native("Maya Render Settings Path: the folder of the render output", 'MWK:ui/render_settings.py:437'), translation_context='MWK:ui/render_settings.py:437')
    get, set_ = _rw("prefix")
    sc.allset_rs_prefix = StringProperty(name=_zh_native("File name prefix", 'MWK:ui/render_settings.py:440'), get=get, set=set_,
                                           description=_zh_native("Maya File name prefix (empty = the scene name)", 'MWK:ui/render_settings.py:440'), translation_context='MWK:ui/render_settings.py:440')
    _g, set_ = _rw("ext")
    sc.allset_rs_ext = EnumProperty(name=_zh_native("Frame/Animation ext", 'MWK:ui/render_settings.py:443'), items=_zh_enum([(k, l, "") for k, l, _s in EXTS], 'MWK:ui/render_settings.py:443'),
                                      get=_ext_get, set=set_,
                                      description=_zh_native("Maya Frame/Animation ext: how the frame number joins the name", 'MWK:ui/render_settings.py:443'), translation_context='MWK:ui/render_settings.py:443')
    get, set_ = _rw("padding")
    sc.allset_rs_padding = IntProperty(name=_zh_native("Frame padding", 'MWK:ui/render_settings.py:447'), min=1, max=10, get=get, set=set_,
                                         description=_zh_native("Digits of the frame number (Maya extensionPadding)", 'MWK:ui/render_settings.py:447'), translation_context='MWK:ui/render_settings.py:447')
    sc.allset_rs_size = EnumProperty(name=_zh_native("Image Size Presets", 'MWK:ui/render_settings.py:449'), items=_zh_enum(SIZE_ITEMS, 'MWK:ui/render_settings.py:449'), get=_size_get, set=_size_set,
                                       description=_zh_native("Maya image size presets (HD 540 = 960 x 540 is Maya's default)", 'MWK:ui/render_settings.py:449'), translation_context='MWK:ui/render_settings.py:449')
    bpy.types.WindowManager.allset_rs_tab = EnumProperty(name=_zh_native("Render Settings Tab", 'MWK:ui/render_settings.py:451'), items=_zh_enum(_tab_items, 'MWK:ui/render_settings.py:451'),
                                                           options={'SKIP_SAVE'}, translation_context='MWK:ui/render_settings.py:451')
    for cls in classes:
        bpy.utils.register_class(cls)
    wrap_panels()      # after the kit panels: Blender's re-registered ones come after them
    funcs = bpy.types.PROPERTIES_HT_header._dyn_ui_initialize()
    _orig["header"] = funcs[0]
    funcs[0] = _header_draw


def unregister():
    if "header" in _orig:
        bpy.types.PROPERTIES_HT_header._dyn_ui_initialize()[0] = _orig.pop("header")
    unwrap_panels()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for name in ("allset_rs_dir", "allset_rs_prefix", "allset_rs_ext", "allset_rs_padding",
                 "allset_rs_size"):
        delattr(bpy.types.Scene, name)
    del bpy.types.WindowManager.allset_rs_tab
    _WINDOWS.clear()

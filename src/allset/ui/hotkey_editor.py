# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya's Hotkey Editor window (step 215, Issue #121; Windows > Settings/Preferences > Hotkey Editor).

Maya 2022's Hotkey Editor lists the commands of the current hotkey set with their keys, searches them by name or by
hotkey, filters by category, and lets a key be assigned (warning when another command already uses it). The kit's
list = Maya's factory hotkeys (``keymap/hotkey_rows``: Maya's factory hotkey list joined with ``keymap/mapping.py``) with what
the kit binds for each one.

A binding is changed the Blender way: on the item of ``wm.keyconfigs.user`` — the merged keymap Blender's own
Preferences > Keymap edits. Measured (step 215, Blender 4.5, tests/test_step215_hotkeys.py): the user keyconfig holds
the kit's add-on items at the head of each keymap; changing ``type`` / modifiers there marks the keymap user-modified
and leaves the add-on item as it was; ``KeyMap.restore_item_to_default`` brings the Maya key back; the edit survives
Maya mode off / on (Blender re-applies the keymap diff to the re-added add-on items); the kit writes no file — the
edit is kept only by Blender's own Save Preferences / auto-save (``preferences.is_dirty`` turns on), exactly like an
edit in Blender's keymap editor. Only rows whose binding is a kit add-on item (status KIT / IC with a check) can be
changed; the active keyconfig is never touched.

Window = a ``marked_window`` kind "HOTKEY_EDITOR" (Properties Tool tab in its own window). Rows live in a
WindowManager collection rebuilt by the search / category updates and the edit operators, never in ``draw``.
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, StringProperty

from . import marked_window
from ..keymap import hotkey_rows, mapping

KIND = "HOTKEY_EDITOR"
TITLE = "Hotkey Editor"
SET_NAME = "Maya Workflow Kit"          # names.PRODUCT; Maya shows the current hotkey set's name ("Maya_Default")
COLUMNS = (("Command", 0.36), ("Maya Hotkey", 0.17), ("Kit Hotkey", 0.24), ("Status", 1.0))
PERSIST_NOTE = "Changes are Blender keymap edits: Save Preferences (or auto-save) keeps them"

# Blender keymaps of one object mode each (keymap/maya_patches.MODE_KEYMAPS + Sculpt)
MODE_KEYMAPS = frozenset(("Object Mode", "Mesh", "Pose", "Curve", "Curves", "Armature", "Metaball", "Lattice",
                          "Particle", "Font", "Sculpt", "Weight Paint", "Vertex Paint", "Image Paint"))
_ROWS = []            # hotkey_rows.build_rows(), built once
_BY_INDEX = {}
_SIBLINGS = {}        # check signature -> [row]
_CATEGORIES = []      # EnumProperty items (kept referenced: Blender reads the strings later)

_IGNORE = {"MOUSEMOVE", "INBETWEEN_MOUSEMOVE", "TIMER", "TIMER_REPORT", "TIMERREGION", "NONE", "WINDOW_DEACTIVATE",
           "LEFT_CTRL", "RIGHT_CTRL", "LEFT_SHIFT", "RIGHT_SHIFT", "LEFT_ALT", "RIGHT_ALT", "OSKEY", "TEXTINPUT",
           "WHEELUPMOUSE", "WHEELDOWNMOUSE", "WHEELINMOUSE", "WHEELOUTMOUSE", "TRACKPADPAN", "TRACKPADZOOM",
           "MOUSEROTATE", "MOUSESMARTZOOM", "KM_TEXTINPUT"}
_CANCEL = {"ESC", "LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE", "BUTTON4MOUSE", "BUTTON5MOUSE"}


def rows():
    if not _ROWS:
        _ROWS.extend(hotkey_rows.build_rows())
        _BY_INDEX.update((r["index"], r) for r in _ROWS)
        for r in _ROWS:
            if r["check"]:
                _SIBLINGS.setdefault(_sig(r["check"]), []).append(r)
    return _ROWS


def row_of(index):
    rows()
    return _BY_INDEX.get(index)


def _sig(check):
    km, idname, props = check
    return km, idname, tuple(sorted((k, repr(v)) for k, v in props.items()))


def category_items(self, context):
    if not _CATEGORIES:
        _CATEGORIES.append(("ALL", "All Categories", "Every Maya hotkey"))
        _CATEGORIES.extend((c, c, f"Maya hotkeys of {c}") for c in hotkey_rows.categories(rows()))
    return _CATEGORIES


# --- live keymap items (wm.keyconfigs.user) ---------------------------------------------------------------------

def item_event(kmi):
    return {"type": kmi.type, "value": kmi.value, "any": kmi.any, "ctrl": bool(kmi.ctrl), "alt": bool(kmi.alt),
            "shift": bool(kmi.shift), "oskey": bool(kmi.oskey)}


def _norm(value):
    if isinstance(value, float):
        return round(value, 5)          # float32 storage: 0.8 reads back as 0.800000011920929
    if isinstance(value, (set, frozenset)):
        return frozenset(value)
    if not isinstance(value, str) and hasattr(value, "__len__"):
        return tuple(value)
    return value


def _prop(p, name):
    """An item property's value; an unset one = its RNA default, None for an unset enum (reading an unset enum whose
    default isn't an item prints a bpy.rna warning, e.g. allset.set_key ``channels``)."""
    rna = p.bl_rna.properties.get(name)
    if rna is None:
        raise AttributeError(name)
    if p.is_property_set(name):
        return getattr(p, name)
    if getattr(rna, "is_array", False):
        return tuple(rna.default_array)
    if rna.type == 'ENUM':
        # even ``rna.default`` warns when the default is no item; the kit's add-on items set what they compare
        return None
    return rna.default


def _props_match(kmi, want):
    p = kmi.properties
    for k, v in want.items():
        try:
            cur = _prop(p, k) if p is not None else None
        except AttributeError:
            return False
        if p is None or _norm(cur) != _norm(v):
            return False
    return True


def _user_keymaps(context):
    kcs = context.window_manager.keyconfigs
    return kcs.user.keymaps if kcs.user is not None else None


def _is_addon_item(context, km_name, kmi):
    """The add-on keyconfig (where the kit puts the Maya keymap) has an item of this operator + properties."""
    addon = context.window_manager.keyconfigs.addon
    km = addon.keymaps.get(km_name) if addon is not None else None
    if km is None:
        return False
    want = {k: getattr(kmi.properties, k) for k in kmi.properties.bl_rna.properties.keys()
            if k != "rna_type" and kmi.properties.is_property_set(k)} if kmi.properties is not None else {}
    return any(k.idname == kmi.idname and _props_match(k, want) for k in km.keymap_items)


def find_item(context, row):
    """(user KeyMap, KeyMapItem) that implements ``row`` (a kit add-on item), else (KeyMap or None, None).

    The item with the row's Maya key wins; a changed one (``is_user_modified``) is found by operator + properties
    when no other row of the same operator owns its key."""
    if not row or not row["check"]:
        return None, None
    kms = _user_keymaps(context)
    km_name, idname, want = row["check"]
    km = kms.get(km_name) if kms is not None else None
    if km is None:
        return None, None
    cands = [k for k in km.keymap_items
             if k.idname == idname and (k.active or k.is_user_modified) and _props_match(k, want)]
    want_key = hotkey_rows.event_key(row["event"])
    for k in cands:
        if hotkey_rows.event_key(item_event(k)) == want_key:
            return km, k
    others = {hotkey_rows.event_key(r["event"]) for r in _SIBLINGS.get(_sig(row["check"]), ())
              if r["index"] != row["index"]}
    for k in cands:
        if k.is_user_modified and hotkey_rows.event_key(item_event(k)) not in others:
            return km, k
    return km, None


def editable_item(context, row):
    km, kmi = find_item(context, row)
    if kmi is None or not _is_addon_item(context, km.name, kmi):
        return km, None
    return km, kmi


def kit_text(context, row):
    """The list's Kit Hotkey cell."""
    if not row["editable"]:
        return "—"
    _km, kmi = find_item(context, row)
    if kmi is None:
        return "—"
    text = hotkey_rows.event_text(item_event(kmi))
    return text + " *" if kmi.is_user_modified else text


def conflicts(context, row, event, exclude=None):
    """[(keymap name, operator name)] of active items in the row's Maya context keymaps that already use ``event``."""
    kms = _user_keymaps(context)
    if kms is None:
        return []
    names = list(mapping.CONTEXT_KEYMAPS.get(row["context"], ()))
    own = row["check"][0] if row["check"] else None
    if own and own not in names:
        names.insert(0, own)
    if own in MODE_KEYMAPS:     # Object Mode and Mesh never run together: no conflict across modes
        names = [n for n in names if n == own or n not in MODE_KEYMAPS]
    ex = exclude.as_pointer() if exclude is not None else 0
    items = []
    for name in names:
        km = kms.get(name)
        if km is None:
            continue
        items.extend((name, k.name or k.idname, item_event(k)) for k in km.keymap_items
                     if k.active and k.as_pointer() != ex and k.map_type in {'KEYBOARD', 'MOUSE', 'NDOF', 'TEXTINPUT'})
    return hotkey_rows.conflicts(items, dict(event, value=event.get("value", "PRESS")))


def assign(context, row, event):
    """Bind ``row``'s kit item to ``event`` (type + modifiers) in the user keyconfig. Returns (ok, conflicts)."""
    km, kmi = editable_item(context, row)
    if kmi is None:
        return False, []
    clash = conflicts(context, row, dict(event, value=kmi.value), exclude=kmi)
    kmi.type = event["type"]
    for m in hotkey_rows.MODIFIERS:
        setattr(kmi, m, bool(event.get(m)))
    context.window_manager.keyconfigs.update()
    return True, clash


def restore(context, row):
    """Give ``row``'s kit item its Maya key back (Blender's Restore Item). True if something was restored."""
    km, kmi = editable_item(context, row)
    if kmi is None or not kmi.is_user_modified:
        return False
    km.restore_item_to_default(kmi)
    context.window_manager.keyconfigs.update()
    return True


def changed_rows(context):
    out = []
    for row in rows():
        if row["editable"]:
            _km, kmi = editable_item(context, row)
            if kmi is not None and kmi.is_user_modified:
                out.append(row)
    return out


def restore_all(context):
    """Restore every changed kit item (other user edits of those keymaps stay). Returns how many."""
    items = {}
    for row in rows():
        if row["editable"]:
            km, kmi = editable_item(context, row)
            if kmi is not None and kmi.is_user_modified:
                items[kmi.as_pointer()] = (km, kmi)      # rows of several Maya contexts can share one item
    items = list(items.values())
    for km, kmi in items:
        km.restore_item_to_default(kmi)
    if items:
        context.window_manager.keyconfigs.update()
    return len(items)


# --- the list ---------------------------------------------------------------------------------------------------

class ALLSET_PG_hotkey_row(bpy.types.PropertyGroup):
    index: IntProperty(translation_context='MWK:ui/hotkey_editor.py:257')            # hotkey_data index
    command: StringProperty(translation_context='MWK:ui/hotkey_editor.py:258')
    maya_key: StringProperty(translation_context='MWK:ui/hotkey_editor.py:259')
    kit_key: StringProperty(translation_context='MWK:ui/hotkey_editor.py:260')
    status: StringProperty(translation_context='MWK:ui/hotkey_editor.py:261')
    editable: BoolProperty(translation_context='MWK:ui/hotkey_editor.py:262')


def _wm(context):
    return context.window_manager


def live_events(context, row):
    _km, kmi = find_item(context, row) if row["editable"] else (None, None)
    return [item_event(kmi)] if kmi is not None else []


def refresh(context):
    """Rebuild the shown rows from the search text, search mode and category (keeps the selected command)."""
    wm = _wm(context)
    coll = wm.allset_hk_rows
    keep = coll[wm.allset_hk_active].index if 0 <= wm.allset_hk_active < len(coll) else -1
    text, by = wm.allset_hk_search, wm.allset_hk_by
    live = {}
    if by == "HOTKEY" and text.strip():
        live = {r["index"]: live_events(context, r) for r in rows() if r["editable"]}
    shown = hotkey_rows.search(rows(), text, by, wm.allset_hk_category, live)
    coll.clear()
    active = 0
    for i, r in enumerate(shown):
        item = coll.add()
        item.index, item.command, item.maya_key = r["index"], r["command"] or "(none)", r["maya_key"]
        item.kit_key, item.status, item.editable = kit_text(context, r), r["status_text"], r["editable"]
        if r["index"] == keep:
            active = i
    wm.allset_hk_active = active if shown else -1
    marked_window.redraw(context, KIND)


def _refresh_update(self, context):
    refresh(context)


def selected_row(context):
    wm = _wm(context)
    coll = wm.allset_hk_rows
    if 0 <= wm.allset_hk_active < len(coll):
        return row_of(coll[wm.allset_hk_active].index)
    return None


class ALLSET_UL_hotkeys(bpy.types.UIList):
    """Maya's Hotkey Editor list: command, Maya key, the kit's key, status"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        cells = _columns(layout)
        cells[0].label(text=_zh(item.command, 'MWK:ui/hotkey_editor.py:313'))
        cells[1].label(text=_zh(item.maya_key, 'MWK:ui/hotkey_editor.py:314'))
        cells[2].label(text=_zh(item.kit_key, 'MWK:ui/hotkey_editor.py:315'))
        cells[3].label(text=_zh(item.status, 'MWK:ui/hotkey_editor.py:316'))

    def filter_items(self, context, data, propname):
        return [], []      # the collection is already filtered (refresh)


def _columns(layout):
    out, rest = [], layout
    for _name, factor in COLUMNS[:-1]:
        split = rest.split(factor=factor / max(1e-6, 1.0 - sum(f for _n, f in COLUMNS[:len(out)])))
        out.append(split.row())
        rest = split
    out.append(rest.row())
    return out


# --- operators --------------------------------------------------------------------------------------------------

class ALLSET_OT_hotkey_editor(bpy.types.Operator):
    """Open the Hotkey Editor: Maya's hotkeys, the kit's keys for them, search and assign new keys"""
    bl_translation_context = 'MWK:ui/hotkey_editor.py:337'
    bl_idname = "allset.hotkey_editor"
    bl_label = _zh_native("Hotkey Editor", 'MWK:ui/hotkey_editor.py:337')
    bl_description = _zh_native("Open the Hotkey Editor: Maya's hotkeys, the kit's keys for them, search and assign new keys", 'MWK:ui/hotkey_editor.py:337')

    def execute(self, context):
        if context.window is None:
            return {'CANCELLED'}
        refresh(context)
        if marked_window.open_window(context, KIND) is None:
            self.report({'ERROR'}, _zh("Could not open the Hotkey Editor window", 'MWK:ui/hotkey_editor.py:344'))
            return {'CANCELLED'}
        return {'FINISHED'}


class ALLSET_OT_hotkey_assign(bpy.types.Operator):
    """Assign a new key to this command: press the key (with Ctrl / Alt / Shift), Esc cancels"""
    bl_translation_context = 'MWK:ui/hotkey_editor.py:352'
    bl_idname = "allset.hotkey_assign"
    bl_label = _zh_native("Assign New Hotkey", 'MWK:ui/hotkey_editor.py:352')
    bl_description = _zh_native('Assign a new key to this command: press the key (with Ctrl / Alt / Shift), Esc cancels', 'MWK:ui/hotkey_editor.py:352')
    bl_options = {'INTERNAL'}

    row: IntProperty(default=-1, options={'SKIP_SAVE'}, translation_context='MWK:ui/hotkey_editor.py:355')
    key: StringProperty(options={'SKIP_SAVE'}, translation_context='MWK:ui/hotkey_editor.py:356')        # event type; empty = capture the next key press
    ctrl: BoolProperty(options={'SKIP_SAVE'}, translation_context='MWK:ui/hotkey_editor.py:357')
    alt: BoolProperty(options={'SKIP_SAVE'}, translation_context='MWK:ui/hotkey_editor.py:358')
    shift: BoolProperty(options={'SKIP_SAVE'}, translation_context='MWK:ui/hotkey_editor.py:359')
    oskey: BoolProperty(options={'SKIP_SAVE'}, translation_context='MWK:ui/hotkey_editor.py:360')

    def _row(self, context):
        return row_of(self.row) if self.row >= 0 else selected_row(context)

    def execute(self, context):
        row = self._row(context)
        if row is None or not self.key:
            return {'CANCELLED'}
        event = {"type": self.key, "ctrl": self.ctrl, "alt": self.alt, "shift": self.shift, "oskey": self.oskey}
        ok, clash = assign(context, row, event)
        if not ok:
            self.report({'WARNING'}, _zh(f"{row['command'] or row['maya_key']}: not a kit key binding, can't be changed", 'MWK:ui/hotkey_editor.py:372'))
            return {'CANCELLED'}
        refresh(context)
        text = hotkey_rows.event_text(event)
        if clash:
            self.report({'WARNING'}, _zh(f"{text} is also used by " + ", ".join(f"{n} ({km})" for km, n in clash[:3]), 'MWK:ui/hotkey_editor.py:377'))
        else:
            from .. import results
            results.result(self, _zh(f"{row['command']}: {text}", 'MWK:ui/hotkey_editor.py:380'))
        return {'FINISHED'}

    def invoke(self, context, event):
        if self.key:
            return self.execute(context)
        row = self._row(context)
        if row is None or editable_item(context, row)[1] is None:
            self.report({'WARNING'}, _zh("Pick a command the kit binds (status Kit / Blender (IC))", 'MWK:ui/hotkey_editor.py:388'))
            return {'CANCELLED'}
        self.row = row["index"]
        _wm(context).allset_hk_capture = True
        marked_window.redraw(context, KIND)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _end(self, context):
        _wm(context).allset_hk_capture = False
        marked_window.redraw(context, KIND)

    def modal(self, context, event):
        etype = event.type
        if etype in _IGNORE or event.value != 'PRESS':
            return {'RUNNING_MODAL'}
        if etype in _CANCEL:
            self._end(context)
            return {'CANCELLED'}
        if etype not in hotkey_rows.KEYBOARD:
            return {'RUNNING_MODAL'}
        self.key = etype
        self.ctrl, self.alt, self.shift, self.oskey = event.ctrl, event.alt, event.shift, event.oskey
        self._end(context)
        return self.execute(context)


class ALLSET_OT_hotkey_restore(bpy.types.Operator):
    """Give this command its Maya hotkey back"""
    bl_translation_context = 'MWK:ui/hotkey_editor.py:418'
    bl_idname = "allset.hotkey_restore"
    bl_label = _zh_native("Restore", 'MWK:ui/hotkey_editor.py:418')
    bl_description = _zh_native('Give this command its Maya hotkey back', 'MWK:ui/hotkey_editor.py:418')
    bl_options = {'INTERNAL'}

    row: IntProperty(default=-1, options={'SKIP_SAVE'}, translation_context='MWK:ui/hotkey_editor.py:421')
    all: BoolProperty(name=_zh_native("All", 'MWK:ui/hotkey_editor.py:422'), options={'SKIP_SAVE'}, translation_context='MWK:ui/hotkey_editor.py:422')

    def execute(self, context):
        from .. import results
        if self.all:
            n = restore_all(context)
            refresh(context)
            results.result(self, _zh(f"Restored {n} Maya hotkey(s)", 'MWK:ui/hotkey_editor.py:429'))
            return {'FINISHED'}
        row = row_of(self.row) if self.row >= 0 else selected_row(context)
        if row is None or not restore(context, row):
            return {'CANCELLED'}
        refresh(context)
        results.result(self, _zh(f"{row['command']}: {row['maya_key']}", 'MWK:ui/hotkey_editor.py:435'))
        return {'FINISHED'}


class ALLSET_OT_hotkey_blender_prefs(bpy.types.Operator):
    """Open Blender's Preferences > Keymap (every Blender and add-on key)"""
    bl_translation_context = 'MWK:ui/hotkey_editor.py:442'
    bl_idname = "allset.hotkey_blender_prefs"
    bl_label = _zh_native("Blender Keymap Preferences", 'MWK:ui/hotkey_editor.py:442')
    bl_description = _zh_native("Open Blender's Preferences > Keymap (every Blender and add-on key)", 'MWK:ui/hotkey_editor.py:442')
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return bpy.ops.screen.userpref_show('INVOKE_DEFAULT', section='KEYMAP')


# --- the window -------------------------------------------------------------------------------------------------

def _details(layout, context, row):
    box = layout.box()
    col = box.column(align=True)
    col.label(text=_zh(f"{row['command'] or '(no command)'}" + (f"  /  {row['release']} (release)" if row["release"]
                                                               else ""), 'MWK:ui/hotkey_editor.py:454'))
    col.label(text=_zh(f"Maya hotkey: {row['maya_key']}    Context: {row['context']}"
                   + (f"    Category: {row['category']}" if row["category"] else ""), 'MWK:ui/hotkey_editor.py:456'))
    if row["check"]:
        km_name, idname, props = row["check"]
        args = ", ".join(f"{k}={v!r}" for k, v in props.items())
        col.label(text=_zh(f"Kit: {idname}" + (f"({args})" if args else "") + f"  in  {km_name}", 'MWK:ui/hotkey_editor.py:461'))
    else:
        col.label(text=_zh(f"Kit: {row['status_text']}" + (f" (step {row['step']})" if row["step"] else ""), 'MWK:ui/hotkey_editor.py:463'))
    if row["note"] and row["note"].isascii():     # mapping.py notes are partly Korean dev notes: not shown
        col.label(text=_zh(row["note"], 'MWK:ui/hotkey_editor.py:465'))
    if not row["editable"]:
        return
    km, kmi = editable_item(context, row)
    if kmi is None:
        box.label(text=_zh("Kit hotkey: — (Maya mode off or the item was removed)", 'MWK:ui/hotkey_editor.py:470'), icon='INFO')
        return
    ev = item_event(kmi)
    line = box.row(align=True)
    line.label(text=_zh(f"Kit hotkey: {hotkey_rows.event_text(ev)}" + ("  (changed)" if kmi.is_user_modified else ""), 'MWK:ui/hotkey_editor.py:474'))
    act = line.row(align=True)
    if _wm(context).allset_hk_capture:
        act.alert = True
        act.label(text=_zh("Press a key... (Esc cancels)", 'MWK:ui/hotkey_editor.py:478'))
    else:
        act.operator(ALLSET_OT_hotkey_assign.bl_idname, text=_zh("Assign New Hotkey...", 'MWK:ui/hotkey_editor.py:480')).row = row["index"]
    sub = act.row(align=True)
    sub.enabled = kmi.is_user_modified
    sub.operator(ALLSET_OT_hotkey_restore.bl_idname, text=_zh("Restore", 'MWK:ui/hotkey_editor.py:483')).row = row["index"]
    clash = conflicts(context, row, ev, exclude=kmi)
    if clash:
        box.label(text=_zh("Also used by: " + ", ".join(f"{n} ({k})" for k, n in clash[:3]), 'MWK:ui/hotkey_editor.py:486'), icon='ERROR')


class ALLSET_PT_hotkey_editor(bpy.types.Panel):
    """Maya's Hotkey Editor (a marked Properties Tool tab in its own window)"""
    bl_translation_context = 'MWK:ui/hotkey_editor.py:494'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = _zh_native("Hotkey Editor", 'MWK:ui/hotkey_editor.py:494')
    bl_options = {'HIDE_HEADER'}
    bl_order = -300

    @classmethod
    def poll(cls, context):
        return marked_window.context_kind(context) == KIND

    def draw(self, context):
        wm = _wm(context)
        layout = self.layout
        top = layout.row(align=True)
        top.label(text=_zh(f"Hotkey Set: {SET_NAME}", 'MWK:ui/hotkey_editor.py:506'))
        top.operator(ALLSET_OT_hotkey_blender_prefs.bl_idname, icon='PREFERENCES')
        search = layout.row(align=True)
        search.prop(wm, "allset_hk_by", text="")
        search.prop(wm, "allset_hk_search", text="", icon='VIEWZOOM')
        search.prop(wm, "allset_hk_category", text="")
        head = _columns(layout.row())
        for cell, (name, _f) in zip(head, COLUMNS):
            cell.label(text=name)
        layout.template_list("ALLSET_UL_hotkeys", "", wm, "allset_hk_rows", wm, "allset_hk_active", rows=9)
        layout.label(text=_zh(f"{len(wm.allset_hk_rows)} of {len(rows())} Maya hotkeys", 'MWK:ui/hotkey_editor.py:516'))
        row = selected_row(context)
        if row is not None:
            _details(layout, context, row)
        layout.label(text=_zh(PERSIST_NOTE, 'MWK:ui/hotkey_editor.py:520'), icon='INFO')
        bottom = layout.row(align=True)
        bottom.operator(ALLSET_OT_hotkey_restore.bl_idname, text=_zh("Restore All Maya Hotkeys", 'MWK:ui/hotkey_editor.py:522')).all = True
        bottom.operator("allset.marked_window_close", text=_zh("Close", 'MWK:ui/hotkey_editor.py:523'))


classes = (ALLSET_PG_hotkey_row, ALLSET_UL_hotkeys, ALLSET_OT_hotkey_editor, ALLSET_OT_hotkey_assign,
           ALLSET_OT_hotkey_restore, ALLSET_OT_hotkey_blender_prefs, ALLSET_PT_hotkey_editor)

_WM_PROPS = ("allset_hk_rows", "allset_hk_active", "allset_hk_search", "allset_hk_by", "allset_hk_category",
             "allset_hk_capture")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.types.WindowManager
    wm.allset_hk_rows = CollectionProperty(type=ALLSET_PG_hotkey_row, translation_context='MWK:ui/hotkey_editor.py:537')
    wm.allset_hk_active = IntProperty(name=_zh_native("Hotkey", 'MWK:ui/hotkey_editor.py:538'), default=-1, translation_context='MWK:ui/hotkey_editor.py:538')
    wm.allset_hk_search = StringProperty(name=_zh_native("Search", 'MWK:ui/hotkey_editor.py:539'), update=_refresh_update, options={'TEXTEDIT_UPDATE'},
                                         description=_zh_native("Search the Maya hotkeys by command name or by hotkey", 'MWK:ui/hotkey_editor.py:539'), translation_context='MWK:ui/hotkey_editor.py:539')
    wm.allset_hk_by = EnumProperty(name=_zh_native("Search by", 'MWK:ui/hotkey_editor.py:541'), update=_refresh_update, default="NAME",
                                   items=_zh_enum((("NAME", "Search by Name", "Find commands whose name contains the text"),
                                          ("HOTKEY", "Search by Hotkey", "Find commands bound to a key "
                                                                         "(e.g. Ctrl+Z, Shift+Q, F8)")), 'MWK:ui/hotkey_editor.py:541'), translation_context='MWK:ui/hotkey_editor.py:541')
    wm.allset_hk_category = EnumProperty(name=_zh_native("Category", 'MWK:ui/hotkey_editor.py:545'), items=_zh_enum(category_items, 'MWK:ui/hotkey_editor.py:545'), update=_refresh_update, translation_context='MWK:ui/hotkey_editor.py:545')
    wm.allset_hk_capture = BoolProperty(name=_zh_native("Capturing a Key", 'MWK:ui/hotkey_editor.py:546'), translation_context='MWK:ui/hotkey_editor.py:546')


def unregister():
    for name in _WM_PROPS:
        if hasattr(bpy.types.WindowManager, name):
            delattr(bpy.types.WindowManager, name)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

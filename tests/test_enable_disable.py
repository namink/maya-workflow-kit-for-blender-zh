"""Enabling then disabling the extension leaves Blender exactly as it was."""

import bpy

import kit

AUTO_ENABLE = False  # this test drives enable/disable itself


def test_enable_registers_preferences():
    assert not kit.is_enabled()
    kit.enable()
    try:
        prefs = bpy.context.preferences.addons[kit.MODULE].preferences
        assert prefs is not None, "AddonPreferences not registered"
        assert type(prefs).bl_idname == kit.MODULE, type(prefs).bl_idname
    finally:
        kit.disable()


def test_disable_restores_baseline():
    before = kit.snapshot()
    kit.enable()
    kit.disable()
    after = kit.snapshot()
    d = kit.diff(before, after)
    assert not d, "state leaked after disable:\n" + "\n".join(d)


def test_enable_disable_cycles():
    before = kit.snapshot()
    for _ in range(3):
        kit.enable()
        kit.disable()
    d = kit.diff(before, kit.snapshot())
    assert not d, "state leaked after 3 cycles:\n" + "\n".join(d)


def test_snapshot_detects_leaks():
    """Guard against a vacuous pass: a leaked prop, keymap item and handler must show up."""
    before = kit.snapshot()

    def _leak_handler(*_):
        pass

    bpy.types.Scene.allset_leak = bpy.props.IntProperty()
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    kmi = km.keymap_items.new("view3d.view_all", "F13", "PRESS")
    bpy.app.handlers.load_post.append(_leak_handler)
    try:
        d = "\n".join(kit.diff(before, kit.snapshot()))
        for needle in ("allset_leak", "F13", "_leak_handler"):
            assert needle in d, f"snapshot missed {needle}:\n{d}"
    finally:
        del bpy.types.Scene.allset_leak
        km.keymap_items.remove(kmi)
        bpy.app.handlers.load_post.remove(_leak_handler)

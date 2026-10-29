"""Run in a factory-startup Blender with an isolated user environment."""
import sys
from pathlib import Path
import bpy
import addon_utils

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src'))
bpy.context.preferences.view.language = 'zh_HANS'
bpy.context.preferences.view.use_translate_interface = True
addon_utils.enable('allset', default_set=True)
import allset
from allset.i18n import tr, enum_items
assert tr('Channel Box') == '通道盒'
assert tr('Set Driven Key') == '设置驱动关键帧'
# RNA stores canonical English strings; Blender translates them when drawn.
assert enum_items([('WORLD', 'World', '', 7)])[0] == ('WORLD', 'World', '', 7)
from allset.ui import menu_data
assert 'mainMeshMenu' in menu_data.MENUS
assert menu_data.MENUS['mainMeshMenu'][0] == 'Mesh'
from allset import switch
switch.register_mode()
switch._registered[0] = True
assert bpy.ops.allset.create(kind='CUBE') == {'FINISHED'}
obj = bpy.context.object
assert obj.name.startswith('pCube'), obj.name
assert tr('Freeze Transformations') == '冻结变换'
print('CHINESE_SMOKE_PASS', bpy.app.version_string, obj.name, flush=True)
bpy.context.preferences.view.language = 'en_US'
assert tr('Channel Box') == 'Channel Box'
assert tr('Set Driven Key') == 'Set Driven Key'
print('ENGLISH_SWITCH_PASS', flush=True)
addon_utils.disable('allset', default_set=True)
print('REGISTER_UNREGISTER_PASS', flush=True)

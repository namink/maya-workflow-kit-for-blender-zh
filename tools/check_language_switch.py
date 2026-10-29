"""Language and registration integration checks in a disposable factory Blender.

Run only through run_language_switch_checks.py, which supplies isolated paths.
This test deliberately switches the SAME text repeatedly without clearing a
translation cache. Static RNA strings must remain English in both languages.
"""
import argparse
import importlib
import json
import re
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

import addon_utils
import bpy

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--initial-language', default='en_US')
parser.add_argument('--report', required=True)
parser.add_argument('--module', default='allset')
parser.add_argument('--package-focus', action='store_true')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
MODULE = args.module
if MODULE == 'allset':
    sys.path.insert(0, str(ROOT / 'src'))
report = {'blender': bpy.app.version_string, 'module': MODULE, 'initial_language': args.initial_language, 'tests': []}
view = bpy.context.preferences.view
PROBE_CONTEXT = 'ALLSET_TEST_LANGUAGE_CONTEXT_20261029'
CJK = re.compile('[\u3400-\u9fff]')
probe = None
module = None


def language(name, interface=True):
    view.language = name
    view.use_translate_interface = interface
    # Keep tooltip translation on while checking the interface toggle, so the
    # helper cannot accidentally gate on the wrong preference.
    view.use_translate_tooltips = True
    return bpy.app.translations.locale


def check(name, function):
    if args.package_focus and name not in {
            'native_strings_stay_english_before_registration',
            'static_rna_is_english_after_initial_import',
            'native_context_translates_actual_rna_label_property_and_enum',
            'real_preferences_and_channel_menu_native_contexts',
            'same_string_language_cache_round_trip',
            'translation_checkbox_off_and_back_on',
            'real_catalog_conditionals_and_canonical_data',
            'translation_registry_removed_and_rebuilt_over_enable_cycles'}:
        return
    try:
        detail = function()
        report['tests'].append({'name': name, 'ok': True, 'detail': detail})
        print('PASS', name, flush=True)
    except Exception:
        report['tests'].append({'name': name, 'ok': False, 'error': traceback.format_exc()})
        print('FAIL', name, traceback.format_exc(), flush=True)


def equal(actual, expected):
    assert actual == expected, f'{actual!r} != {expected!r}'


def enable_addon():
    def raise_error(error):
        raise error
    result = addon_utils.enable(MODULE, default_set=True, handle_error=raise_error)
    assert result is not None and MODULE in bpy.context.preferences.addons
    return result


def chinese(value):
    assert CJK.search(value), f'Expected Chinese display text, got {value!r}'
    return value


def raw_metadata():
    """Inspect the complete registered add-on, including generated menus."""
    classes = {}
    for name, item in tuple(sys.modules.items()):
        if name != MODULE and not name.startswith(MODULE + '.'):
            continue
        if item is None:
            continue
        for value in vars(item).values():
            if isinstance(value, type) and value.__module__.startswith(MODULE) and hasattr(value, 'bl_rna'):
                classes[id(value)] = value
    labels = []
    properties = []
    problems = []
    operator_properties = 0
    for cls in classes.values():
        label = getattr(cls, 'bl_label', None)
        if isinstance(label, str):
            labels.append((cls.__name__, label))
            if CJK.search(label): problems.append(('class', cls.__name__, label))
        description = getattr(cls, 'bl_description', None)
        if isinstance(description, str) and CJK.search(description):
            problems.append(('class description', cls.__name__, description))
        structs = [cls.bl_rna]
        if issubclass(cls, bpy.types.Operator):
            idname = getattr(cls, 'bl_idname', '')
            if '.' in idname:
                category, operation = idname.split('.', 1)
                try:
                    structs.append(getattr(getattr(bpy.ops, category), operation).get_rna_type())
                    operator_properties += 1
                except (AttributeError, RuntimeError):
                    pass
        for prop in (p for struct in structs for p in struct.properties):
            if prop.identifier == 'rna_type': continue
            properties.append((cls.__name__, prop.identifier, prop.name))
            if CJK.search(prop.name): problems.append(('property', cls.__name__, prop.identifier, prop.name))
            if CJK.search(prop.description): problems.append(('property description', cls.__name__, prop.identifier, prop.description))
            if prop.type == 'ENUM':
                for enum_item in prop.enum_items:
                    if CJK.search(enum_item.name):
                        problems.append(('enum', cls.__name__, prop.identifier, enum_item.identifier, enum_item.name))
    assert not problems, f'Chinese baked into static RNA: {problems[:15]!r}'
    assert len(labels) > 100, f'Too few add-on classes inspected: {len(labels)}'
    assert operator_properties > 100, f'Too few OperatorProperties inspected: {operator_properties}'
    return {'classes': len(labels), 'properties': len(properties), 'operator_types': operator_properties}


try:
    language(args.initial_language)
    module = importlib.import_module(MODULE)
    i18n = importlib.import_module(MODULE + '.i18n')
    for required in ('tr', 'native', 'enum_items', 'register', 'unregister'):
        assert callable(getattr(i18n, required, None)), f'Missing public i18n interface: {required}'

    # Mimic an add-on imported while Blender is ALREADY Chinese. Class and
    # property metadata may not become Chinese even in that initial state.
    probe_items = i18n.enum_items([
        ('WORLD', 'World', 'Maya Mode', 61),
        None,
        ('OBJECT', 'Object', 'Object Mode', 62),
    ], PROBE_CONTEXT)
    probe_label = i18n.native('Channel Box', PROBE_CONTEXT)
    probe_property = i18n.native('Channels', PROBE_CONTEXT)
    probe_welcome = i18n.native('Make Blender feel like Maya', PROBE_CONTEXT)
    check('native_strings_stay_english_before_registration', lambda: (
        equal(probe_label, 'Channel Box'), equal(probe_property, 'Channels'),
        equal(probe_welcome, 'Make Blender feel like Maya'),
        equal(probe_items[0][0], 'WORLD'), equal(probe_items[0][1], 'World'),
        equal(probe_items[0][-1], 61), equal(probe_items[1], None)))

    class ALLSET_OT_language_test_probe(bpy.types.Operator):
        bl_idname = 'allset.language_test_probe'
        bl_label = probe_label
        bl_translation_context = PROBE_CONTEXT
        test_choice: bpy.props.EnumProperty(
            name=probe_property, items=probe_items, translation_context=PROBE_CONTEXT)

        def execute(self, context):
            return {'FINISHED'}

    probe = ALLSET_OT_language_test_probe
    enable_addon()
    bpy.utils.register_class(probe)
    module.switch.set_mode(True, layout=False)

    check('static_rna_is_english_after_initial_import', raw_metadata)
    check('probe_property_and_enum_metadata_are_english', lambda: (
        equal(bpy.ops.allset.language_test_probe.get_rna_type().properties['test_choice'].name, 'Channels'),
        equal(bpy.ops.allset.language_test_probe.get_rna_type().properties['test_choice'].enum_items['WORLD'].name, 'World'),
        equal(bpy.ops.allset.language_test_probe.get_rna_type().properties['test_choice'].enum_items['WORLD'].value, 61)))

    def english_draw():
        language('en_US')
        equal(i18n.tr('Channel Box'), 'Channel Box')
        equal(i18n.tr('Set Driven Key'), 'Set Driven Key')
        equal(bpy.app.translations.pgettext_iface('Make Blender feel like Maya', PROBE_CONTEXT),
              'Make Blender feel like Maya')
    check('english_draw_after_initial_import', english_draw)

    def chinese_draw():
        language('zh_HANS')
        equal(i18n.tr('Channel Box'), '通道盒')
        equal(i18n.tr('Set Driven Key'), '设置驱动关键帧')
    check('chinese_draw_after_english_lookup', chinese_draw)

    def chinese_native():
        language('zh_HANS')
        equal(bpy.app.translations.pgettext_iface(probe.bl_label, probe.bl_translation_context), '通道盒')
        prop = bpy.ops.allset.language_test_probe.get_rna_type().properties['test_choice']
        equal(bpy.app.translations.pgettext_iface(prop.name, prop.translation_context), '通道')
        equal(bpy.app.translations.pgettext_iface(prop.enum_items['WORLD'].name, prop.translation_context), '世界')
        chinese(bpy.app.translations.pgettext_iface('Make Blender feel like Maya', PROBE_CONTEXT))
    check('native_context_translates_actual_rna_label_property_and_enum', chinese_native)

    def actual_plugin_metadata_translation():
        language('zh_HANS')
        prefs = module.preferences.ALLSET_AddonPreferences.bl_rna
        mode = prefs.properties['maya_mode']
        equal(mode.name, 'Maya Mode')
        chinese(bpy.app.translations.pgettext_iface(mode.name, mode.translation_context))
        speed = prefs.properties['cb_speed']
        equal(speed.name, 'Slider Speed')
        chinese(bpy.app.translations.pgettext_iface(speed.name, speed.translation_context))
        slow = speed.enum_items['SLOWEST']
        equal(slow.name, 'Slowest')
        chinese(bpy.app.translations.pgettext_iface(slow.name, speed.translation_context))
        channel_box = importlib.import_module(MODULE + '.ui.channel_box')
        menu = channel_box.ALLSET_MT_cb_channels
        equal(menu.bl_label, 'Channels')
        equal(bpy.app.translations.pgettext_iface(menu.bl_label, menu.bl_translation_context), '通道')
    check('real_preferences_and_channel_menu_native_contexts', actual_plugin_metadata_translation)

    def switch_repeatedly():
        for _ in range(3):
            language('en_US')
            equal(i18n.tr('Channel Box'), 'Channel Box')
            language('zh_HANS')
            equal(i18n.tr('Channel Box'), '通道盒')
        language('en_US')
        equal(i18n.tr('Channel Box'), 'Channel Box')
    check('same_string_language_cache_round_trip', switch_repeatedly)

    def interface_disabled():
        language('zh_HANS', interface=False)
        equal(i18n.tr('Channel Box'), 'Channel Box')
        equal(bpy.app.translations.pgettext_iface('Make Blender feel like Maya', PROBE_CONTEXT),
              'Make Blender feel like Maya')
        language('zh_HANS', interface=True)
        equal(i18n.tr('Channel Box'), '通道盒')
    check('translation_checkbox_off_and_back_on', interface_disabled)

    def other_locale_is_not_simplified_chinese():
        language('ja_JP')
        equal(i18n.tr('Channel Box'), 'Channel Box')
        language('en_US')
        equal(i18n.tr('Channel Box'), 'Channel Box')
    check('non_chinese_locale_does_not_get_simplified_chinese', other_locale_is_not_simplified_chinese)

    def template_formatting():
        language('zh_HANS')
        text = i18n.tr('Device aspect ratio: {aspect}')
        assert '{aspect}' in text, text
        chinese(text)
        equal(text.format(aspect='1.777').count('1.777'), 1)
        template = 'Texel density {s.texel_density:.3f} px per unit (map {s.map_size})'
        translated = i18n.tr(template)
        assert '{s.texel_density:.3f}' in translated and '{s.map_size}' in translated, translated
        value = translated.format(s=SimpleNamespace(texel_density=1.23456, map_size=2048))
        assert '1.235' in value and '2048' in value, value
        chinese(value)
        language('en_US')
        equal(i18n.tr(template), template)
    check('format_specifiers_and_placeholders_survive', template_formatting)

    def evaluated_template_and_user_name():
        language('zh_HANS')
        for user_name in ['Channel Box', 'Set Key 左手.001', 'Hero:Root_CTRL']:
            original = f'Created {user_name}'
            translated = i18n.tr(original)
            chinese(translated)
            assert user_name in translated, (original, translated)
        rendered = i18n.tr('Texel density 1.235 px per unit (map 2048)')
        chinese(rendered)
        assert '1.235' in rendered and '2048' in rendered, rendered
        language('en_US')
        equal(i18n.tr('Created Set Key 左手.001'), 'Created Set Key 左手.001')
    check('evaluated_templates_preserve_user_names_and_numeric_values', evaluated_template_and_user_name)

    def real_catalog_conditionals_and_canonical_data():
        language('zh_HANS')
        assert i18n.tr('Added 2 attribute(s)') == '已添加 2 个属性', i18n.tr('Added 2 attribute(s)')
        assert i18n.tr('Deleted 2 materials') == '已删除 2 个材质。', i18n.tr('Deleted 2 materials')
        assert i18n.tr('Local rotation axes on') == '局部旋转轴：已启用', i18n.tr('Local rotation axes on')
        shelf = importlib.import_module(MODULE + '.ui.shelf')
        equal(shelf.display_shelf_label('USER:World', 'World'), 'World')
        equal(shelf.display_shelf_label('USER:Channel Box', 'Channel Box'), 'Channel Box')
        equal(shelf.display_shelf_label('Polygons', 'Polygons'), '多边形')
        menu_data = importlib.import_module(MODULE + '.ui.menu_data')
        menu_map = importlib.import_module(MODULE + '.ui.menu_map')
        equal(menu_data.MENUS['mainMeshMenu'][0], 'Mesh')
        assert 'Edit Mesh/Extrude' in menu_map.MAP
        assert '创建/挤出' not in menu_map.MAP
        enum = module.preferences.ALLSET_AddonPreferences.bl_rna.properties['cb_speed'].enum_items
        equal(enum['SLOWEST'].identifier, 'SLOWEST')
        equal(enum['SLOWEST'].name, 'Slowest')
        # Names are data even if they collide with a known UI caption.
        ob = bpy.data.objects.new('Channel Box', None)
        bpy.context.scene.collection.objects.link(ob)
        language('en_US')
        equal(ob.name, 'Channel Box')
        equal(i18n.tr('Added 2 attribute(s)'), 'Added 2 attribute(s)')
        language('zh_HANS')
        equal(ob.name, 'Channel Box')
        equal(i18n.tr('Created Channel Box'), '已创建 Channel Box。')
        return {'catalog_file': str(Path(module.__file__).with_name('translations_zh_HANS.json'))}
    check('real_catalog_conditionals_and_canonical_data', real_catalog_conditionals_and_canonical_data)

    def create_in_each_language():
        created = []
        for locale in ('en_US', 'zh_HANS'):
            language(locale)
            assert bpy.ops.allset.create(kind='CUBE') == {'FINISHED'}
            ob = bpy.context.object
            assert ob.name.startswith('pCube'), ob.name
            user_name = 'Set Key 左手_' + locale
            ob.name = user_name
            ob['user_note'] = 'Channel Box World Set Key'
            language('zh_HANS' if locale == 'en_US' else 'en_US')
            equal(ob.name, user_name)
            equal(ob['user_note'], 'Channel Box World Set Key')
            created.append(user_name)
        return created
    check('maya_create_operator_and_scene_names_in_both_languages', create_in_each_language)

    check('static_rna_remains_english_after_language_switches', raw_metadata)

    def lifecycle_translation_registry():
        language('zh_HANS')
        chinese(bpy.app.translations.pgettext_iface('Make Blender feel like Maya', PROBE_CONTEXT))
        for _ in range(2):
            addon_utils.disable(MODULE, default_set=True)
            equal(bpy.app.translations.pgettext_iface('Make Blender feel like Maya', PROBE_CONTEXT),
                  'Make Blender feel like Maya')
            enable_addon()
            module.switch.set_mode(True, layout=False)
            chinese(bpy.app.translations.pgettext_iface('Make Blender feel like Maya', PROBE_CONTEXT))
            assert bpy.ops.allset.create(kind='CUBE') == {'FINISHED'}
        addon_utils.disable(MODULE, default_set=True)
        equal(bpy.app.translations.pgettext_iface('Make Blender feel like Maya', PROBE_CONTEXT),
              'Make Blender feel like Maya')
    check('translation_registry_removed_and_rebuilt_over_enable_cycles', lifecycle_translation_registry)
except Exception:
    report['tests'].append({'name': 'setup', 'ok': False, 'error': traceback.format_exc()})
    print(traceback.format_exc(), flush=True)
finally:
    if probe is not None:
        try: bpy.utils.unregister_class(probe)
        except (RuntimeError, ValueError): pass
    try:
        if MODULE in bpy.context.preferences.addons:
            addon_utils.disable(MODULE, default_set=True)
    except Exception:
        report['tests'].append({'name': 'final_cleanup', 'ok': False, 'error': traceback.format_exc()})
    report['passed'] = sum(test['ok'] for test in report['tests'])
    report['failed'] = sum(not test['ok'] for test in report['tests'])
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('LANGUAGE_CHECK_RESULT', report['passed'], 'passed', report['failed'], 'failed', flush=True)
if report['failed']:
    raise SystemExit(1)

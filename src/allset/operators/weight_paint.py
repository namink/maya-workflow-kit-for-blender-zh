# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Paint Skin Weights workspace: native brush tools and configurable weight operations."""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native
from contextlib import contextmanager

import bpy
from bpy.props import (BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, PointerProperty,
                       StringProperty)

from .. import compat
from . import skin

# Each native operation keeps its own settings, including all scalar operator options.
ACTIONS = {
    'SET': ('Set Weight', 'paint.weight_set'),
    'NORMALIZE_ALL': ('Normalize All', 'object.vertex_group_normalize_all'),
    'NORMALIZE': ('Normalize Influence', 'object.vertex_group_normalize'),
    'MIRROR': ('Mirror Weights', 'object.vertex_group_mirror'),
    'INVERT': ('Invert Weights', 'object.vertex_group_invert'),
    'CLEAN': ('Prune Small Weights', 'object.vertex_group_clean'),
    'QUANTIZE': ('Quantize Weights', 'object.vertex_group_quantize'),
    'LEVELS': ('Weight Levels', 'object.vertex_group_levels'),
    'SMOOTH': ('Smooth Weights', 'object.vertex_group_smooth'),
    'LIMIT': ('Limit Influences', 'object.vertex_group_limit_total'),
    'TRANSFER': ('Transfer Weights', 'object.data_transfer'),
    'AUTO': ('Automatic Weights', 'paint.weight_from_bones'),
    'ENVELOPE': ('Bone Envelope Weights', 'paint.weight_from_bones'),
}
SCOPE = [('ACTIVE', 'Active influence', 'Only the active vertex group'),
         ('BONE_SELECT', 'Selected joints', 'Groups belonging to selected pose bones'),
         ('BONE_DEFORM', 'Deform joints', 'All deforming bone groups'),
         ('ALL', 'All groups', 'All vertex groups, including non-joint groups')]
TRANSFER_FIELDS = {'vert_mapping', 'use_create', 'use_object_transform', 'use_auto_transform',
                   'use_max_distance', 'max_distance', 'ray_radius', 'layers_select_src',
                   'layers_select_dst', 'mix_mode', 'mix_factor'}


def native(name):
    module, op = name.split('.')
    return getattr(getattr(bpy.ops, module), op)


def _annotation(prop, action):
    kw = {'name': prop.name, 'description': prop.description}
    if prop.identifier == 'group_select_mode':
        return EnumProperty(**kw, items=_zh_enum(SCOPE[1:] if action in {'NORMALIZE_ALL', 'LIMIT'} else SCOPE, 'MWK:operators/weight_paint.py:47'),
                            default='BONE_DEFORM' if action in {'NORMALIZE_ALL', 'LIMIT'} else 'ACTIVE', translation_context='MWK:operators/weight_paint.py:47')
    if prop.type == 'BOOLEAN':
        return BoolProperty(**kw, default=prop.default, translation_context='MWK:operators/weight_paint.py:50')
    if prop.type in {'INT', 'FLOAT'} and not prop.is_array:
        kw.update(default=prop.default, min=prop.hard_min, max=prop.hard_max)
        return (IntProperty if prop.type == 'INT' else FloatProperty)(**kw)
    if prop.type == 'ENUM':
        items = [(e.identifier, e.name, e.description) for e in prop.enum_items if e.identifier]
        if items and not prop.is_enum_flag:
            return EnumProperty(**kw, items=_zh_enum(items, 'MWK:operators/weight_paint.py:57'), default=prop.default, translation_context='MWK:operators/weight_paint.py:57')
    return None


_SETTING_CLASSES = []
_FIELDS = {}
for _key, (_label, _op) in ACTIONS.items():
    _ann = {}
    for _p in native(_op).get_rna_type().properties:
        if _p.identifier == 'rna_type' or (_key == 'TRANSFER' and _p.identifier not in TRANSFER_FIELDS):
            continue
        _a = _annotation(_p, _key)
        if _a is not None:
            _ann[_p.identifier] = _a
    if _key == 'TRANSFER':
        _ann['source'] = PointerProperty(name=_zh_native('Source mesh', 'MWK:operators/weight_paint.py:72'), type=bpy.types.Object,
                                        poll=lambda self, ob: ob.type == 'MESH', translation_context='MWK:operators/weight_paint.py:72')
    _FIELDS[_key] = tuple(_ann)
    _SETTING_CLASSES.append(type('ALLSET_PG_weight_' + _key.lower(), (bpy.types.PropertyGroup,),
                                {'__annotations__': _ann, '__module__': __name__}))


def _normalize_get(self):
    return bpy.context.tool_settings.use_auto_normalize


def _normalize_set(self, value):
    bpy.context.tool_settings.use_auto_normalize = value
    mesh = bpy.context.active_object
    if mesh is not None and mesh.type == 'MESH':
        mesh[skin.NORMALIZE_PROP] = 'INTERACTIVE' if value else 'NONE'


def _normalize_mode_get(self):
    mesh = bpy.context.active_object
    ids = [k for k, _l, _d in skin.NORMALIZE]
    if mesh is not None and mesh.type == 'MESH' and mesh.get(skin.NORMALIZE_PROP) in ids:
        if mesh[skin.NORMALIZE_PROP] != 'INTERACTIVE' or bpy.context.tool_settings.use_auto_normalize:
            return ids.index(mesh[skin.NORMALIZE_PROP])
    return ids.index('INTERACTIVE' if bpy.context.tool_settings.use_auto_normalize else 'NONE')


def _normalize_mode_set(self, value):
    """Maya Normalize Weights Off / Interactive / Post: Interactive = Blender Auto Normalize; Post = weights left as
    painted and normalised by the deformation (Blender's Armature modifier divides by the weight sum)."""
    key = skin.NORMALIZE[value][0]
    bpy.context.tool_settings.use_auto_normalize = key == 'INTERACTIVE'
    mesh = bpy.context.active_object
    if mesh is not None and mesh.type == 'MESH':
        mesh[skin.NORMALIZE_PROP] = key


def _numbers_update(self, context):
    for area in context.screen.areas if context.screen else ():
        if area.type == 'VIEW_3D':
            area.tag_redraw()


class ALLSET_PG_weight_workspace(bpy.types.PropertyGroup):
    search: StringProperty(name=_zh_native('Find influence', 'MWK:operators/weight_paint.py:116'), options={'TEXTEDIT_UPDATE'}, translation_context='MWK:operators/weight_paint.py:116')
    # Maya 2026 Sort: Alphabetically (natural order) / By Hierarchy (default) / Flat
    sort: EnumProperty(name=_zh_native('Sort', 'MWK:operators/weight_paint.py:118'), items=_zh_enum([('NAME', 'Alphabetically', 'Natural name order (joint2 before joint10)'),
                                         ('HIERARCHY', 'By Hierarchy', 'Joint hierarchy order'),
                                         ('INDEX', 'Flat', 'Influence order, no hierarchy')], 'MWK:operators/weight_paint.py:118'), default='HIERARCHY', translation_context='MWK:operators/weight_paint.py:118')
    paint_tool: StringProperty(default='', options={'HIDDEN'}, translation_context='MWK:operators/weight_paint.py:121')
    show_all: BoolProperty(name=_zh_native('Include non-joint groups', 'MWK:operators/weight_paint.py:122'), default=False, translation_context='MWK:operators/weight_paint.py:122')
    locked_only: BoolProperty(name=_zh_native('Locked influences only', 'MWK:operators/weight_paint.py:123'), default=False, translation_context='MWK:operators/weight_paint.py:123')
    auto_normalize: BoolProperty(name=_zh_native('Auto normalize', 'MWK:operators/weight_paint.py:124'),
                                 description=_zh_native('Keep deform weights normalized while painting; remembered for this skin', 'MWK:operators/weight_paint.py:124'),
                                 get=_normalize_get, set=_normalize_set, translation_context='MWK:operators/weight_paint.py:124')
    # Tool Settings frames in Maya 2024+ order (Skin Clusters / Influences / Brush / Visualization / Stroke /
    # Stylus Pressure / Display), then the Blender-only extras (ui/paint_weights.SECTIONS)
    # Maya 2026 frame defaults: Skin Clusters collapsed (skinCtxClustersCollapsed 1), Influences / Brush /
    # Visualization open, Stroke / Stylus Pressure / Display collapsed
    show_skin_clusters: BoolProperty(default=False, translation_context='MWK:operators/weight_paint.py:131')
    show_influences: BoolProperty(default=True, translation_context='MWK:operators/weight_paint.py:132')
    show_brush: BoolProperty(default=True, translation_context='MWK:operators/weight_paint.py:133')
    show_visualization: BoolProperty(default=True, translation_context='MWK:operators/weight_paint.py:134')
    show_stroke: BoolProperty(default=False, translation_context='MWK:operators/weight_paint.py:135')
    show_pressure: BoolProperty(default=False, translation_context='MWK:operators/weight_paint.py:136')
    show_display: BoolProperty(default=False, translation_context='MWK:operators/weight_paint.py:137')
    show_commands: BoolProperty(default=False, translation_context='MWK:operators/weight_paint.py:138')
    show_mask: BoolProperty(default=False, translation_context='MWK:operators/weight_paint.py:139')
    status: StringProperty(default='', translation_context='MWK:operators/weight_paint.py:140')
    # step 224: Maya 2026 fields the kit keeps itself (ctx_defaults)
    skin_cluster: IntProperty(name=_zh_native('Skin Cluster', 'MWK:operators/weight_paint.py:142'), default=0, min=0,
                              description=_zh_native('The skin cluster (Armature modifier) whose influences the list shows', 'MWK:operators/weight_paint.py:142'), translation_context='MWK:operators/weight_paint.py:142')
    normalize_mode: EnumProperty(name=_zh_native('Normalize Weights', 'MWK:operators/weight_paint.py:144'), items=_zh_enum(skin.NORMALIZE, 'MWK:operators/weight_paint.py:144'), get=_normalize_mode_get,
                                 set=_normalize_mode_set, translation_context='MWK:operators/weight_paint.py:144')
    weight_type: EnumProperty(name=_zh_native('Weight Type', 'MWK:operators/weight_paint.py:146'), items=_zh_enum([('SKIN', 'Skin Weight', 'Paint the skin weights'),
                                                        ('DQ', 'DQ Blend Weight', 'Blender has no per-vertex dual '
                                                         'quaternion blend weight')], 'MWK:operators/weight_paint.py:146'), default='SKIN', translation_context='MWK:operators/weight_paint.py:146')
    min_value: FloatProperty(name=_zh_native('Min', 'MWK:operators/weight_paint.py:149'), default=0.0, min=0.0, max=1.0, description=_zh_native('Lowest weight Flood writes', 'MWK:operators/weight_paint.py:149'), translation_context='MWK:operators/weight_paint.py:149')
    max_value: FloatProperty(name=_zh_native('Max', 'MWK:operators/weight_paint.py:150'), default=1.0, min=0.0, max=1.0, description=_zh_native('Highest weight Flood writes', 'MWK:operators/weight_paint.py:150'), translation_context='MWK:operators/weight_paint.py:150')
    show_numbers: BoolProperty(name=_zh_native('Show Numbers', 'MWK:operators/weight_paint.py:151'), default=False, update=_numbers_update,
                               description=_zh_native("Draw the painted influence's weight at every vertex", 'MWK:operators/weight_paint.py:151'), translation_context='MWK:operators/weight_paint.py:151')
    number_places: IntProperty(name=_zh_native('Decimal Places', 'MWK:operators/weight_paint.py:153'), default=2, min=1, max=4, translation_context='MWK:operators/weight_paint.py:153')
    number_color: FloatVectorProperty(name=_zh_native('Number Color', 'MWK:operators/weight_paint.py:154'), subtype='COLOR', size=3, min=0.0, max=1.0,
                                      default=(1.0, 1.0, 0.0), translation_context='MWK:operators/weight_paint.py:154')
    number_color_ramp: BoolProperty(name=_zh_native('Color Ramp', 'MWK:operators/weight_paint.py:156'), default=False,
                                    description=_zh_native('Colour the numbers by weight (0 = Min color, 1 = Max color)', 'MWK:operators/weight_paint.py:156'), translation_context='MWK:operators/weight_paint.py:156')
    number_min_color: FloatVectorProperty(name=_zh_native('Weight 0', 'MWK:operators/weight_paint.py:158'), subtype='COLOR', size=3, min=0.0, max=1.0,
                                          default=(1.0, 1.0, 1.0), translation_context='MWK:operators/weight_paint.py:158')
    number_max_color: FloatVectorProperty(name=_zh_native('Weight 1', 'MWK:operators/weight_paint.py:160'), subtype='COLOR', size=3, min=0.0, max=1.0,
                                          default=(0.0, 0.0, 0.0), translation_context='MWK:operators/weight_paint.py:160')


# One settings group per Paint Weights action (above). Python 3.14 has no ``__annotations__`` name in a class body to
# update (PEP 649; Issue #176: "name '__annotations__' is not defined" on CachyOS right after install), so they are
# merged in after the class body, before registration.
ALLSET_PG_weight_workspace.__annotations__ = {
    **compat.own_annotations(ALLSET_PG_weight_workspace),
    **{key.lower(): PointerProperty(type=cls, translation_context='MWK:operators/weight_paint.py:169') for key, cls in zip(ACTIONS, _SETTING_CLASSES)}}


def state(context):
    return context.window_manager.allset_weight_workspace


def active(context):
    ob = context.active_object
    return context.mode == 'PAINT_WEIGHT' and ob is not None and ob.type == 'MESH'


@contextmanager
def viewport(context):
    from ..ui.status_line import main_view3d
    area, region = main_view3d(context.screen)
    if area is None or region is None:
        raise RuntimeError('Open a 3D View to paint skin weights')
    with context.temp_override(window=context.window, area=area, region=region):
        yield bpy.context


def brush_kind(brush):
    return getattr(brush, 'weight_brush_type', getattr(brush, 'weight_tool', 'DRAW')) if brush else ''


def brush_tool(context, kind):
    from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as tools
    ids = [t.idname for entry in tools.tools_from_context(context)
           for t in (entry if type(entry) is tuple else (entry,)) if t is not None]
    suffix = {'BLUR': 'blur', 'AVERAGE': 'average', 'SMEAR': 'smear'}.get(kind)
    return next((name for name in ids if suffix and name.lower() == 'builtin_brush.' + suffix), 'builtin.brush')


def activate_brush(context, kind='DRAW', blend=None):
    with viewport(context) as ctx:
        bpy.ops.wm.tool_set_by_id(name=brush_tool(ctx, kind))
        brush = ctx.tool_settings.weight_paint.brush
        if brush is None or brush_kind(brush) != kind:
            asset = {'DRAW': 'Paint', 'BLUR': 'Blur', 'AVERAGE': 'Average', 'SMEAR': 'Smear'}[kind]
            bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',
                relative_asset_identifier='brushes/essentials_brushes-mesh_weight.blend/Brush/' + asset)
            brush = ctx.tool_settings.weight_paint.brush
        if brush is None or brush_kind(brush) != kind:
            raise RuntimeError('Choose a compatible weight brush from Brush Assets')
        if blend is not None and not skin._brush_set(brush, 'blend', blend):
            raise RuntimeError('This brush is read-only; make an editable copy from Brush Assets')
        return brush


class ALLSET_OT_weight_tool(bpy.types.Operator):
    bl_translation_context = 'MWK:operators/weight_paint.py:221'
    bl_idname = 'allset.weight_tool'
    bl_label = _zh_native('Weight Paint Tool', 'MWK:operators/weight_paint.py:221')
    bl_options = {'REGISTER', 'UNDO'}
    kind: StringProperty(default='DRAW', translation_context='MWK:operators/weight_paint.py:223')
    blend: StringProperty(default='', translation_context='MWK:operators/weight_paint.py:224')

    @classmethod
    def description(cls, context, properties):
        return _zh({'ASSETS': 'Browse Blender weight-paint brush assets',
                'DRAW': 'Paint weights with the chosen blend operation',
                'BLUR': 'Smooth weights across neighboring vertices',
                'AVERAGE': 'Paint the average weight under the brush',
                'SMEAR': 'Drag weights along the direction of your stroke',
                'LINEAR': 'Drag in the viewport to paint a linear weight gradient',
                'RADIAL': 'Drag in the viewport to paint a radial weight gradient',
                'SAMPLE': 'Click the mesh to sample its weight into Value',
                'SAMPLE_GROUP': 'Click the mesh to choose an influence under the cursor'}.get(properties.kind, 'Weight Paint Tool'), 'MWK:operators/weight_paint.py:228')

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        try:
            if self.kind == 'ASSETS':
                with viewport(context):
                    bpy.ops.wm.call_asset_shelf_popover('INVOKE_DEFAULT', name='VIEW3D_AST_brush_weight_paint')
            elif self.kind in {'DRAW', 'BLUR', 'AVERAGE', 'SMEAR'}:
                activate_brush(context, self.kind, self.blend or None)
            else:
                tool = {'LINEAR': 'builtin.gradient', 'RADIAL': 'builtin.gradient',
                        'SAMPLE': 'builtin.sample_weight', 'SAMPLE_GROUP': 'builtin.sample_vertex_group'}[self.kind]
                with viewport(context) as ctx:
                    bpy.ops.wm.tool_set_by_id(name=tool)
                    if self.kind in {'LINEAR', 'RADIAL'}:
                        current = ctx.workspace.tools.from_space_view3d_mode('PAINT_WEIGHT', create=False)
                        current.operator_properties('paint.weight_gradient').type = self.kind
            state(context).status = ''
            return {'FINISHED'}
        except (RuntimeError, TypeError, ValueError, KeyError) as ex:
            self.report({'WARNING'}, _zh(str(ex), 'MWK:operators/weight_paint.py:260'))
            return {'CANCELLED'}


class ALLSET_OT_weight_value(bpy.types.Operator):
    bl_translation_context = 'MWK:operators/weight_paint.py:266'
    bl_idname = 'allset.weight_value'
    bl_label = _zh_native('Set Paint Value', 'MWK:operators/weight_paint.py:266')
    bl_options = {'UNDO', 'INTERNAL'}
    value: FloatProperty(min=0, max=1, translation_context='MWK:operators/weight_paint.py:268')

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        ups = compat.unified_paint_settings(context.tool_settings)
        brush = context.tool_settings.weight_paint.brush
        owner = ups if ups.use_unified_weight or brush is None else brush
        owner.weight = self.value
        return {'FINISHED'}


class ALLSET_OT_weight_mask(bpy.types.Operator):
    bl_translation_context = 'MWK:operators/weight_paint.py:284'
    bl_idname = 'allset.weight_mask'
    bl_label = _zh_native('Weight Paint Selection', 'MWK:operators/weight_paint.py:284')
    bl_options = {'REGISTER', 'UNDO'}
    action: StringProperty(default='ALL', translation_context='MWK:operators/weight_paint.py:286')

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        mesh = context.active_object.data
        if not (mesh.use_paint_mask or mesh.use_paint_mask_vertex):
            mesh.use_paint_mask_vertex = True
        prefix = 'vert' if mesh.use_paint_mask_vertex else 'face'
        try:
            with viewport(context):
                if self.action in {'ALL', 'NONE', 'INVERT'}:
                    native('paint.' + prefix + '_select_all')(
                        action={'ALL': 'SELECT', 'NONE': 'DESELECT', 'INVERT': 'INVERT'}[self.action])
                elif self.action in {'BOX', 'CIRCLE', 'LASSO'}:
                    native('view3d.select_' + self.action.lower())('INVOKE_DEFAULT')
                elif self.action == 'REVEAL':
                    bpy.ops.paint.face_vert_reveal()
                elif self.action in {'HIDE', 'HIDE_OTHER'}:
                    native('paint.' + prefix + '_select_hide')(unselected=self.action == 'HIDE_OTHER')
                else:
                    suffix = {'GROW': 'more', 'SHRINK': 'less', 'LINKED': 'linked', 'UNGROUPED': 'ungrouped'}[self.action]
                    native('paint.' + prefix + '_select_' + suffix)()
            return {'FINISHED'}
        except (RuntimeError, KeyError) as ex:
            self.report({'WARNING'}, _zh(str(ex), 'MWK:operators/weight_paint.py:313'))
            return {'CANCELLED'}


class ALLSET_OT_weight_curve(bpy.types.Operator):
    bl_translation_context = 'MWK:operators/weight_paint.py:319'
    bl_idname = 'allset.weight_curve'
    bl_label = _zh_native('Draw Paint Curve', 'MWK:operators/weight_paint.py:319')

    def execute(self, context):
        with viewport(context):
            if not bpy.ops.paintcurve.draw.poll():
                self.report({'WARNING'}, _zh('Create a Paint Curve before drawing it', 'MWK:operators/weight_paint.py:324'))
                return {'CANCELLED'}
            bpy.ops.paintcurve.draw('INVOKE_DEFAULT')
        return {'FINISHED'}


class ALLSET_OT_weight_influence(bpy.types.Operator):
    bl_translation_context = 'MWK:operators/weight_paint.py:332'
    bl_idname = 'allset.weight_influence'
    bl_label = _zh_native('Influence Locks', 'MWK:operators/weight_paint.py:332')
    bl_options = {'UNDO'}
    action: EnumProperty(items=_zh_enum([('LOCK', 'Lock all', ''), ('UNLOCK', 'Unlock all', ''),
                               ('OTHERS', 'Lock unselected', ''), ('INVERT', 'Invert locks', ''),
                               ('LOCK_SELECTED', 'Lock selected joints', ''),
                               ('UNLOCK_SELECTED', 'Unlock selected joints', ''),
                               ('LOCK_OTHERS', 'Lock Inverse Selection', ''),
                               ('UNLOCK_OTHERS', 'Unlock other influences', ''),
                               ('JOINT', 'Select influence joint', '')], 'MWK:operators/weight_paint.py:334'), translation_context='MWK:operators/weight_paint.py:334')

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        mesh = context.active_object
        groups = list(mesh.vertex_groups) if state(context).show_all else skin.influences(mesh)
        vg = mesh.vertex_groups.active
        if self.action == 'JOINT':
            mod = skin.armature_modifier(mesh)
            pb = mod.object.pose.bones.get(vg.name) if mod and vg else None
            if pb is None:
                return {'CANCELLED'}
            from ..ui.channel_box import set_bone_selected
            for bone in mod.object.pose.bones:
                set_bone_selected(bone, bone == pb)
            mod.object.data.bones.active = pb.bone
        else:
            selected = picked_influences(context, mesh)
            for group in groups:
                if self.action in {'LOCK_SELECTED', 'UNLOCK_SELECTED'}:
                    if group.name in selected:
                        group.lock_weight = self.action == 'LOCK_SELECTED'
                elif self.action in {'LOCK_OTHERS', 'UNLOCK_OTHERS'}:      # Maya Lock / Unlock Unselected
                    if group.name not in selected:
                        group.lock_weight = self.action == 'LOCK_OTHERS'
                else:
                    group.lock_weight = (not group.lock_weight if self.action == 'INVERT' else
                                         group != vg if self.action == 'OTHERS' else self.action == 'LOCK')
        return {'FINISHED'}


class ALLSET_OT_weight_workspace(bpy.types.Operator):
    bl_translation_context = 'MWK:operators/weight_paint.py:376'
    bl_idname = 'allset.weight_workspace'
    bl_label = _zh_native('Paint Skin Weights Workspace', 'MWK:operators/weight_paint.py:376')

    def execute(self, context):
        if not active(context):
            result = bpy.ops.allset.paint_skin_weights('EXEC_DEFAULT')
            if 'FINISHED' not in result:
                return result
        from ..ui import tool_dock
        if tool_dock.show(context, width=400) is None:
            self.report({'WARNING'}, _zh('Open a modeling viewport to show Paint Skin Weights', 'MWK:operators/weight_paint.py:385'))
            return {'CANCELLED'}
        return {'FINISHED'}


def locked_snapshot(mesh):
    locked = {g.index: g.name for g in mesh.vertex_groups if g.lock_weight}
    result = {name: {} for name in locked.values()}
    if locked:
        for vertex in mesh.data.vertices:
            for entry in vertex.groups:
                name = locked.get(entry.group)
                if name is not None:
                    result[name][vertex.index] = entry.weight
    return result


def restore_locked(mesh, snapshot):
    indices = {g.index: g.name for g in mesh.vertex_groups if g.name in snapshot}
    current = {name: {} for name in indices.values()}
    if indices:
        for vertex in mesh.data.vertices:
            for entry in vertex.groups:
                name = indices.get(entry.group)
                if name is not None:
                    current[name][vertex.index] = entry.weight
    for name, before in snapshot.items():
        group = mesh.vertex_groups.get(name)
        if group is None:
            continue
        after = current[name]
        remove = list(after.keys() - before.keys())
        if remove:
            group.remove(remove)
        for index, weight in before.items():
            if after.get(index) != weight:
                group.add([index], weight, 'REPLACE')


@contextmanager
def vertex_targets(mesh, indices):
    """Give native flood/smooth/normalize the same precise mask, then restore it."""
    data = mesh.data
    selected = [v.select for v in data.vertices]
    vertex_mask, face_mask = data.use_paint_mask_vertex, data.use_paint_mask
    targets = set(indices)
    try:
        data.use_paint_mask = False
        data.use_paint_mask_vertex = True
        for vertex in data.vertices:
            vertex.select = vertex.index in targets
        data.update()
        yield
    finally:
        data.use_paint_mask_vertex = vertex_mask
        data.use_paint_mask = face_mask
        for vertex, value in zip(data.vertices, selected):
            vertex.select = value
        data.update()


# --- Flood (Maya 2026 Paint Skin Weights Flood) ---------
# Maya applies the operation to the influence being painted, multiplied by Opacity o:
#   Replace w' = w + o(v - w)   Add w' = min(1, w + o v)   Scale w' = w (1 - o (1 - v))
#   Smooth  w' = w + o(avg - w), avg = the mean of the vertex and its edge neighbours (Value ignored; the neighbour
#   rule was fitted to the measured rings, docs/steps/step_218.md)
# and gives the change to the other unlocked influences in their old ratio; locked influences keep their weight; only
# selected vertices change when any vertex is selected (Maya, on polyCylinder h 8 sx 20 sy 8).

OPERATIONS = (('BRUSH', 'Brush', 'The current brush and its blend'), ('REPLACE', 'Replace', ''),
              ('ADD', 'Add', ''), ('SCALE', 'Scale', ''), ('SMOOTH', 'Smooth', ''))
_BLEND_OPERATION = {'MIX': 'REPLACE', 'ADD': 'ADD', 'MUL': 'SCALE'}


def maya_target(op, w, value, opacity, avg=None):
    """New weight of the painted influence for one vertex (before clamping / redistribution)."""
    if op == 'REPLACE':
        return w + opacity * (value - w)
    if op == 'ADD':
        return w + opacity * value
    if op == 'SCALE':
        return w * (1.0 - opacity * (1.0 - value))
    if op == 'SMOOTH':
        return w + opacity * (avg - w)
    if op == 'SUB':
        return w - opacity * value
    if op == 'LIGHTEN':
        return w + opacity * (max(w, value) - w)
    if op == 'DARKEN':
        return w + opacity * (min(w, value) - w)
    raise ValueError(op)


def redistribute(weights, target, new, locked, influences):
    """Maya Interactive normalization of one vertex: ``weights`` {group: w}; returns the new {group: w}.

    The painted influence gets ``new`` clamped to what the locked ones leave; the unlocked other influences share the
    rest in their old ratio (Replace 0.3 keeps j1:j3, Value 0 gives j2's weight to j1 / j3, joint1 locked + Add 1 only
    takes joint3's share)."""
    out = dict(weights)
    locked_sum = sum(w for g, w in weights.items() if g != target and g in locked and g in influences)
    others = {g: w for g, w in weights.items() if g != target and g not in locked and g in influences and w > 0}
    room = max(0.0, 1.0 - locked_sum)
    new = min(max(new, 0.0), room)
    total = sum(others.values())
    if total <= 0.0:
        # nothing unlocked takes the rest: a normalized vertex can't lose weight, an unweighted one simply gets the
        # value (Maya's value unknown: delegated)
        new = max(new, min(room, weights.get(target, 0.0)))
    else:
        rest = room - new
        for g, w in others.items():
            out[g] = rest * w / total
    out[target] = new
    return out


def flood_vertices(mesh):
    """Vertices a Flood changes: the face mask's faces, else the selected vertices when any vertex is selected (Maya
    floods only selected components, vertex mask on or off), else every visible vertex."""
    data = mesh.data
    visible = [v.index for v in data.vertices if not v.hide]
    if data.use_paint_mask:
        faces = {i for f in data.polygons if f.select and not f.hide for i in f.vertices}
        return [i for i in visible if i in faces]
    selected = [i for i in visible if data.vertices[i].select]
    return selected if selected else visible


def _neighbours(data):
    nb = [[] for _ in data.vertices]
    for e in data.edges:
        a, b = e.vertices
        nb[a].append(b)
        nb[b].append(a)
    return nb


def flood_settings(context, operation='BRUSH'):
    """(operation, value, opacity) from the operator or the current brush."""
    ts = context.tool_settings
    brush = ts.weight_paint.brush
    ups = compat.unified_paint_settings(ts)
    strength = (ups if ups.use_unified_strength or brush is None else brush).strength
    value = (ups if ups.use_unified_weight or brush is None else brush).weight
    if operation != 'BRUSH':
        return operation, value, strength
    kind = brush_kind(brush) or 'DRAW'
    if kind == 'SMEAR':
        raise ValueError('Smear needs a directional stroke; choose another operation to flood')
    if kind == 'BLUR':
        return 'SMOOTH', value, strength
    if kind == 'AVERAGE':
        return 'AVERAGE', value, strength
    blend = brush.blend if brush is not None else 'MIX'
    op = _BLEND_OPERATION.get(blend, blend)
    if op not in {'REPLACE', 'ADD', 'SCALE', 'SUB', 'LIGHTEN', 'DARKEN'}:
        raise ValueError('Flood supports Replace, Add, Scale, Smooth, Subtract, Lighten, Darken and Average')
    return op, value, strength


def flood(context, operation='BRUSH'):
    """Maya Flood: the paint operation x Opacity into the painted influence, Maya's redistribution and locks."""
    mesh = context.active_object
    group = mesh.vertex_groups.active
    if group is None or group.lock_weight:
        raise ValueError('Choose an unlocked influence before flooding')
    op, value, opacity = flood_settings(context, operation)
    data = mesh.data
    targets = flood_vertices(mesh)
    if context.tool_settings.weight_paint.use_group_restrict:
        targets = [i for i in targets if any(e.group == group.index for e in data.vertices[i].groups)]
    if not targets or opacity <= 0:
        return {'FINISHED'}
    t = group.index
    rows = {i: {e.group: e.weight for e in data.vertices[i].groups} for i in targets}
    nb, own = None, None
    if op == 'SMOOTH':
        nb = _neighbours(data)
        own = {}
        for i in {j for i in targets for j in (i, *nb[i])}:
            own[i] = next((e.weight for e in data.vertices[i].groups if e.group == t), 0.0)
    elif op == 'AVERAGE':
        op, value = 'REPLACE', sum(r.get(t, 0.0) for r in rows.values()) / len(rows)
    influences = {g.index for g in skin.influences(mesh)}
    normalize = context.tool_settings.use_auto_normalize and t in influences
    locked = {g.index for g in mesh.vertex_groups if g.lock_weight}
    groups = mesh.vertex_groups
    st = state(context)
    lo_hi = (min(st.min_value, st.max_value), max(st.min_value, st.max_value))
    for i, row in rows.items():
        w = row.get(t, 0.0)
        avg = (own[i] + sum(own[j] for j in nb[i])) / (1 + len(nb[i])) if op == 'SMOOTH' else None
        new = maya_target(op, w, value, opacity, avg)
        new = min(lo_hi[1], max(lo_hi[0], new))         # Maya Min / Max value (step 224)
        if normalize:
            result = redistribute(row, t, new, locked, influences)
        else:
            result = {**row, t: min(1.0, max(0.0, new))}
        for g, nw in result.items():
            if nw == row.get(g):
                continue
            if nw <= 0.0:
                if g in row:
                    groups[g].remove([i])
            else:
                groups[g].add([i], nw, 'REPLACE')
    data.update()
    state(context).status = 'Flood complete'
    return {'FINISHED'}


# --- Influences list RMB (Maya 2026) -------------------

NO_INFLUENCE = 'Please select an influence first'      # Maya's warning text


def picked_influences(context, mesh):
    """The influences "selected in the Influences list" (Maya's treeView selection): Blender's list has one active
    row, so that row. Selected joints don't count (delegated): a skeleton often stays fully selected after it is
    made or bound, which would turn Select Vertices into "every vertex"."""
    vg = mesh.vertex_groups.active
    return {vg.name} if vg is not None else set()


def affected_vertices(mesh, names):
    """Vertices whose weight in any of the named influences is > 0 (Maya Select Affected Vertices)."""
    idx = {mesh.vertex_groups[n].index for n in names if n in mesh.vertex_groups}
    return {v.index for v in mesh.data.vertices if any(e.group in idx and e.weight > 0.0 for e in v.groups)}


def show_vertex_selection(mesh):
    """Blender shows (and limits painting to) a weight-paint vertex selection only with the vertex mask on."""
    mesh.data.use_paint_mask = False
    mesh.data.use_paint_mask_vertex = True


def set_vertex_selection(mesh, indices):
    from .. import compat
    data = mesh.data
    compat.repair_selection_attributes(data)     # Blender 5.0.1: a mistyped .select_edge crashes MeshEdge.select
    keep = set(indices)
    for v in data.vertices:
        v.select = v.index in keep and not v.hide
    for e in data.edges:
        e.select = all(data.vertices[i].select for i in e.vertices)
    for f in data.polygons:
        f.select = all(data.vertices[i].select for i in f.vertices)
    data.update()


class ALLSET_OT_weight_influence_verts(bpy.types.Operator):
    """Select the vertices the influences picked in the list affect (weight > 0)"""
    bl_translation_context = 'MWK:operators/weight_paint.py:639'
    bl_idname = 'allset.weight_influence_verts'
    bl_label = _zh_native('Select Vertices', 'MWK:operators/weight_paint.py:639')
    bl_description = _zh_native('Select the vertices the influences picked in the list affect (weight > 0)', 'MWK:operators/weight_paint.py:639')
    bl_options = {'UNDO'}
    mode: EnumProperty(items=_zh_enum([('SET', 'Select Vertices', 'Select the vertices the picked influences affect'),
                              ('ADD', 'Add Affected Vertices', 'Add them to the vertex selection'),
                              ('REMOVE', 'Remove Affected Vertices', 'Remove them from the vertex selection')], 'MWK:operators/weight_paint.py:641'),
                       options={'SKIP_SAVE'}, translation_context='MWK:operators/weight_paint.py:641')

    @classmethod
    def description(cls, context, properties):
        return _zh({'SET': 'Select the vertices the picked influences affect (weight above 0)',
                'ADD': 'Add the vertices the picked influences affect to the selection',
                'REMOVE': 'Remove the vertices the picked influences affect from the selection'}[properties.mode], 'MWK:operators/weight_paint.py:648')

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        mesh = context.active_object
        names = picked_influences(context, mesh)
        if not names:
            self.report({'ERROR'}, _zh(NO_INFLUENCE, 'MWK:operators/weight_paint.py:660'))
            return {'CANCELLED'}
        hit = affected_vertices(mesh, names)
        current = {v.index for v in mesh.data.vertices if v.select}
        chosen = hit if self.mode == 'SET' else current | hit if self.mode == 'ADD' else current - hit
        show_vertex_selection(mesh)
        set_vertex_selection(mesh, chosen)
        return {'FINISHED'}


# --- Skin Paint Mode (Paint / Select / Paint Select, Ctrl+. / Ctrl+,) and Select Geometry ----------------------

class ALLSET_OT_weight_skin_cluster(bpy.types.Operator):
    """Show this skin cluster's influences in the Influences list"""
    bl_translation_context = 'MWK:operators/weight_paint.py:675'
    bl_idname = 'allset.weight_skin_cluster'
    bl_label = _zh_native('Skin Cluster', 'MWK:operators/weight_paint.py:675')
    bl_description = _zh_native("Show this skin cluster's influences in the Influences list", 'MWK:operators/weight_paint.py:675')
    bl_options = {'INTERNAL'}

    index: IntProperty(default=0, min=0, translation_context='MWK:operators/weight_paint.py:678')

    def execute(self, context):
        state(context).skin_cluster = self.index
        for area in context.screen.areas if context.screen else ():
            area.tag_redraw()
        return {'FINISHED'}


class ALLSET_OT_weight_profile(bpy.types.Operator):
    """Maya brush Profile: the brush falloff (Gaussian / Soft / Solid)"""
    bl_translation_context = 'MWK:operators/weight_paint.py:690'
    bl_idname = 'allset.weight_profile'
    bl_label = _zh_native('Profile', 'MWK:operators/weight_paint.py:690')
    bl_description = _zh_native('Maya brush Profile: the brush falloff (Gaussian / Soft / Solid)', 'MWK:operators/weight_paint.py:690')
    bl_options = {'REGISTER', 'UNDO'}

    profile: EnumProperty(items=_zh_enum([(k, k.title(), '') for k in ('GAUSSIAN', 'SOFT', 'SOLID', 'SQUARE')], 'MWK:operators/weight_paint.py:693'),
                          options={'SKIP_SAVE'}, translation_context='MWK:operators/weight_paint.py:693')

    @classmethod
    def description(cls, context, properties):
        if properties.profile == 'SQUARE':
            return _zh("Blender brushes are round: Maya's Square profile has no Blender brush", 'MWK:operators/weight_paint.py:699')
        return _zh(f"Brush falloff {skin.PROFILE_CURVE.get(properties.profile, '').title()}", 'MWK:operators/weight_paint.py:700')

    def execute(self, context):
        brush = context.tool_settings.weight_paint.brush
        preset = skin.PROFILE_CURVE.get(self.profile)
        if brush is None or preset is None:
            self.report({'WARNING'}, _zh("Blender brushes are round: no Square profile", 'MWK:operators/weight_paint.py:706'))
            return {'CANCELLED'}
        if not skin._brush_set(brush, compat.brush_falloff_props(brush)[0], preset):
            self.report({'WARNING'}, _zh("This brush is a linked asset: Blender keeps its falloff", 'MWK:operators/weight_paint.py:709'))
            return {'CANCELLED'}
        return {'FINISHED'}


PAINT_MODES = ('PAINT', 'SELECT', 'PAINT_SELECT')
MODE_LABELS = {'PAINT': 'Paint', 'SELECT': 'Select', 'PAINT_SELECT': 'Paint Select'}
_MODE_TOOLS = {'SELECT': 'builtin.select_box', 'PAINT_SELECT': 'builtin.select_circle'}


def paint_mode(context):
    """Maya's Skin Paint Mode read from the active weight-paint tool."""
    ws = context.workspace
    tool = ws.tools.from_space_view3d_mode('PAINT_WEIGHT', create=False) if ws is not None else None
    name = tool.idname if tool is not None else ''
    if name == 'builtin.select_circle':
        return 'PAINT_SELECT'
    if name.startswith('builtin.select'):
        return 'SELECT'
    return 'PAINT'


def next_mode(mode, step):
    return PAINT_MODES[(PAINT_MODES.index(mode) + step) % len(PAINT_MODES)]


class ALLSET_OT_skin_paint_mode(bpy.types.Operator):
    """Maya Skin Paint Mode: Paint weights, Select vertices, or Paint Select vertices with a brush"""
    bl_translation_context = 'MWK:operators/weight_paint.py:738'
    bl_idname = 'allset.skin_paint_mode'
    bl_label = _zh_native('Skin Paint Mode', 'MWK:operators/weight_paint.py:738')
    bl_description = _zh_native('Maya Skin Paint Mode: Paint weights, Select vertices, or Paint Select vertices with a brush', 'MWK:operators/weight_paint.py:738')
    bl_options = {'UNDO'}
    mode: EnumProperty(items=_zh_enum([('PAINT', 'Paint', 'Paint weights'), ('SELECT', 'Select', 'Select vertices'),
                              ('PAINT_SELECT', 'Paint Select', 'Select vertices with a brush')], 'MWK:operators/weight_paint.py:740'),
                       options={'SKIP_SAVE'}, translation_context='MWK:operators/weight_paint.py:740')
    step: IntProperty(default=0, options={'SKIP_SAVE', 'HIDDEN'},
                      description=_zh_native('1 = next mode (Ctrl+.), -1 = previous mode (Ctrl+,), 0 = the mode above', 'MWK:operators/weight_paint.py:743'), translation_context='MWK:operators/weight_paint.py:743')

    @classmethod
    def description(cls, context, properties):
        if properties.step:
            return _zh('Next Skin Paint Mode' if properties.step > 0 else 'Previous Skin Paint Mode', 'MWK:operators/weight_paint.py:749')
        return _zh({'PAINT': 'Paint weights with the brush',
                'SELECT': 'Select vertices (drag a box); Flood then fills only the selection',
                'PAINT_SELECT': 'Select vertices by brushing over them'}[properties.mode], 'MWK:operators/weight_paint.py:750')

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        current = paint_mode(context)
        mode = next_mode(current, self.step) if self.step else self.mode
        mesh = context.active_object
        s = state(context)
        try:
            if mode == 'PAINT':
                skin.set_view_tool(context, s.paint_tool or 'builtin.brush')
            else:
                if current == 'PAINT':
                    ws = context.workspace
                    tool = ws.tools.from_space_view3d_mode('PAINT_WEIGHT', create=False) if ws else None
                    s.paint_tool = tool.idname if tool is not None and tool.idname else 'builtin.brush'
                show_vertex_selection(mesh)
                from ..ui import toolbox
                toolbox.KEEP_PAINT[0] = True
                try:
                    skin.set_view_tool(context, _MODE_TOOLS[mode])
                finally:
                    toolbox.KEEP_PAINT[0] = False
        except RuntimeError as ex:
            self.report({'WARNING'}, _zh(str(ex), 'MWK:operators/weight_paint.py:779'))
            return {'CANCELLED'}
        from .. import results
        results.result(self, _zh('Paint mode: ' + MODE_LABELS[mode], 'MWK:operators/weight_paint.py:782'))
        return {'FINISHED'}


class ALLSET_OT_select_geometry(bpy.types.Operator):
    """Select the whole mesh (drop the vertex selection) and keep painting"""
    bl_translation_context = 'MWK:operators/weight_paint.py:789'
    bl_idname = 'allset.select_geometry'
    bl_label = _zh_native('Select Geometry', 'MWK:operators/weight_paint.py:789')
    bl_description = _zh_native('Select the whole mesh (drop the vertex selection) and keep painting', 'MWK:operators/weight_paint.py:789')
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        mesh = context.active_object
        set_vertex_selection(mesh, ())
        mesh.data.use_paint_mask_vertex = False
        mesh.data.use_paint_mask = False
        mesh.select_set(True)
        return {'FINISHED'}


class ALLSET_OT_paint_copy_vertex_weights(bpy.types.Operator):
    """Maya Copy Vertex Weights while painting: remember the active (else first selected) vertex's weights"""
    bl_translation_context = 'MWK:operators/weight_paint.py:808'
    bl_idname = 'allset.paint_copy_vertex_weights'
    bl_label = _zh_native('Copy Vertex Weights', 'MWK:operators/weight_paint.py:808')
    bl_description = _zh_native("Maya Copy Vertex Weights while painting: remember the active (else first selected) vertex's weights", 'MWK:operators/weight_paint.py:808')

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        import bmesh
        mesh = context.active_object
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh.data)
            act = bm.select_history.active
            index = act.index if isinstance(act, bmesh.types.BMVert) and act.select else None
        finally:
            bm.free()
        if index is None:
            index = next((v.index for v in mesh.data.vertices if v.select and not v.hide), None)
        if index is None:
            self.report({'WARNING'}, _zh('Select a vertex', 'MWK:operators/weight_paint.py:827'))
            return {'CANCELLED'}
        names = {vg.index: vg.name for vg in mesh.vertex_groups}
        skin._VERTEX_CLIPBOARD.clear()
        skin._VERTEX_CLIPBOARD.update({names[e.group]: e.weight for e in mesh.data.vertices[index].groups
                                       if e.group in names})
        from .. import results
        results.result(self, _zh(f"Copied {len(skin._VERTEX_CLIPBOARD)} weight(s)", 'MWK:operators/weight_paint.py:834'))
        return {'FINISHED'}


class ALLSET_OT_paint_paste_vertex_weights(bpy.types.Operator):
    """Maya Paste Vertex Weights while painting: give the selected vertices the copied weights"""
    bl_translation_context = 'MWK:operators/weight_paint.py:841'
    bl_idname = 'allset.paint_paste_vertex_weights'
    bl_label = _zh_native('Paste Vertex Weights', 'MWK:operators/weight_paint.py:841')
    bl_description = _zh_native('Maya Paste Vertex Weights while painting: give the selected vertices the copied weights', 'MWK:operators/weight_paint.py:841')
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return active(context) and bool(skin._VERTEX_CLIPBOARD)

    def execute(self, context):
        mesh = context.active_object
        targets = [v.index for v in mesh.data.vertices if v.select and not v.hide]
        if not targets:
            self.report({'WARNING'}, _zh('Select vertices to paste the weights on', 'MWK:operators/weight_paint.py:852'))
            return {'CANCELLED'}
        groups = {name: (mesh.vertex_groups.get(name) or mesh.vertex_groups.new(name=name))
                  for name in skin._VERTEX_CLIPBOARD}
        for vg in mesh.vertex_groups:
            if vg.name not in groups:
                vg.remove(targets)
        for name, w in skin._VERTEX_CLIPBOARD.items():
            groups[name].add(targets, w, 'REPLACE')
        mesh.data.update()
        from .. import results
        results.result(self, _zh(f"Pasted weights on {len(targets)} vertices", 'MWK:operators/weight_paint.py:863'))
        return {'FINISHED'}


class ALLSET_OT_paint_reflection(bpy.types.Operator):
    """Maya Toggle Reflection while painting: mirror the paint across X"""
    bl_translation_context = 'MWK:operators/weight_paint.py:870'
    bl_idname = 'allset.paint_reflection'
    bl_label = _zh_native('Toggle Reflection', 'MWK:operators/weight_paint.py:870')
    bl_description = _zh_native('Maya Toggle Reflection while painting: mirror the paint across X', 'MWK:operators/weight_paint.py:870')
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return active(context)

    def execute(self, context):
        data = context.active_object.data
        data.use_mirror_x = not data.use_mirror_x
        from .. import results
        results.result(self, _zh('Reflection ' + ('on (X)' if data.use_mirror_x else 'off'), 'MWK:operators/weight_paint.py:881'))
        return {'FINISHED'}


class ALLSET_OT_weight_action(bpy.types.Operator):
    bl_translation_context = 'MWK:operators/weight_paint.py:887'
    bl_idname = 'allset.weight_action'
    bl_label = _zh_native('Edit Skin Weights', 'MWK:operators/weight_paint.py:887')
    bl_options = {'REGISTER', 'UNDO'}
    action: EnumProperty(items=_zh_enum([(key, label, label) for key, (label, op) in ACTIONS.items()], 'MWK:operators/weight_paint.py:889'), translation_context='MWK:operators/weight_paint.py:889')

    @classmethod
    def description(cls, context, properties):
        return _zh(ACTIONS.get(properties.action, ('Edit Skin Weights', ''))[0] + ': configure and apply; locked influences stay protected', 'MWK:operators/weight_paint.py:893')

    @classmethod
    def poll(cls, context):
        return active(context) and len(context.active_object.vertex_groups) > 0

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=380, title=_zh(ACTIONS[self.action][0], 'MWK:operators/weight_paint.py:900'), confirm_text=_zh('Apply', 'MWK:operators/weight_paint.py:900'))

    def draw(self, context):
        layout = self.layout
        settings = getattr(state(context), self.action.lower())
        layout.use_property_split = True
        layout.use_property_decorate = False
        for name in _FIELDS[self.action]:
            if self.action in {'AUTO', 'ENVELOPE'} and name == 'type':
                continue
            layout.prop(settings, name)
        if not _FIELDS[self.action]:
            layout.label(text=(_zh('Assign the current Value to the masked or visible vertices.' if self.action == 'SET'
                               else 'Normalize the active influence to its maximum weight.', 'MWK:operators/weight_paint.py:912')))
        note = layout.row()
        note.active = False
        note.label(text=_zh('Locked influences are preserved.', 'MWK:operators/weight_paint.py:916'), icon='LOCKED')
        if context.active_object.data.use_paint_mask_vertex or context.active_object.data.use_paint_mask:
            layout.label(text=_zh('Selection mask limits affected vertices.', 'MWK:operators/weight_paint.py:918'), icon='RESTRICT_SELECT_OFF')

    def execute(self, context):
        mesh = context.active_object
        settings = getattr(state(context), self.action.lower())
        values = {k: getattr(settings, k) for k in _FIELDS[self.action] if k != 'source'}
        if self.action in {'AUTO', 'ENVELOPE'}:
            values['type'] = 'AUTOMATIC' if self.action == 'AUTO' else 'ENVELOPES'
        if self.action == 'TRANSFER':
            source = settings.source
            if source is None or source == mesh or source.name not in context.view_layer.objects:
                self.report({'WARNING'}, _zh('Choose a different source mesh in this view layer', 'MWK:operators/weight_paint.py:929'))
                return {'CANCELLED'}
            values.update(data_type='VGROUP_WEIGHTS', use_reverse_transfer=True)
            # Blender's reverse-transfer flag also reverses the two layer enums.
            # Keep the workspace labels in source -> painted mesh order.
            values['layers_select_src'], values['layers_select_dst'] = (
                values['layers_select_dst'], values['layers_select_src'])
        snapshot = locked_snapshot(mesh)
        selected = list(context.selected_objects)
        try:
            with viewport(context):
                if self.action == 'TRANSFER':
                    for ob in context.selected_objects:
                        if ob != mesh:
                            ob.select_set(False)
                    settings.source.select_set(True)
                op = native(ACTIONS[self.action][1])
                if not op.poll():
                    raise RuntimeError('This operation needs a skinned mesh and a valid influence selection')
                result = op('EXEC_DEFAULT', **values)
                if 'FINISHED' not in result:
                    return result
            state(context).status = ACTIONS[self.action][0] + ' complete'
            return {'FINISHED'}
        except (RuntimeError, TypeError, ValueError) as ex:
            self.report({'WARNING'}, _zh(str(ex), 'MWK:operators/weight_paint.py:954'))
            return {'CANCELLED'}
        finally:
            restore_locked(mesh, snapshot)
            if self.action == 'TRANSFER':
                for ob in context.selected_objects:
                    if ob not in selected:
                        ob.select_set(False)
                for ob in selected:
                    ob.select_set(True)
                context.view_layer.objects.active = mesh


classes = (*_SETTING_CLASSES, ALLSET_PG_weight_workspace, ALLSET_OT_weight_tool,
           ALLSET_OT_weight_value, ALLSET_OT_weight_mask, ALLSET_OT_weight_influence, ALLSET_OT_weight_action,
           ALLSET_OT_weight_workspace, ALLSET_OT_weight_curve, ALLSET_OT_weight_influence_verts,
           ALLSET_OT_skin_paint_mode, ALLSET_OT_select_geometry, ALLSET_OT_weight_skin_cluster, ALLSET_OT_weight_profile, ALLSET_OT_paint_copy_vertex_weights,
           ALLSET_OT_paint_paste_vertex_weights, ALLSET_OT_paint_reflection)


def register_props():
    bpy.types.WindowManager.allset_weight_workspace = PointerProperty(type=ALLSET_PG_weight_workspace, translation_context='MWK:operators/weight_paint.py:975')
    # Good skinning defaults without changing mesh/brush data.
    s = bpy.context.window_manager.allset_weight_workspace
    s.transfer.vert_mapping = 'POLYINTERP_NEAREST'
    s.transfer.layers_select_src = 'ALL'
    s.transfer.layers_select_dst = 'NAME'


def unregister_props():
    if hasattr(bpy.types.WindowManager, 'allset_weight_workspace'):
        del bpy.types.WindowManager.allset_weight_workspace

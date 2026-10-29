# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Maya 2022 curve commands on Blender curves (step 156;
maths in ``curves_math`` — bpy-free, tested against Maya's numbers).

Representation (docs/steps/step_156.md 「계획」): a Maya clamped-uniform NURBS curve = a Blender NURBS spline with
``use_endpoint_u`` and order = degree + 1 (Blender's endpoint knots are the clamped uniform vector, measured); periodic
uniform = a cyclic NURBS spline; degree 1 = a POLY spline; any other cubic (non-uniform knots after Detach / Cut at a
curve point) = an exact Bezier decomposition. Blender Bezier input = a cubic B-spline with triple interior knots.
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from mathutils import Vector

from .. import undo_steps
from . import curves_math as cm
from . import naming, units


# --- Blender spline <-> Maya curve -------------------------------------------------------------------

class MCurve:
    """A Maya-style curve: cvs (3-tuples), knots (Maya list), degree, weights (or None), periodic."""

    def __init__(self, cvs, knots, degree, weights=None, periodic=False):
        self.cvs, self.knots, self.degree, self.weights, self.periodic = list(cvs), list(knots), degree, weights, periodic

    def math(self):
        return (self.cvs, self.knots, self.degree, self.weights)


def _periodic_knots(n_unique, degree):
    n = n_unique + degree
    return [float(i - degree + 1) for i in range(n + degree - 1)]


def read_spline(sp, matrix=None):
    """Blender spline -> MCurve (in ``matrix`` space: world when given)."""
    def tx(v):
        v = Vector(v[:3])
        return tuple(matrix @ v) if matrix is not None else tuple(v)

    if sp.type == 'BEZIER':
        pts = list(sp.bezier_points)
        cvs = []
        seq = pts + ([pts[0]] if sp.use_cyclic_u else [])
        for i, (a, b) in enumerate(zip(seq, seq[1:])):
            if i == 0:
                cvs.append(tx(a.co))
            cvs += [tx(a.handle_right), tx(b.handle_left), tx(b.co)]
        segs = (len(cvs) - 1) // 3
        knots = [0.0] * 3 + [float(k) for k in range(1, segs) for _ in range(3)] + [float(segs)] * 3
        return MCurve(cvs, knots, 3)
    pts = [tx(p.co) for p in sp.points]
    weights = [p.co[3] for p in sp.points]
    weights = None if all(abs(w - 1.0) < 1e-9 for w in weights) else weights
    if sp.type == 'POLY':
        return MCurve(pts + ([pts[0]] if sp.use_cyclic_u else []),
                      cm.clamped_uniform(len(pts) + (1 if sp.use_cyclic_u else 0), 1), 1)
    degree = max(1, min(sp.order_u - 1, len(pts) - 1))
    if sp.use_cyclic_u:
        cvs = pts + pts[:degree]
        w = weights + weights[:degree] if weights else None
        return MCurve(cvs, _periodic_knots(len(pts), degree), degree, w, periodic=True)
    if sp.use_endpoint_u:
        return MCurve(pts, cm.clamped_uniform(len(pts), degree), degree, weights)
    # Blender's plain uniform knots (not clamped): Maya's open curve with uniform unclamped knots
    return MCurve(pts, [float(i) for i in range(len(pts) + degree - 1)], degree, weights)


def _norm_knots(knots):
    a, b = knots[0], knots[-1]
    return [(k - a) / (b - a) for k in knots] if b > a else knots


def write_spline(data, c, matrix_inv=None):
    """MCurve -> a new spline in curve ``data`` (points through ``matrix_inv``: world -> object when given)."""
    def tx(v):
        v = Vector(v)
        return tuple(matrix_inv @ v) if matrix_inv is not None else tuple(v)

    if c.degree == 1 and not c.weights:
        sp = data.splines.new('POLY')
        cvs = c.cvs[:-1] if c.periodic else c.cvs
        sp.points.add(len(cvs) - 1)
        for p, v in zip(sp.points, cvs):
            p.co = (*tx(v), 1.0)
        sp.use_cyclic_u = c.periodic
        return sp
    if c.periodic or cm.is_clamped_uniform(c.knots, c.degree):
        unique = len(c.cvs) - c.degree if c.periodic else len(c.cvs)
        sp = data.splines.new('NURBS')
        sp.points.add(unique - 1)
        for i, p in enumerate(sp.points):
            w = c.weights[i] if c.weights else 1.0
            p.co = (*tx(c.cvs[i]), w)
        sp.order_u = c.degree + 1
        sp.use_cyclic_u = c.periodic
        sp.use_endpoint_u = not c.periodic
        sp.resolution_u = 12
        return sp
    if c.degree == 3 and not c.weights:
        segs = cm.to_bezier(c.cvs, c.knots, 3)
        sp = data.splines.new('BEZIER')
        sp.bezier_points.add(len(segs))
        bp = sp.bezier_points
        for i, seg in enumerate(segs):
            bp[i].co = tx(seg[0])
            bp[i].handle_right = tx(seg[1])
            bp[i + 1].handle_left = tx(seg[2])
            bp[i + 1].co = tx(seg[3])
        for p in bp:
            p.handle_left_type = p.handle_right_type = 'FREE'
        bp[0].handle_left = tuple(Vector(bp[0].co) * 2 - Vector(bp[0].handle_right))
        bp[-1].handle_right = tuple(Vector(bp[-1].co) * 2 - Vector(bp[-1].handle_left))
        return sp
    # other degrees with non-uniform knots: a dense polyline of the exact curve (rare)
    pts = cm.samples(c.cvs, c.knots, c.degree, 64, c.weights)
    return write_spline(data, MCurve(pts, cm.clamped_uniform(len(pts), 1), 1), matrix_inv)


def _new_curve_object(context, base, curves, matrix=None, select=True):
    data = bpy.data.curves.new(base + "Shape", 'CURVE')
    data.dimensions = '3D'
    inv = matrix.inverted() if matrix is not None else None
    for c in curves:
        write_spline(data, c, inv)
    ob = bpy.data.objects.new(base, data)
    if matrix is not None:
        ob.matrix_world = matrix
    (context.collection or context.scene.collection).objects.link(ob)
    if select:
        for o in context.selected_objects:
            o.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob
    return ob


def _replace_splines(ob, curves):
    data = ob.data
    data.splines.clear()
    for c in curves:
        write_spline(data, c)


def _curves_selected(context):
    return [o for o in context.selected_objects if o.type == 'CURVE']


# --- drawing tools' builders (operators/curve_draw.py calls these; points in world, scene units) ------

def _named(ob, base="curve"):
    naming.apply_maya_name(ob, base)
    return ob


def make_cv_curve(context, points, degree=3):
    """Maya CV Curve Tool: the clicked points are the CVs (clamped uniform knots)."""
    cvs, knots, deg = cm.cv_curve([tuple(p) for p in points], degree)
    return _new_curve_object(context, "curve", [MCurve(cvs, knots, deg)])


def make_ep_curve(context, points, degree=3, uniform=True):
    """Maya EP Curve Tool (factory Uniform knot spacing): the cubic through the clicks at u = 0 .. n-1, natural ends."""
    cvs, knots, deg = cm.ep_curve([tuple(p) for p in points], degree, uniform)
    return _new_curve_object(context, "curve", [MCurve(cvs, knots, deg)])


def make_arc3(context, p1, p2, p3, sections=8, degree=3):
    cvs, knots, deg = cm.arc3(tuple(p1), tuple(p2), tuple(p3), sections, degree)
    return _new_curve_object(context, "curve", [MCurve(cvs, knots, deg)])


def make_arc2(context, p1, p2, normal=(0.0, 0.0, 1.0), radius=None, toggle=False, sections=8, degree=3):
    """Maya Two Point Circular Arc tool: half circle (radius = chord / 2) about the view normal (ground: +Z)."""
    cvs, knots, deg = cm.arc2(tuple(p1), tuple(p2), tuple(normal), radius, toggle, sections, degree)
    return _new_curve_object(context, "curve", [MCurve(cvs, knots, deg)])


# --- operators -------------------------------------------------------------------------------------------

class _CurveOp:
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'EDIT_CURVE'} and any(o.type == 'CURVE' for o in context.selected_objects)

    def _object_mode(self, context):
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')


@undo_steps.no_redo_panel
class ALLSET_OT_curve_rebuild(_CurveOp, bpy.types.Operator):
    """Rebuild the selected curves with uniform spans (Maya Curves > Rebuild; factory 4 spans, degree 3)"""
    bl_translation_context = 'MWK:operators/curves_maya.py:201'
    bl_idname = "allset.curve_rebuild"
    bl_label = _zh_native("Rebuild Curve", 'MWK:operators/curves_maya.py:201')
    bl_description = _zh_native('Rebuild the selected curves with uniform spans (Maya Curves > Rebuild; factory 4 spans, degree 3)', 'MWK:operators/curves_maya.py:201')

    spans: IntProperty(name=_zh_native("Number of spans", 'MWK:operators/curves_maya.py:203'), default=4, min=1, max=1000, options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:203')
    degree: EnumProperty(name=_zh_native("Degree", 'MWK:operators/curves_maya.py:204'), items=_zh_enum([('1', "1 Linear", ""), ('2', "2", ""), ('3', "3 Cubic", ""),
                                               ('5', "5", ""), ('7', "7", "")], 'MWK:operators/curves_maya.py:204'), default='3', options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:204')

    def execute(self, context):
        self._object_mode(context)
        for ob in _curves_selected(context):
            out = []
            for sp in ob.data.splines:
                c = read_spline(sp)
                if c.periodic:
                    out.append(c)       # periodic rebuild unknown [U]: left as it is
                    continue
                cvs, knots, deg = cm.rebuild(c.cvs, c.knots, c.degree, self.spans, int(self.degree), c.weights)
                out.append(MCurve(cvs, knots, deg))
            _replace_splines(ob, out)
        return {'FINISHED'}


@undo_steps.no_redo_panel
class ALLSET_OT_curve_attach(_CurveOp, bpy.types.Operator):
    """Join two curves into a new one at their nearest ends (Maya Curves > Attach; factory Blend, bias 0.5)"""
    bl_translation_context = 'MWK:operators/curves_maya.py:226'
    bl_idname = "allset.curve_attach"
    bl_label = _zh_native("Attach Curves", 'MWK:operators/curves_maya.py:226')
    bl_description = _zh_native('Join two curves into a new one at their nearest ends (Maya Curves > Attach; factory Blend, bias 0.5)', 'MWK:operators/curves_maya.py:226')

    method: EnumProperty(name=_zh_native("Attach method", 'MWK:operators/curves_maya.py:228'), items=_zh_enum([('CONNECT', "Connect", ""), ('BLEND', "Blend", "")], 'MWK:operators/curves_maya.py:228'),
                         default='BLEND', options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:228')
    bias: FloatProperty(name=_zh_native("Blend bias", 'MWK:operators/curves_maya.py:230'), default=0.5, min=0.0, max=1.0, options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:230')
    keep_originals: EnumProperty(name=_zh_native("Keep originals", 'MWK:operators/curves_maya.py:231'), items=_zh_enum([('ON', "On", ""), ('OFF', "Off", "")], 'MWK:operators/curves_maya.py:231'), default='ON',
                                 options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:231')

    def execute(self, context):
        self._object_mode(context)
        obs = _curves_selected(context)
        if len(obs) != 2:
            self.report({'WARNING'}, _zh("Select two curves to attach", 'MWK:operators/curves_maya.py:238'))
            return {'CANCELLED'}
        active = context.view_layer.objects.active
        first = next(o for o in obs if o is not active) if active in obs else obs[0]
        second = obs[1] if first is obs[0] else obs[0]
        a = read_spline(first.data.splines[0], first.matrix_world)
        b = read_spline(second.data.splines[0], second.matrix_world)
        if a.degree != b.degree or a.periodic or b.periodic:
            self.report({'WARNING'}, _zh("Attach needs two open curves of the same degree", 'MWK:operators/curves_maya.py:246'))
            return {'CANCELLED'}
        cvs, knots = cm.attach((a.cvs, a.knots), (b.cvs, b.knots), a.degree, self.method, self.bias)
        ob = _new_curve_object(context, f"{first.name}attachedCurve", [MCurve(cvs, knots, a.degree)])
        naming.apply_maya_name(ob, f"{first.name}attachedCurve")
        if self.keep_originals == 'OFF':
            for o in (first, second):
                bpy.data.objects.remove(o)
        return {'FINISHED'}


def _greville(c, i):
    p = c.degree
    U = cm.full(c.knots)
    return sum(U[i + 1:i + p + 1]) / p


@undo_steps.no_redo_panel
class ALLSET_OT_curve_detach(_CurveOp, bpy.types.Operator):
    """Split the curve at the edit point nearest each selected CV (Maya Curves > Detach)"""
    bl_translation_context = 'MWK:operators/curves_maya.py:267'
    bl_idname = "allset.curve_detach"
    bl_label = _zh_native("Detach Curve", 'MWK:operators/curves_maya.py:267')
    bl_description = _zh_native('Split the curve at the edit point nearest each selected CV (Maya Curves > Detach)', 'MWK:operators/curves_maya.py:267')

    def execute(self, context):
        ob = context.edit_object if context.mode == 'EDIT_CURVE' else context.active_object
        if ob is None or ob.type != 'CURVE':
            return {'CANCELLED'}
        picks = []
        for si, sp in enumerate(ob.data.splines):
            pts = sp.points if sp.type != 'BEZIER' else sp.bezier_points
            sel = [i for i, p in enumerate(pts) if (p.select if sp.type != 'BEZIER' else p.select_control_point)]
            if sel:
                picks.append((si, sel))
        self._object_mode(context)
        if not picks:
            self.report({'WARNING'}, _zh("Select curve points to detach at", 'MWK:operators/curves_maya.py:281'))
            return {'CANCELLED'}
        out, extra = [], []
        for si, sp in enumerate(ob.data.splines):
            c = read_spline(sp)
            sel = dict(picks).get(si)
            if not sel or c.periodic:
                out.append(c)
                continue
            if sp.type == 'BEZIER':
                us = [float(i) for i in sel]
            else:
                inner = sorted(set(c.knots))
                us = [min(inner, key=lambda k: abs(k - _greville(c, i))) for i in sel]
            us = sorted(u for u in set(us) if c.knots[0] < u < c.knots[-1])
            cur = (c.cvs, c.knots)
            pieces = []
            for u in us:
                a, cur = cm.split(cur[0], cur[1], c.degree, u)
                pieces.append(a)
            pieces.append(cur)
            out.append(MCurve(*pieces[0], c.degree))
            extra += [MCurve(*p, c.degree) for p in pieces[1:]]
        _replace_splines(ob, out)
        for i, c in enumerate(extra):
            new = _new_curve_object(context, f"{ob.name}detachedCurve", [c], ob.matrix_world, select=False)
            naming.apply_maya_name(new, f"{ob.name}detachedCurve")
        return {'FINISHED'}


@undo_steps.no_redo_panel
class ALLSET_OT_curve_cut(_CurveOp, bpy.types.Operator):
    """Cut the selected curves where they cross, keeping all pieces (Maya Curves > Cut)"""
    bl_translation_context = 'MWK:operators/curves_maya.py:315'
    bl_idname = "allset.curve_cut"
    bl_label = _zh_native("Cut Curve", 'MWK:operators/curves_maya.py:315')
    bl_description = _zh_native('Cut the selected curves where they cross, keeping all pieces (Maya Curves > Cut)', 'MWK:operators/curves_maya.py:315')

    # Cut Curve Options (step 196): Cut "Using last curve" / Keep "Longest
    # segments"; the last curve = the active one (Maya's last selected)
    last_only: BoolProperty(name=_zh_native("Using last curve", 'MWK:operators/curves_maya.py:319'), default=False, options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:319')
    keep_longest: BoolProperty(name=_zh_native("Longest segments", 'MWK:operators/curves_maya.py:320'), default=False, options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:320')

    def execute(self, context):
        self._object_mode(context)
        obs = _curves_selected(context)
        if len(obs) < 2:
            self.report({'WARNING'}, _zh("Select two or more crossing curves", 'MWK:operators/curves_maya.py:326'))
            return {'CANCELLED'}
        active = context.view_layer.objects.active
        if self.last_only and active in obs:
            obs.remove(active)
            obs.append(active)
        world = [read_spline(o.data.splines[0], o.matrix_world) for o in obs]
        res = cm.cut_all([c.math() for c in world], last_only=self.last_only, keep_longest=self.keep_longest)
        cuts = 0
        for ob, c, pieces in zip(obs, world, res):
            if len(pieces) < 2:
                if self.keep_longest and pieces and (abs(pieces[0][1][0] - c.knots[0]) > 1e-9
                                                     or abs(pieces[0][1][-1] - c.knots[-1]) > 1e-9):  # longest kept
                    cuts += 1
                    ob.data.splines.clear()
                    write_spline(ob.data, MCurve(*pieces[0], c.degree), ob.matrix_world.inverted())
                continue
            cuts += len(pieces) - 1
            inv = ob.matrix_world.inverted()
            ob.data.splines.clear()
            write_spline(ob.data, MCurve(*pieces[0], c.degree), inv)
            for p in pieces[1:]:
                new = _new_curve_object(context, f"{ob.name}detachedCurve", [MCurve(*p, c.degree)], ob.matrix_world,
                                        select=False)
                naming.apply_maya_name(new, f"{ob.name}detachedCurve")
        if not cuts:
            self.report({'WARNING'}, _zh("The curves don't cross", 'MWK:operators/curves_maya.py:352'))
            return {'CANCELLED'}
        return {'FINISHED'}


@undo_steps.no_redo_panel
class ALLSET_OT_curve_fillet(_CurveOp, bpy.types.Operator):
    """A circular fillet curve between two curves (Maya Curves > Fillet; factory radius 1)"""
    bl_translation_context = 'MWK:operators/curves_maya.py:361'
    bl_idname = "allset.curve_fillet"
    bl_label = _zh_native("Fillet Curves", 'MWK:operators/curves_maya.py:361')
    bl_description = _zh_native('A circular fillet curve between two curves (Maya Curves > Fillet; factory radius 1)', 'MWK:operators/curves_maya.py:361')

    radius: FloatProperty(name=_zh_native("Radius", 'MWK:operators/curves_maya.py:363'), default=1.0, min=0.0001, options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:363')

    def execute(self, context):
        self._object_mode(context)
        obs = _curves_selected(context)
        if len(obs) != 2:
            self.report({'WARNING'}, _zh("Select two curves to fillet", 'MWK:operators/curves_maya.py:369'))
            return {'CANCELLED'}
        a, b = (read_spline(o.data.splines[0], o.matrix_world) for o in obs)
        res = cm.fillet_curves(a.math(), b.math(), self.radius * units.maya_unit(context.scene))
        if res is None:
            self.report({'WARNING'}, _zh("Fillet needs two curves that are not parallel", 'MWK:operators/curves_maya.py:374'))
            return {'CANCELLED'}
        cvs, knots, weights = res
        ob = _new_curve_object(context, "filletedCurve", [MCurve(cvs, knots, 3, weights)])
        naming.apply_maya_name(ob, "filletedCurve")
        return {'FINISHED'}


@undo_steps.no_redo_panel
class ALLSET_OT_curve_straighten(_CurveOp, bpy.types.Operator):
    """Lay every CV leg of the selected curves on one line, keeping their lengths (Maya Curves > Straighten)"""
    bl_translation_context = 'MWK:operators/curves_maya.py:386'
    bl_idname = "allset.curve_straighten"
    bl_label = _zh_native("Straighten Curve", 'MWK:operators/curves_maya.py:386')
    bl_description = _zh_native('Lay every CV leg of the selected curves on one line, keeping their lengths (Maya Curves > Straighten)', 'MWK:operators/curves_maya.py:386')

    # Straighten Curves Options (step 196): Maya factory Straightness 1, Preserve length on
    straightness: FloatProperty(name=_zh_native("Straightness", 'MWK:operators/curves_maya.py:389'), default=1.0, soft_min=0.0, soft_max=2.0, options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:389')
    preserve_length: BoolProperty(name=_zh_native("Preserve length", 'MWK:operators/curves_maya.py:390'), default=True, options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:390')

    def execute(self, context):
        self._object_mode(context)
        for ob in _curves_selected(context):
            out = []
            for sp in ob.data.splines:
                c = read_spline(sp)
                if not c.periodic and len(c.cvs) >= 2:
                    c = MCurve(cm.straighten(c.cvs, self.straightness, self.preserve_length), c.knots, c.degree,
                               c.weights)
                out.append(c)
            _replace_splines(ob, out)
        return {'FINISHED'}


@undo_steps.no_redo_panel
class ALLSET_OT_curve_smooth_curves(_CurveOp, bpy.types.Operator):
    """Smooth the CVs of the selected curves, ends kept (Maya Curves > Smooth in the Modify section, nHair > Modify
    Curves > Smooth; factory Smooth factor 4)"""
    bl_translation_context = 'MWK:operators/curves_maya.py:411'
    bl_idname = "allset.curve_smooth_curves"
    bl_label = _zh_native("Smooth Curves", 'MWK:operators/curves_maya.py:411')
    bl_description = _zh_native('Smooth the CVs of the selected curves, ends kept (Maya Curves > Smooth in the Modify section, nHair > Modify\nCurves > Smooth; factory Smooth factor 4)', 'MWK:operators/curves_maya.py:411')

    factor: IntProperty(name=_zh_native("Smooth factor", 'MWK:operators/curves_maya.py:413'), default=4, min=0, soft_min=1, soft_max=100, options={'SKIP_SAVE'}, translation_context='MWK:operators/curves_maya.py:413')

    def execute(self, context):
        self._object_mode(context)
        for ob in _curves_selected(context):
            out = []
            for sp in ob.data.splines:
                c = read_spline(sp)
                if not c.periodic and len(c.cvs) >= 3:
                    c = MCurve(cm.smooth_cvs(c.cvs, self.factor), c.knots, c.degree, c.weights)
                out.append(c)
            _replace_splines(ob, out)
        return {'FINISHED'}


@undo_steps.no_redo_panel
class ALLSET_OT_curve_move_seam(_CurveOp, bpy.types.Operator):
    """Move the start of a closed curve to the selected point (Maya Curves > Move Seam)"""
    bl_translation_context = 'MWK:operators/curves_maya.py:432'
    bl_idname = "allset.curve_move_seam"
    bl_label = _zh_native("Move Seam", 'MWK:operators/curves_maya.py:432')
    bl_description = _zh_native('Move the start of a closed curve to the selected point (Maya Curves > Move Seam)', 'MWK:operators/curves_maya.py:432')

    def execute(self, context):
        ob = context.edit_object if context.mode == 'EDIT_CURVE' else context.active_object
        if ob is None or ob.type != 'CURVE':
            return {'CANCELLED'}
        done = 0
        if context.mode == 'EDIT_CURVE':
            bpy.ops.object.mode_set(mode='OBJECT')
        for sp in ob.data.splines:
            if not sp.use_cyclic_u or sp.type == 'BEZIER':
                continue
            sel = [i for i, p in enumerate(sp.points) if p.select]
            if not sel:
                continue
            k = sel[0]
            co = [tuple(p.co) for p in sp.points]
            co = co[k:] + co[:k]
            for p, v in zip(sp.points, co):
                p.co = v
            done += 1
        if not done:
            self.report({'WARNING'}, _zh("Select a point on a closed curve", 'MWK:operators/curves_maya.py:454'))
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (ALLSET_OT_curve_rebuild, ALLSET_OT_curve_attach, ALLSET_OT_curve_detach, ALLSET_OT_curve_cut,
           ALLSET_OT_curve_fillet, ALLSET_OT_curve_straighten, ALLSET_OT_curve_move_seam,
           ALLSET_OT_curve_smooth_curves)

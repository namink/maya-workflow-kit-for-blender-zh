# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 156: Maya option windows of the Curves menu and Create > Curve Tools (same spec as operators/option_windows.py;
option_windows._extend appends ``WINDOWS``). Titles, fields and factory values from Maya's option windows
(each option with its factory value). Fields Blender / the kit can't follow are listed as ``missing``."""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy

from .option_windows import F, Window


def _run_rebuild(context, v):
    return bpy.ops.allset.curve_rebuild('EXEC_DEFAULT', spans=v["spans"], degree=v["degree"].split()[0])


def _run_attach(context, v):
    return bpy.ops.allset.curve_attach('EXEC_DEFAULT', method=v["method"].upper(), bias=v["bias"],
                                      keep_originals='ON' if v["keep_originals"] else 'OFF')


def _run_fillet(context, v):
    return bpy.ops.allset.curve_fillet('EXEC_DEFAULT', radius=v["radius"])


def _run_cv_tool(context, v):
    return bpy.ops.allset.cv_curve_tool('INVOKE_DEFAULT', degree=int(v["degree"].split()[0]))


def _run_ep_tool(context, v):
    return bpy.ops.allset.ep_curve_tool('INVOKE_DEFAULT', degree=int(v["degree"].split()[0]))


DEGREES = ("1 Linear", "2", "3 Cubic", "5", "7")

WINDOWS = [
    # Curves > Rebuild (factory: Uniform, 4 spans, degree 3, keep ends, 0 to 1)
    Window("rebuild_curve", "Rebuild Curve Options", "Rebuild", ("allset.curve_rebuild", {}), [
        F("spans", "Number of spans:", "int", 4, lo=1, hi=1000, translation_context='MWK:operators/option_windows_curves.py:39'),
        F("degree", "Degree:", "enum", "3 Cubic", items=("1 Linear", "2", "3 Cubic", "5", "7"), translation_context='MWK:operators/option_windows_curves.py:40'),
    ], _run_rebuild, paths=("Curves/Rebuild",),
        missing=("Rebuild type: Reduce / Match knots / No multiple knots / Curvature / End conditions / Clean "
                 "(Uniform only)", "Parameter range: Keep / 0 to #spans (0 to 1 only)",
                 "Keep: CVs / Tangents / NumSpans (Ends always kept)", "Keep original (off)"), translation_context='MWK:operators/option_windows_curves.py:38'),
    # Curves > Attach (factory: Blend, bias 0.5, keep multiple knots, keep originals)
    Window("attach_curves", "Attach Curves Options", "Attach", ("allset.curve_attach", {}), [
        F("method", "Attach method:", "enum", "Blend", items=("Connect", "Blend"), translation_context='MWK:operators/option_windows_curves.py:47'),
        F("bias", "Blend bias:", "float", 0.5, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_curves.py:48'),
        F("keep_originals", "", "bool", True, text=_zh_native("Keep originals", 'MWK:operators/option_windows_curves.py:49'), translation_context='MWK:operators/option_windows_curves.py:49'),
    ], _run_attach, paths=("Curves/Attach",),
        missing=("Multiple knots: Keep / Remove (Keep)", "Insert knot / Insert parameter (off, 0.1)"), translation_context='MWK:operators/option_windows_curves.py:46'),
    # Curves > Fillet (factory: Circular, radius 1, no trim / join)
    Window("fillet_curve", "Fillet Curve Options", "Fillet", ("allset.curve_fillet", {}), [
        F("radius", "Radius:", "float", 1.0, lo=0.0001, hi=1000.0, translation_context='MWK:operators/option_windows_curves.py:54'),
    ], _run_fillet, paths=("Curves/Fillet",),
        missing=("Trim / Join (off)", "Construction: Freeform (Circular only)", "Keep originals (off)"), translation_context='MWK:operators/option_windows_curves.py:53'),
    # Create > Curve Tools (Tool Settings: degree 3, knot spacing Uniform, multiple end knots)
    Window("cv_curve_tool", "CV Curve Tool", "Create Curve", None, [
        F("degree", "Curve degree:", "enum", "3 Cubic", items=DEGREES, translation_context='MWK:operators/option_windows_curves.py:59'),
    ], _run_cv_tool, paths=("Create/Curve Tools/CV Curve Tool",),
        missing=("Knot spacing: Uniform (Chord length not in the tool)", "Multiple end knots (always on)"), translation_context='MWK:operators/option_windows_curves.py:58'),
    Window("ep_curve_tool", "EP Curve Tool", "Create Curve", None, [
        F("degree", "Curve degree:", "enum", "3 Cubic", items=("1 Linear", "3 Cubic"), translation_context='MWK:operators/option_windows_curves.py:63'),
    ], _run_ep_tool, paths=("Create/Curve Tools/EP Curve Tool",),
        missing=("Knot spacing: Uniform (Chord length not in the tool)", "Multiple end knots (always on)"), translation_context='MWK:operators/option_windows_curves.py:62'),
]

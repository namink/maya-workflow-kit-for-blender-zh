# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 207: Maya option windows of Curves > Bend / Curl / Scale Curvature (same spec as operators/option_windows.py).
Titles, labels and factory values: Maya's Bend / Curl / Scale Curvature Options windows."""

import bpy

from .option_windows import F, Window


def _run(kind, a, b):
    def run(context, v):
        return bpy.ops.allset.curve_modify('EXEC_DEFAULT', kind=kind, amount=v[a], second=v[b])
    return run


WINDOWS = [
    Window("bend_curves", "Bend Curves Options", "Bend Curves", None, [
        F("amount", "Bend amount:", "float", 0.2, lo=-10.0, hi=10.0, translation_context='MWK:operators/option_windows_curves207.py:18'),
        F("twist", "Twist:", "float", 0.0, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_curves207.py:19'),
    ], _run('BEND', "amount", "twist"), paths=("Curves/Bend",), translation_context='MWK:operators/option_windows_curves207.py:17'),
    Window("curl_curves", "Curl Curves Options", "Curl Curves", None, [
        F("amount", "Curl amount:", "float", 0.3, lo=-10.0, hi=10.0, translation_context='MWK:operators/option_windows_curves207.py:22'),
        F("frequency", "Curl frequency:", "float", 1.0, lo=0.0, hi=100.0, translation_context='MWK:operators/option_windows_curves207.py:23'),
    ], _run('CURL', "amount", "frequency"), paths=("Curves/Curl",), translation_context='MWK:operators/option_windows_curves207.py:21'),
    Window("scale_curvature", "Scale Curvature Options", "Scale Curvature", None, [
        F("factor", "Scale factor:", "float", 1.1, lo=0.0, hi=10.0, translation_context='MWK:operators/option_windows_curves207.py:26'),
        F("max_curvature", "Max curvature:", "float", 0.8, lo=0.0, hi=10.0, translation_context='MWK:operators/option_windows_curves207.py:27'),
    ], _run('CURVATURE', "factor", "max_curvature"), paths=("Curves/Scale Curvature",), translation_context='MWK:operators/option_windows_curves207.py:25'),
]

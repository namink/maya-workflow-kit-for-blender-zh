# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Step 197 (#104): Maya's Cleanup Options window for Mesh > Cleanup... (operators/poly_cleanup.py).

Title / button / labels / factory values from Maya 2022's Cleanup Options window.
"""

from ..i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

from .option_windows import F, Window
from .poly_cleanup import run_window

WINDOWS = [
    Window("poly_cleanup", "Cleanup Options", "Cleanup", None, [
        F("operation", "Operation:", "enum", "Cleanup matching polygons",
          items=("Cleanup matching polygons", "Select matching polygons"), heading="Cleanup Effect", translation_context='MWK:operators/option_windows_197.py:14'),
        F("scope", "Scope:", "enum", "Apply to selected objects",
          items=("Apply to selected objects", "Apply to all polygonal objects"), translation_context='MWK:operators/option_windows_197.py:16'),
        F("quads", "", "bool", False, text=_zh_native("4-sided faces", 'MWK:operators/option_windows_197.py:18'), heading="Fix by Tesselation", translation_context='MWK:operators/option_windows_197.py:18'),
        F("nsided", "", "bool", False, text=_zh_native("Faces with more than 4 sides", 'MWK:operators/option_windows_197.py:19'), translation_context='MWK:operators/option_windows_197.py:19'),
        F("concave", "", "bool", False, text=_zh_native("Concave faces", 'MWK:operators/option_windows_197.py:20'), translation_context='MWK:operators/option_windows_197.py:20'),
        F("holes", "", "bool", False, text=_zh_native("Faces with holes", 'MWK:operators/option_windows_197.py:21'), translation_context='MWK:operators/option_windows_197.py:21'),
        F("nonplanar", "", "bool", False, text=_zh_native("Non-planar faces", 'MWK:operators/option_windows_197.py:22'), translation_context='MWK:operators/option_windows_197.py:22'),
        F("lamina", "", "bool", False, text=_zh_native("Lamina faces (faces sharing all edges)", 'MWK:operators/option_windows_197.py:23'), heading="Remove Geometry", translation_context='MWK:operators/option_windows_197.py:23'),
        F("nonmanifold", "", "bool", False, text=_zh_native("Nonmanifold geometry", 'MWK:operators/option_windows_197.py:24'), translation_context='MWK:operators/option_windows_197.py:24'),
        F("nonmanifold_type", "", "enum", "Normals and geometry", items=("Normals and geometry", "Geometry only"), translation_context='MWK:operators/option_windows_197.py:25'),
        F("zero_edge", "", "bool", False, text=_zh_native("Edges with zero length", 'MWK:operators/option_windows_197.py:26'), translation_context='MWK:operators/option_windows_197.py:26'),
        F("edge_tol", "Length tolerance:", "float", 0.00001, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_197.py:27'),
        F("zero_face", "", "bool", False, text=_zh_native("Faces with zero geometry area", 'MWK:operators/option_windows_197.py:28'), translation_context='MWK:operators/option_windows_197.py:28'),
        F("face_tol", "Area tolerance:", "float", 0.00001, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_197.py:29'),
        F("zero_map", "", "bool", False, text=_zh_native("Faces with zero map area", 'MWK:operators/option_windows_197.py:30'), translation_context='MWK:operators/option_windows_197.py:30'),
        F("map_tol", "Area tolerance:", "float", 0.00001, lo=0.0, hi=1.0, translation_context='MWK:operators/option_windows_197.py:31'),
    ], run_window, paths=("Mesh/Cleanup...",),
        missing=("Keep construction history (Blender keeps no polyCleanup node)", "Invalid Components"), translation_context='MWK:operators/option_windows_197.py:13'),
]

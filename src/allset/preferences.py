# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Add-on preferences (Preferences > Add-ons > Maya Workflow Kit).

Options backed by docs/user_decisions.md: Maya units (#1) and parent mode (#2)
from step 10. Only this add-on's own settings live here: since step 130 (#13) no option writes Blender's
preferences (the navigation / undo / panel / auto key / theme / splash / density / font / wire presets are gone).
"""

from .i18n import tr as _zh, enum_items as _zh_enum, native as _zh_native

import bpy


class ALLSET_AddonPreferences(bpy.types.AddonPreferences):
    # Must equal the top-level package name: "bl_ext.<repo>.allset" as an
    # extension, "allset" as a legacy add-on.
    bl_idname = __package__

    # Set once "Maya" was activated automatically on first enable, so later
    # starts respect a different keymap the user picked (docs/steps/step_2.md).
    keymap_auto_activated: bpy.props.BoolProperty(options={'HIDDEN'}, translation_context='MWK:preferences.py:21')

    # Maya mode on/off (switch.py, docs/steps/step_60.md), kept across restarts. Off after install: enabling the
    # extension changes nothing until the user opts in (welcome dialog / button / switch; docs/steps/step_115.md).
    maya_mode: bpy.props.BoolProperty(name=_zh_native("Maya Mode", 'MWK:preferences.py:25'), default=False, options={'HIDDEN'}, translation_context='MWK:preferences.py:25')
    # Edit-mode marquee/lasso also selects occluded components (Maya selectPrefUseDepth false).
    select_through: bpy.props.BoolProperty(
        name=_zh_native("Marquee Selects Hidden Components", 'MWK:preferences.py:27'),
        description=_zh_native("In mesh edit mode, box and lasso selection also pick vertices, edges and faces "
                    "behind the surface, like Maya (Camera based selection off). X-ray is switched "
                    "on only while dragging", 'MWK:preferences.py:27'),
        default=True, translation_context='MWK:preferences.py:27')
    # Maya preSelectHilite true.
    preselect_highlight: bpy.props.BoolProperty(
        name=_zh_native("Pre-selection Highlight", 'MWK:preferences.py:34'),
        description=_zh_native("In mesh edit mode (select and Move / Rotate / Scale tools), highlight the vertex, edge or face "
                    "under the mouse before clicking (Maya)", 'MWK:preferences.py:34'),
        default=True, translation_context='MWK:preferences.py:34')
    # Maya selectPrefPriorityMode "animation", ignoreSelectionPriority false.
    select_priority: bpy.props.BoolProperty(
        name=_zh_native("Selection Priority", 'MWK:preferences.py:40'),
        description=_zh_native("In object mode, a click picks IK handles, then joints (armatures), then curves before meshes "
                    "under the mouse, like Maya's selection priority", 'MWK:preferences.py:40'),
        default=True, translation_context='MWK:preferences.py:40')
    # Step 217 / docs/strategy/DECISIONS7.md decision 6: bone collections = the rigger's "animator controls" set.
    pick_walk_skip_hidden_collections: bpy.props.BoolProperty(
        name=_zh_native("Pick Walk Skips Hidden Bone Collections", 'MWK:preferences.py:46'),
        description=_zh_native("In Pose mode the arrow keys walk past bones whose bone collections are all hidden (Rigify MCH / "
                    "DEF / ORG bones), to the nearest shown parent, child or sibling; a generated Rigify rig follows "
                    "its controls' ORG hierarchy (upper_arm_fk.L Up = shoulder.L). Maya walks into hidden nodes: "
                    "bones hidden one by one (H) are still walked into, and an armature with controller tags "
                    "(Control > Tag As Controller) follows its controller hierarchy instead. Off: plain hierarchy", 'MWK:preferences.py:46'),
        default=True, translation_context='MWK:preferences.py:46')
    # PR #125 extras with no Maya counterpart (no Maya 2022-2027 viewport header has a mode picker or a pulse,
    # PR125_MAYA_LATER.md 4a): off by default.
    armature_mode_header: bpy.props.BoolProperty(
        name=_zh_native("Armature Mode Picker", 'MWK:preferences.py:56'),
        description=_zh_native("Show an Object / Edit Joints / Pose Joints picker at the start of the main viewport header "
                    "while a skeleton is active (not part of Maya)", 'MWK:preferences.py:56'),
        default=False, translation_context='MWK:preferences.py:56')
    armature_mode_pulse: bpy.props.BoolProperty(
        name=_zh_native("Pulse Armature Mode", 'MWK:preferences.py:61'),
        description=_zh_native("Softly pulse the viewport header's mode button while a skeleton is selected (not part of Maya)", 'MWK:preferences.py:61'),
        default=False, translation_context='MWK:preferences.py:61')
    # First start (docs/steps/step_42.md): welcome dialog shown once.
    welcome_done: bpy.props.BoolProperty(options={'HIDDEN'}, translation_context='MWK:preferences.py:66')
    # step 260 (#177): how often the welcome dialog opened without "Make Blender feel like Maya" being clicked
    welcome_shown: bpy.props.IntProperty(options={'HIDDEN'}, translation_context='MWK:preferences.py:68')

    start_in_maya_layout: bpy.props.BoolProperty(
        name=_zh_native("Start in Maya Layout", 'MWK:preferences.py:70'),
        description=_zh_native("When Blender starts without a file in Maya mode, open a new scene in the Maya layout", 'MWK:preferences.py:70'),
        default=False, translation_context='MWK:preferences.py:70')

    # Step 138 (#63): Maya's UI doesn't come from the scene file: opening a file
    # shows the Maya layout (ui/scene_carry.py).
    maya_layout_on_open: bpy.props.BoolProperty(
        name=_zh_native("Keep Maya Layout When Opening Files", 'MWK:preferences.py:77'),
        description=_zh_native("In Maya mode, a file opened in another layout is shown in the Maya layout (its own Maya layout "
                    "workspace when it has one). The file's other workspaces stay", 'MWK:preferences.py:77'),
        default=True, translation_context='MWK:preferences.py:77')

    lock_ortho_tumble: bpy.props.BoolProperty(
        name=_zh_native("Lock Tumble in Ortho Views", 'MWK:preferences.py:83'),
        description=_zh_native("Alt+LMB does nothing in top/front/side orthographic views (Maya)", 'MWK:preferences.py:83'),
        default=True, translation_context='MWK:preferences.py:83')

    # Channel Box virtual slider.
    cb_speed: bpy.props.EnumProperty(
        name=_zh_native("Slider Speed", 'MWK:preferences.py:89'), default='MEDIUM',
        items=_zh_enum((('SLOWEST', "Slowest", "x0.01"), ('SLOW', "Slow", "x0.1"),
               ('MEDIUM', "Medium", "x1"), ('FAST', "Fast", "x10")), 'MWK:preferences.py:89'), translation_context='MWK:preferences.py:89')
    cb_hyperbolic: bpy.props.BoolProperty(
        name=_zh_native("Hyperbolic", 'MWK:preferences.py:93'), description=_zh_native("Value change accelerates with drag distance", 'MWK:preferences.py:93'), translation_context='MWK:preferences.py:93')

    # Graph Editor View > Snap Time To Selection (Maya optionVar snapTimeToSelection, default off; Alt+/ toggles it;
    # docs/steps/step_92.md).
    snap_time_to_selection: bpy.props.BoolProperty(
        name=_zh_native("Snap Time To Selection", 'MWK:preferences.py:98'),
        description=_zh_native("Selecting keys in the Graph Editor moves the current time to the earliest selected key", 'MWK:preferences.py:98'), translation_context='MWK:preferences.py:98')
    # Graph Editor View > Auto Frame / Auto Frame Time / Curve Name (Maya factory: on / off / Never;
    # ui/graph_view.py, step 150).
    graph_auto_frame: bpy.props.BoolProperty(
        name=_zh_native("Auto Frame", 'MWK:preferences.py:103'), default=True,
        description=_zh_native("When the selection changes, the Graph Editor frames the curves it shows (Maya View > Auto Frame)", 'MWK:preferences.py:103'), translation_context='MWK:preferences.py:103')
    # Dope Sheet View > Auto Frame (Maya displayAutoFitItem, factory off in the Dope Sheet; step 166)
    dope_auto_frame: bpy.props.BoolProperty(
        name=_zh_native("Dope Sheet Auto Frame", 'MWK:preferences.py:107'),
        description=_zh_native("When the selection changes, the Dope Sheet frames all the keys it shows (Maya Dope Sheet "
                    "View > Auto Frame)", 'MWK:preferences.py:107'), translation_context='MWK:preferences.py:107')
    graph_auto_frame_time: bpy.props.BoolProperty(
        name=_zh_native("Auto Frame Time", 'MWK:preferences.py:111'),
        description=_zh_native("When the selection changes, the Graph Editor frames the keys along the time axis only "
                    "(Maya View > Auto Frame Time; Auto Frame wins when both are on)", 'MWK:preferences.py:111'), translation_context='MWK:preferences.py:111')
    graph_curve_names: bpy.props.EnumProperty(
        name=_zh_native("Curve Name", 'MWK:preferences.py:115'), default='NEVER',
        description=_zh_native("Write each curve's Maya name (pCube1.translateX) beside its last key in the Graph Editor", 'MWK:preferences.py:115'),
        items=_zh_enum((('ALWAYS', "Always", "Name every curve"), ('NEVER', "Never", "No curve names"),
               ('ACTIVE', "Active Only", "Name the selected curves")), 'MWK:preferences.py:115'), translation_context='MWK:preferences.py:115')

    # Graph Editor depth 2 (step 198): View > Show Buffer Curves (factory off),
    # Curves > Default Tangent Weight (factory Non-weighted), Retime Tool Snap On Frame (factory off), Edit > Set Curve
    # Colors... rules (Maya curveRGBColor: attribute name -> colour; JSON list of [attribute, r, g, b]).
    graph_show_buffers: bpy.props.BoolProperty(
        name=_zh_native("Show Buffer Curves", 'MWK:preferences.py:124'),
        description=_zh_native("Draw each buffered curve's snapshot behind it in the Graph Editor (Maya View > Show Buffer Curves)", 'MWK:preferences.py:124'), translation_context='MWK:preferences.py:124')
    default_tangent_weight: bpy.props.EnumProperty(
        name=_zh_native("Default Tangent Weight", 'MWK:preferences.py:127'), default='NON_WEIGHTED',
        items=_zh_enum((('NON_WEIGHTED', "Non-weighted Tangents", "New curves the kit keys keep every tangent a third of "
                "the way to the next key"),
               ('WEIGHTED', "Weighted Tangents", "New curves the kit keys have tangents whose length can change")), 'MWK:preferences.py:127'),
        description=_zh_native("Tangent weight of the curves the kit creates (Maya Curves > Default Tangent Weight)", 'MWK:preferences.py:127'), translation_context='MWK:preferences.py:127')
    retime_snap_on_frame: bpy.props.BoolProperty(
        name=_zh_native("Snap On Frame", 'MWK:preferences.py:133'),
        description=_zh_native("Retime markers and their drags land on whole frames (Maya Retime Tool setting)", 'MWK:preferences.py:133'), translation_context='MWK:preferences.py:133')
    curve_color_rules: bpy.props.StringProperty(
        name=_zh_native("Curve Colors", 'MWK:preferences.py:136'), default="",
        description=_zh_native("Colour rules by attribute name (Maya Edit > Set Curve Colors...)", 'MWK:preferences.py:136'), translation_context='MWK:preferences.py:136')

    # Script Editor History menu (Maya scriptEditorInfo optionVars; Maya 2022 factory states:
    # Batch Render Messages / Line numbers in errors on,
    # the rest off, History Output Show Both). Read by command_line/runner.py (step 216).
    se_batch_render_messages: bpy.props.BoolProperty(
        name=_zh_native("Batch Render Messages", 'MWK:preferences.py:143'), default=True,
        description=_zh_native("Show batch rendering messages in the Script Editor history (Maya; the kit's batch render "
                    "writes its messages to the system console)", 'MWK:preferences.py:143'), translation_context='MWK:preferences.py:143')
    se_echo_all: bpy.props.BoolProperty(
        name=_zh_native("Echo All Commands", 'MWK:preferences.py:147'),
        description=_zh_native("Write every command run from a menu, shelf or marking menu into the Script Editor history "
                    "(as the Python call the kit runs)", 'MWK:preferences.py:147'), translation_context='MWK:preferences.py:147')
    se_line_numbers: bpy.props.BoolProperty(
        name=_zh_native("Line numbers in errors", 'MWK:preferences.py:151'), default=True,
        description=_zh_native("Error messages name the script line the error happened on", 'MWK:preferences.py:151'), translation_context='MWK:preferences.py:151')
    se_stack_trace: bpy.props.BoolProperty(
        name=_zh_native("Show Stack Trace", 'MWK:preferences.py:154'),
        description=_zh_native("An error writes the whole Python traceback into the Script Editor history", 'MWK:preferences.py:154'), translation_context='MWK:preferences.py:154')
    se_suppress_results: bpy.props.BoolProperty(
        name=_zh_native("Suppress Command Results", 'MWK:preferences.py:157'), description=_zh_native("No \"# Result:\" lines in the Script Editor history", 'MWK:preferences.py:157'), translation_context='MWK:preferences.py:157')
    se_suppress_info: bpy.props.BoolProperty(
        name=_zh_native("Suppress Info Messages", 'MWK:preferences.py:159'), description=_zh_native("No info messages in the Script Editor history", 'MWK:preferences.py:159'), translation_context='MWK:preferences.py:159')
    se_suppress_warnings: bpy.props.BoolProperty(
        name=_zh_native("Suppress Warning Messages", 'MWK:preferences.py:161'), description=_zh_native("No warning messages in the Script Editor history", 'MWK:preferences.py:161'), translation_context='MWK:preferences.py:161')
    se_suppress_errors: bpy.props.BoolProperty(
        name=_zh_native("Suppress Error Messages", 'MWK:preferences.py:163'), description=_zh_native("No error messages in the Script Editor history", 'MWK:preferences.py:163'), translation_context='MWK:preferences.py:163')
    se_suppress_stack_window: bpy.props.BoolProperty(
        name=_zh_native("Suppress Stack Window", 'MWK:preferences.py:165'),
        description=_zh_native("Maya: no stack trace window on error (Blender has no such window: kept for Maya's menu)", 'MWK:preferences.py:165'), translation_context='MWK:preferences.py:165')
    se_suppress_dup_vars: bpy.props.BoolProperty(
        name=_zh_native("Suppress Duplicate Variable Messages", 'MWK:preferences.py:168'),
        description=_zh_native("Maya: no warnings about redeclared MEL variables (the kit runs no MEL: kept for Maya's menu)", 'MWK:preferences.py:168'), translation_context='MWK:preferences.py:168')
    se_history_output: bpy.props.EnumProperty(
        name=_zh_native("History Output", 'MWK:preferences.py:171'), default='BOTH',
        items=_zh_enum((('BOTH', "Show Both", "Show both MEL and Python output in the history"),
               ('MEL', "Show MEL Only", "Show only MEL output in the history"),
               ('PYTHON', "Show Python Only", "Show only Python output in the history")), 'MWK:preferences.py:171'), translation_context='MWK:preferences.py:171')

    # Channel Box Channels > Sync Selection in Graph Editor / Sync Timeline Display (Maya optionVars, factory off;
    # Maya Channel Box Channels menu, ui/cb_channels.py, step 158).
    cb_sync_graph: bpy.props.BoolProperty(
        name=_zh_native("Sync Selection in Graph Editor", 'MWK:preferences.py:179'),
        description=_zh_native("Selecting channels in the Channel Box selects their curves, and S keys only the selected channels", 'MWK:preferences.py:179'), translation_context='MWK:preferences.py:179')
    cb_sync_timeline: bpy.props.BoolProperty(
        name=_zh_native("Sync Timeline Display", 'MWK:preferences.py:182'),
        description=_zh_native("The Time Slider shows only the keys of the channels selected in the Channel Box", 'MWK:preferences.py:182'), translation_context='MWK:preferences.py:182')
    # Graph Editor Select > Curve / Key / In Tangent / Out Tangent (Maya selectType pick masks, factory all on;
    # Maya Graph Editor Select menu, operators/graph_key_menu.py, step 157).
    graph_select_curve: bpy.props.BoolProperty(
        name=_zh_native("Curve", 'MWK:preferences.py:187'), default=True, description=_zh_native("Clicking or dragging in the Graph Editor can pick curves", 'MWK:preferences.py:187'), translation_context='MWK:preferences.py:187')
    graph_select_key: bpy.props.BoolProperty(
        name=_zh_native("Key", 'MWK:preferences.py:189'), default=True, description=_zh_native("Clicking or dragging in the Graph Editor can pick keys", 'MWK:preferences.py:189'), translation_context='MWK:preferences.py:189')
    graph_select_in: bpy.props.BoolProperty(
        name=_zh_native("In Tangent", 'MWK:preferences.py:191'), default=True, description=_zh_native("Clicking or dragging in the Graph Editor can pick in tangents", 'MWK:preferences.py:191'), translation_context='MWK:preferences.py:191')
    graph_select_out: bpy.props.BoolProperty(
        name=_zh_native("Out Tangent", 'MWK:preferences.py:193'), default=True, description=_zh_native("Clicking or dragging in the Graph Editor can pick out tangents", 'MWK:preferences.py:193'), translation_context='MWK:preferences.py:193')
    # Tangents > Default In / Out Tangent (Maya keyTangent -global, factory Auto / Auto):
    # the tangents of the keys the kit sets (S, Shift+W/E/R, Channel Box keys, Auto Key). Blender's own preference
    # is never written (#40).
    default_in_tangent: bpy.props.EnumProperty(
        name=_zh_native("Default In Tangent", 'MWK:preferences.py:198'), default='AUTO',
        items=_zh_enum((('AUTO', "Auto", "Maya Auto: Blender Auto Clamped"), ('SPLINE', "Spline", "Blender Auto"),
               ('LINEAR', "Linear", ""), ('CLAMPED', "Clamped", "Blender Auto Clamped"),
               ('FLAT', "Flat", "Level handles"), ('PLATEAU', "Plateau", "Blender Auto Clamped")), 'MWK:preferences.py:198'),
        description=_zh_native("In tangent of the keys the kit sets (Maya Tangents > Default In Tangent)", 'MWK:preferences.py:198'), translation_context='MWK:preferences.py:198')
    default_out_tangent: bpy.props.EnumProperty(
        name=_zh_native("Default Out Tangent", 'MWK:preferences.py:204'), default='AUTO',
        items=_zh_enum((('AUTO', "Auto", "Maya Auto: Blender Auto Clamped"), ('SPLINE', "Spline", "Blender Auto"),
               ('LINEAR', "Linear", ""), ('CLAMPED', "Clamped", "Blender Auto Clamped"),
               ('FLAT', "Flat", "Level handles"), ('PLATEAU', "Plateau", "Blender Auto Clamped"),
               ('STEPPED', "Stepped", "Blender Constant")), 'MWK:preferences.py:204'),
        description=_zh_native("Out tangent of the keys the kit sets (Maya Tangents > Default Out Tangent)", 'MWK:preferences.py:204'), translation_context='MWK:preferences.py:204')

    # Render > Test Resolution (Maya optionVar renderViewTestResolution, default Render Settings; step 152,
    # operators/render_batch.py): the size of Render Current Frame / Render Sequence.
    test_resolution: bpy.props.EnumProperty(
        name=_zh_native("Test Resolution", 'MWK:preferences.py:214'),
        items=_zh_enum((("PANEL", "Camera Panel", "The size of the 3D View"),
               ("SETTINGS", "Render Settings", "The Render Settings size"),
               ("10", "10%", ""), ("25", "25%", ""), ("50", "50%", ""), ("75", "75%", ""),
               ("110", "110%", ""), ("125", "125%", ""), ("150", "150%", "")), 'MWK:preferences.py:214'),
        default="SETTINGS",
        description=_zh_native("Maya Render > Test Resolution: the size of Render Current Frame / Render Sequence "
                    "(batch renders use the Render Settings size)", 'MWK:preferences.py:214'), translation_context='MWK:preferences.py:214')

    # Top UI (docs/steps/step_7.md; Maya Windows > UI Elements).
    maya_top_bar: bpy.props.BoolProperty(
        name=_zh_native("Maya Menu Bar", 'MWK:preferences.py:225'),
        description=_zh_native("Top bar shows the Maya menus, menu sets and Status Line instead of "
                    "Blender's menus and workspace tabs (Blender menus stay as submenus)", 'MWK:preferences.py:225'),
        default=True, translation_context='MWK:preferences.py:225')
    # Maya view furniture (docs/steps/step_46.md), in views whose Blender navigation gizmo is off.
    maya_viewcube: bpy.props.BoolProperty(
        name=_zh_native("ViewCube", 'MWK:preferences.py:231'), description=_zh_native("Maya ViewCube in the top right of the view (click a face to look "
                                     "along it)", 'MWK:preferences.py:231'), default=True, translation_context='MWK:preferences.py:231')
    maya_camera_names: bpy.props.BoolProperty(
        name=_zh_native("Camera Names", 'MWK:preferences.py:234'), description=_zh_native("Maya camera name (persp, top -Y, ...) at the bottom of the view", 'MWK:preferences.py:234'),
        default=True, translation_context='MWK:preferences.py:234')
    def _update_selection_wire(self, context):
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

    def _update_dock_colors(self, context):
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'PROPERTIES':
                    area.tag_redraw()

    # Maya wireframe on selected objects over shading (docs/steps/step_47.md).
    maya_selection_wire: bpy.props.BoolProperty(
        name=_zh_native("Selection Wireframe", 'MWK:preferences.py:250'), description=_zh_native("Selected objects show their wireframe over shading, like "
                                                "Maya (lead light green, others white); in wireframe shading "
                                                "unselected objects are Maya's dark blue", 'MWK:preferences.py:250'),
        default=True, update=_update_selection_wire, translation_context='MWK:preferences.py:250')
    # Maya component colours in mesh edit mode (docs/steps/step_134_sel.md).
    maya_component_colors: bpy.props.BoolProperty(
        name=_zh_native("Component Colors", 'MWK:preferences.py:256'), description=_zh_native("Mesh edit mode shows Maya's component colors: light blue edges, "
                                              "purple / yellow vertices, orange edges and stippled faces", 'MWK:preferences.py:256'),
        default=True, update=_update_selection_wire, translation_context='MWK:preferences.py:256')
    # Maya grey docks (step 195): the dock areas are lifted from the theme's Properties grey to Maya's #444444
    maya_dock_colors: bpy.props.BoolProperty(
        name=_zh_native("Dock Colors", 'MWK:preferences.py:261'), description=_zh_native("The Channel Box / Attribute Editor / Modeling Toolkit docks are drawn "
                                        "in Maya's lighter grey", 'MWK:preferences.py:261'),
        default=True, update=_update_dock_colors, translation_context='MWK:preferences.py:261')
    maya_view_axis: bpy.props.BoolProperty(
        name=_zh_native("View Axis", 'MWK:preferences.py:265'), description=_zh_native("Maya axis triad in the bottom left of the view", 'MWK:preferences.py:265'), default=True, translation_context='MWK:preferences.py:265')
    # Maya in-view messages (inViewMessageEnable 1; docs/steps/step_72.md).
    in_view_messages: bpy.props.BoolProperty(
        name=_zh_native("In-View Messages", 'MWK:preferences.py:268'), description=_zh_native("Short fading messages in the view when you group, hide, toggle "
                                             "object/component selection (F8), soft select or Make Live, like Maya", 'MWK:preferences.py:268'),
        default=True, translation_context='MWK:preferences.py:268')
    maya_panel_menus: bpy.props.BoolProperty(
        name=_zh_native("Panel Menus", 'MWK:preferences.py:272'),
        description=_zh_native("3D View headers show Maya's panel menus (View, Shading, Lighting, Show, Renderer, "
                    "Panels) instead of Blender's (Blender menus stay as a submenu)", 'MWK:preferences.py:272'),
        default=True, translation_context='MWK:preferences.py:272')
    menu_set: bpy.props.EnumProperty(
        name=_zh_native("Menu Set", 'MWK:preferences.py:277'), description=_zh_native("Maya menu set: which menus follow the common ones", 'MWK:preferences.py:277'),
        items=_zh_enum(lambda self, context: _menu_set_items(), 'MWK:preferences.py:277'), default=0, translation_context='MWK:preferences.py:277')
    show_status_line: bpy.props.BoolProperty(
        name=_zh_native("Status Line", 'MWK:preferences.py:280'), description=_zh_native("Maya Status Line icons in the top bar", 'MWK:preferences.py:280'), default=True, translation_context='MWK:preferences.py:280')
    # Maya layout parity (docs/steps/step_49.md).
    maya_toolbox: bpy.props.BoolProperty(
        name=_zh_native("Maya Tool Box", 'MWK:preferences.py:283'), description=_zh_native("3D View toolbars show Maya's Tool Box in every mode: Select, Lasso, "
                                          "Paint Select, Move, Rotate, Scale, the last other tool and quick layout "
                                          "buttons (other tools stay on keys, menus and the shelf)", 'MWK:preferences.py:283'),
        default=True, update=_update_selection_wire, translation_context='MWK:preferences.py:283')
    show_command_line: bpy.props.BoolProperty(
        name=_zh_native("Command Line", 'MWK:preferences.py:288'), description=_zh_native("Python command line in the status bar", 'MWK:preferences.py:288'), default=True, translation_context='MWK:preferences.py:288')
    show_help_line: bpy.props.BoolProperty(
        name=_zh_native("Help Line", 'MWK:preferences.py:290'), description=_zh_native("Maya-style help for the active tool in the status bar", 'MWK:preferences.py:290'),
        default=True, translation_context='MWK:preferences.py:290')

    # Marking menus and hotbox (docs/steps/step_9.md).
    marking_menu_style: bpy.props.EnumProperty(
        name=_zh_native("Marking Menus", 'MWK:preferences.py:295'),
        description=_zh_native("How Maya marking menus are shown", 'MWK:preferences.py:295'),
        items=_zh_enum((('ENGINE', "Maya Engine", "Maya-style marking menus: drag, flick, in-place submenus, "
                                          "option boxes"),
               ('PIE', "Blender Pies", "Blender pie menus (8 slots, submenus open new pies)")), 'MWK:preferences.py:295'),
        default='ENGINE', translation_context='MWK:preferences.py:295')
    hotbox_style: bpy.props.EnumProperty(
        name=_zh_native("Hotbox Style", 'MWK:preferences.py:302'),
        items=_zh_enum((('ALL', "Zones and Menu Rows", ""), ('ZONES', "Zones Only", ""),
               ('CENTER', "Center Zone Only", "")), 'MWK:preferences.py:302'),
        default='ALL', translation_context='MWK:preferences.py:302')
    hotbox_all_sets: bpy.props.BoolProperty(
        name=_zh_native("Show All Menu Sets", 'MWK:preferences.py:307'), description=_zh_native("Hotbox shows the menus of every menu set, not only "
                                               "the current one (Maya's default, step 52)", 'MWK:preferences.py:307'),
        default=True, translation_context='MWK:preferences.py:307')

    # Shelf (docs/steps/step_12.md): current tab (factory file name or "USER:<name>").
    shelf_current: bpy.props.StringProperty(options={'HIDDEN'}, translation_context='MWK:preferences.py:313')

    # Maya project (operators/project.py, docs/steps/step_69.md): Blender has no projects, so the current
    # project folder and the Recent Projects list live here, like Maya keeps the workspace in its prefs.
    project_root: bpy.props.StringProperty(name=_zh_native("Current Project", 'MWK:preferences.py:317'), subtype='DIR_PATH',
                                           description=_zh_native("Maya Workflow Kit project folder: file dialogs open in its scenes "
                                                       "folder, renders go to its images folder", 'MWK:preferences.py:317'), translation_context='MWK:preferences.py:317')
    recent_projects: bpy.props.StringProperty(options={'HIDDEN'}, translation_context='MWK:preferences.py:320')   # newline-separated, newest first
    # Maya option window values (operators/option_windows.py, step 103): Maya keeps them in optionVars.
    option_settings: bpy.props.StringProperty(options={'HIDDEN'}, translation_context='MWK:preferences.py:322')   # JSON {window key: {field: value}}

    # Scene concepts (docs/steps/step_10.md; docs/user_decisions.md #1, #2).
    parent_mode: bpy.props.EnumProperty(
        name=_zh_native("Parent Mode", 'MWK:preferences.py:325'), description=_zh_native("What P (Parent) does to the child's values", 'MWK:preferences.py:325'),
        items=_zh_enum((('MAYA', "Maya", "Keep the world position and recompute the local values "
                                "relative to the parent (parent inverse = identity)"),
               ('BLENDER', "Blender", "Keep the local values; Blender stores a hidden parent "
                                      "inverse matrix")), 'MWK:preferences.py:325'),
        default='MAYA', translation_context='MWK:preferences.py:325')
    maya_naming: bpy.props.BoolProperty(
        name=_zh_native("Maya Naming", 'MWK:preferences.py:332'), description=_zh_native("Create menu names objects pCube1 / pCubeShape1 "
                                        "(otherwise Blender names)", 'MWK:preferences.py:332'),
        default=True, translation_context='MWK:preferences.py:332')
    # Maya optionVar manipSmartDuplicate 1.
    smart_duplicate: bpy.props.BoolProperty(
        name=_zh_native("Smart Duplicate", 'MWK:preferences.py:337'), description=_zh_native("Shift+drag a Move/Rotate/Scale manipulator "
                                            "duplicates the selection and transforms the copy", 'MWK:preferences.py:337'),
        default=True, translation_context='MWK:preferences.py:337')
    # Maya optionVar manipSmartExtrude 1.
    smart_extrude: bpy.props.BoolProperty(
        name=_zh_native("Smart Extrude", 'MWK:preferences.py:342'), description=_zh_native("Shift+drag a Move/Rotate/Scale manipulator on faces "
                                          "or edges extrudes them and transforms the new ones", 'MWK:preferences.py:342'),
        default=True, translation_context='MWK:preferences.py:342')

    def _update_units(self, context):
        from .operators import units
        if self.maya_units:
            units.apply_file()
        else:
            units.restore_file()

    maya_units: bpy.props.BoolProperty(
        name=_zh_native("Maya Units (1 BU = 1 cm)", 'MWK:preferences.py:354'),
        description=_zh_native("Scene unit scale 0.01 with centimetres and Maya camera clipping "
                    "(0.1 - 10000) for this file and new files. Physics, light falloff and "
                    "importers assume 1 BU = 1 m. Turning it off restores the previous values", 'MWK:preferences.py:354'),
        default=False, update=_update_units, translation_context='MWK:preferences.py:354')

    def draw(self, context):
        layout = self.layout
        draw_about(layout)
        box = layout.box()
        row = box.row()
        row.scale_y = 1.6
        if self.maya_mode:
            row.operator("allset.switch_mode", text=_zh("Switch to Blender", 'MWK:preferences.py:368'), icon='BLENDER').mode = 'BLENDER'
        else:
            # Nothing is changed until the user asks for it (step 115): the same dialog as the first start.
            row.operator("allset.welcome", text=_zh("Make Blender feel like Maya", 'MWK:preferences.py:371'), icon='EVENT_M')
            row.operator("allset.switch_mode", text=_zh("Maya Mode Only", 'MWK:preferences.py:372')).mode = 'MAYA'
        box.label(text=_zh("Ctrl+Alt+Shift+M or the Maya / Blender switch at the right of the top bar switches at any time. "
                       "Blender's own preferences are never changed.", 'MWK:preferences.py:373'), icon='INFO')
        hint = undo_hint(context)
        emulate = emulate_hint(context)
        if hint or emulate:
            box.label(text=_zh("Recommended setup", 'MWK:preferences.py:378'), icon='LOOP_BACK')
        for text in (hint, emulate):
            if text:
                _wrapped(box, text)
        if not self.maya_mode:
            return
        box = layout.box()
        row = box.row()
        row.scale_y = 1.4
        row.operator("allset.new_maya_scene", icon='FILE_NEW')
        row.operator("allset.maya_layout_here", icon='WORKSPACE')
        box.prop(self, "start_in_maya_layout")
        box.prop(self, "maya_layout_on_open")
        col = layout.column()
        col.prop(self, "lock_ortho_tumble")
        col.prop(self, "select_through")
        col.prop(self, "preselect_highlight")
        col.prop(self, "select_priority")
        col.prop(self, "pick_walk_skip_hidden_collections")
        col.prop(self, "armature_mode_header")
        col.prop(self, "armature_mode_pulse")

        box = layout.box()
        box.label(text=_zh("Scene Concepts", 'MWK:preferences.py:401'))
        row = box.row()
        row.prop(self, "parent_mode")
        row.prop(self, "maya_naming")
        row = box.row()
        row.prop(self, "maya_units")
        row.prop(self, "smart_duplicate")
        row.prop(self, "smart_extrude")
        box.prop(self, "project_root")

        box = layout.box()
        box.label(text=_zh("UI Elements", 'MWK:preferences.py:412'))
        row = box.row()
        row.prop(self, "maya_top_bar")
        row.prop(self, "maya_panel_menus")
        row.prop(self, "menu_set", text="")
        row = box.row()
        row.prop(self, "marking_menu_style")
        row.prop(self, "hotbox_style", text="")
        row.prop(self, "hotbox_all_sets")
        row = box.row()
        row.prop(self, "show_status_line")
        row.prop(self, "show_command_line")
        row.prop(self, "show_help_line")
        row = box.row()
        row.prop(self, "maya_toolbox")
        row = box.row()
        row.prop(self, "maya_viewcube")
        row.prop(self, "maya_camera_names")
        row.prop(self, "maya_view_axis")
        row.prop(self, "maya_selection_wire")
        row.prop(self, "maya_component_colors")
        box.prop(self, "maya_dock_colors")
        box.prop(self, "in_view_messages")


# Step 111 (decision 12, docs/distribution/naming.md, docs/distribution/extensions_audit.md 「필수 고지문」)
# Undo depth (step 141, B6): Maya's undo queue is infinite, Blender keeps 32 steps
# by default and the kit may not write Blender's preferences (step 130), so the kit only tells the user (delegated).
UNDO_RECOMMENDED = 256      # Blender's maximum
UNDO_HINT = ("Maya's undo is unlimited; Blender keeps {steps} steps. For long Maya-style sessions raise Edit > "
             "Preferences > System > Memory & Limits > Undo Steps to 256 (Blender's maximum).")


EMULATE_HINT = ("Emulate 3 Button Mouse is on (Preferences > Input): Blender turns Alt+left drag into a middle drag "
                "before any key map sees it, so Maya's Alt+LMB tumble can't work. Turn it off for Maya navigation "
                "(Alt+MMB track and Alt+RMB dolly work either way).")


def emulate_hint(context=None):
    """Step 260 (#177): the Emulate 3 Button Mouse hint while that Blender preference is on, else None (read only:
    the kit never writes Blender's preferences, step 130). Blender converts Alt+LMB into a plain MMB without Alt
    (wm_event_system.cc wm_eventemulation, docs/steps/step_260_prep.md)."""
    inputs = (context or bpy.context).preferences.inputs
    return EMULATE_HINT if getattr(inputs, "use_mouse_emulate_3_button", False) else None


def undo_hint(context=None):
    """The undo-depth hint while Blender's Undo Steps is below 256, else None (read only, nothing is written)."""
    steps = (context or bpy.context).preferences.edit.undo_steps
    return UNDO_HINT.format(steps=steps) if steps < UNDO_RECOMMENDED else None


ABOUT = ("Other tools give you one piece at a time: a pivot, a keymap, a shelf, a theme. Maya Workflow Kit brings the whole Maya "
         "workflow into Blender in one install: hotbox and marking menus, Channel Box, Attribute Editor, Outliner, "
         "menu sets, shelves, option windows, Freeze / History concepts, centimetre units and pCube1-style naming.")
TRADEMARK_NOTICE = (
    "Autodesk and Maya are registered trademarks or trademarks of Autodesk, Inc., and/or its subsidiaries and/or "
    "affiliates in the USA and/or other countries. This project is an independent, free and open-source (GPL) "
    "extension for Blender. It is not affiliated with, endorsed by, sponsored by, or otherwise approved by Autodesk, "
    "Inc. or the Blender Foundation. It contains no Autodesk code, icons, MEL scripts or other Autodesk assets; "
    "references to Maya are solely to describe compatibility and the intended audience.")


def _wrapped(layout, text, width=110):
    import unicodedata
    text = _zh(text, 'MWK:preferences.py:477')
    if any('\u3400' <= char <= '\u9fff' for char in text):
        col = layout.column(align=True)
        line, used = '', 0
        for char in text:
            cells = 2 if unicodedata.east_asian_width(char) in {'W', 'F'} else 1
            if char == '\n' or used + cells > width:
                col.label(text=_zh(line, 'MWK:preferences.py:484'))
                line, used = '', 0
                if char == '\n':
                    continue
            line += char
            used += cells
        if line:
            col.label(text=_zh(line, 'MWK:preferences.py:491'))
        return
    line = ""
    col = layout.column(align=True)
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            col.label(text=_zh(line, 'MWK:preferences.py:497'))
            line = word
        else:
            line = f"{line} {word}" if line else word
    if line:
        col.label(text=_zh(line, 'MWK:preferences.py:502'))


def draw_about(layout):
    """The About box of the preferences: what Maya Workflow Kit is, and the trademark notice."""
    box = layout.box()
    box.label(text=_zh("Maya Workflow Kit: the whole Maya workflow in Blender, in one install", 'MWK:preferences.py:508'), icon='INFO')
    _wrapped(box, ABOUT)
    sub = box.column()
    sub.scale_y = 0.8
    sub.enabled = False
    _wrapped(sub, TRADEMARK_NOTICE)


_SET_ITEMS = []


def _menu_set_items():
    # Kept in a module list: Blender needs the enum item strings to stay referenced.
    if not _SET_ITEMS:
        from .ui import menu_sets
        _SET_ITEMS.extend(menu_sets.SET_ITEMS)
    return _SET_ITEMS


classes = (ALLSET_AddonPreferences,)

register, unregister = bpy.utils.register_classes_factory(classes)


def get(context=None):
    """Return this add-on's preferences instance."""
    context = context or bpy.context
    return context.preferences.addons[__package__].preferences

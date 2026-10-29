# Maya Workflow Kit for Blender — Simplified Chinese localization

An independent community localization of [Maya Workflow Kit by ohnsk / 5hyuns](https://github.com/5hyuns/maya-workflow-kit-for-blender).

Chinese UI is enabled only when Blender uses Simplified Chinese (`zh_HANS`) and interface translation is enabled. Switching back to English restores English captions without restarting the extension. Internal commands, enum IDs, node names, scene data, and user-authored shelf names remain unchanged.

Download the installable ZIP from this repository's Releases, then use Blender Preferences → Get Extensions → Install from Disk. The extension ID remains `allset`; do not enable upstream and localized versions together.

Supported manifest range: Blender 4.5 through 5.2. Localization checks ran on Blender 5.1.0 and 5.2.2; 4.5 and every possible GUI state have not been retested. This is a workflow adapter, not a Maya scene-file reader or MEL runtime.

Build locally with `python tools/build.py`. Source provenance and modification scope are documented in [UPSTREAM.json](UPSTREAM.json) and [LOCALIZATION.md](LOCALIZATION.md). The source snapshot retains full extension code but does not include upstream Git history, marketing website, or all upstream development tools/tests.

Code: GPL-3.0-or-later. Original non-code extension assets: CC0-1.0 as specified in [ASSETS_LICENSE.txt](src/allset/ASSETS_LICENSE.txt). Original author attribution is retained. This project is not affiliated with Autodesk or the Blender Foundation.

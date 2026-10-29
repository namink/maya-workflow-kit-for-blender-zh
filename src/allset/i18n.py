# Simplified Chinese localization and language switching modified by namink, 2026-10-29.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Simplified Chinese presentation helpers. Command paths and RNA identifiers stay English."""
import ast
from functools import wraps
import json
from pathlib import Path
import re
from string import Formatter

NATIVE_CONTEXT = 'MayaWorkflowKit'
_CATALOG_PATH = Path(__file__).with_name('translations_zh_HANS.json')
_REGISTRY_NAME = __name__ + '.native'
_FORMATTER = Formatter()
_messages, _contexts, _template_cache = {}, {}, {}
_native_texts, _enum_references = {}, {}
_loaded = _registered = _dirty = False
_batch_depth = 0
_SAFE_UI_FIELDS = frozenset({'plural', 'unit_label', 'component_label', 'mode_label',
                            'window.title', 'window.action', 'window.apply_text',
                            'f.label', 'f.heading', 'f.text'})


def _blender():
    try:
        import bpy
        return bpy
    except ImportError:
        return None


def is_chinese():
    """Read live interface preferences; never enable for Traditional Chinese."""
    bpy = _blender()
    if bpy is None:
        return False
    try:
        view = bpy.context.preferences.view
        if not view.use_translate_interface:
            return False
        language = view.language
        if language == 'DEFAULT':
            language = bpy.app.translations.locale
        language = str(language).split('.', 1)[0].replace('-', '_').casefold()
        return language in {'zh_hans', 'zh_cn'}
    except (AttributeError, ReferenceError, RuntimeError):
        return False


def _load_catalog(force=False):
    global _messages, _contexts, _loaded
    if _loaded and not force:
        return
    try:
        data = json.loads(_CATALOG_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        data = {}
    _messages = {key: value for key, value in data.get('messages', {}).items()
                 if isinstance(key, str) and isinstance(value, str)}
    _contexts = {context: {key: value for key, value in values.items()
                          if isinstance(key, str) and isinstance(value, str)}
                 for context, values in data.get('contexts', {}).items()
                 if isinstance(context, str) and isinstance(values, dict)}
    _loaded = True
    _template_cache.clear()


def _lookup(text, context=None):
    """Language-independent exact lookup, including native metadata setup."""
    _load_catalog()
    return _contexts.get(context, {}).get(text, _messages.get(text, text))


def _static_choices(node):
    """Read literal conditional alternatives without executing expressions."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return (node.value,)
    if isinstance(node, ast.IfExp):
        left, right = _static_choices(node.body), _static_choices(node.orelse)
        if left is not None and right is not None:
            return left + right
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _static_choices(node.left), _static_choices(node.right)
        if left is not None and right is not None and len(left) * len(right) <= 32:
            return tuple(a + b for a in left for b in right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and not node.args and not node.keywords:
        values = _static_choices(node.func.value)
        if values is not None and node.func.attr in {'upper', 'lower', 'title', 'capitalize'}:
            return tuple(getattr(value, node.func.attr)() for value in values)
    return None


def _choices(field):
    try:
        return _static_choices(ast.parse(field, mode='eval').body)
    except (SyntaxError, ValueError, RecursionError):
        return None


def _quoted_end(text, start):
    quote = text[start]
    marker = quote * 3 if text.startswith(quote * 3, start) else quote
    pos = start + len(marker)
    while pos < len(text):
        if text[pos] == '\\':
            pos += 2
        elif text.startswith(marker, pos):
            return pos + len(marker)
        else:
            pos += 1
    raise ValueError('unterminated string in template field')


def _split_field(content):
    """Split a field outside Python strings/brackets, without evaluating it."""
    pos, depth = 0, 0
    while pos < len(content):
        char = content[pos]
        if char in {'"', "'"}:
            pos = _quoted_end(content, pos)
            continue
        if char in '([{':
            depth += 1
        elif char in ')]}':
            depth -= 1
        elif depth == 0 and char == ':':
            return content[:pos], content[pos + 1:], None
        elif depth == 0 and char == '!' and pos + 1 < len(content) and content[pos + 1] in 'rsa':
            after = content[pos + 2:]
            if not after or after.startswith(':'):
                return content[:pos], after[1:] if after else '', content[pos + 1]
        pos += 1
    return content, '', None


def _parse(text):
    """Parse format fields, including nested f-string expressions, without eval."""
    if not isinstance(text, str):
        return ()
    parts, literal = [], []
    pos, automatic = 0, 0
    try:
        while pos < len(text):
            if text.startswith('{{', pos):
                literal.append('{'); pos += 2
            elif text.startswith('}}', pos):
                literal.append('}'); pos += 2
            elif text[pos] == '}':
                raise ValueError('unmatched closing brace')
            elif text[pos] == '{':
                start, end, depth = pos + 1, pos + 1, 1
                while end < len(text) and depth:
                    if text[end] in {'"', "'"}:
                        end = _quoted_end(text, end)
                        continue
                    if text[end] == '{': depth += 1
                    elif text[end] == '}': depth -= 1
                    if depth: end += 1
                if depth:
                    raise ValueError('unmatched opening brace')
                name, spec, conversion = _split_field(text[start:end])
                if not name:
                    name = str(automatic); automatic += 1
                parts.append((''.join(literal), name, spec, conversion))
                literal = []; pos = end + 1
            else:
                literal.append(text[pos]); pos += 1
        if literal or not parts:
            parts.append((''.join(literal), None, None, None))
        return tuple(parts)
    except (ValueError, IndexError):
        return ()


def _branch_signature(field):
    """Ignore only output branch wording; keep tests and data expressions exact."""
    try:
        node = ast.parse(field, mode='eval').body
    except (SyntaxError, ValueError):
        return None
    def signature(value):
        if isinstance(value, ast.IfExp):
            return ('if', ast.dump(value.test), signature(value.body), signature(value.orelse))
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return ('text',)
        if isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
            return ('add', signature(value.left), signature(value.right))
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) and not value.args and not value.keywords:
            return ('call', value.func.attr, signature(value.func.value))
        return ('expression', ast.dump(value))
    return signature(node)


def _field_key(name, spec, conversion):
    return name, spec or '', conversion or ''


class _Template:
    __slots__ = ('pattern', 'source_fields', 'target', 'score', 'menu_labels')

    def __init__(self, source, translated):
        source_parts, target_parts = _parse(source), _parse(translated)
        if not source_parts or not target_parts:
            raise ValueError('invalid template')
        literals = ''.join(part[0] for part in source_parts)
        # Pure data/name templates must not catch arbitrary user strings.
        if len(re.findall(r'[A-Za-z\u3400-\u9fff]', literals)) < 3:
            raise ValueError('data-only template')
        chunks, fields = [], []
        for literal, name, spec, conversion in source_parts:
            chunks.append(re.escape(literal))
            if name is not None:
                choices = _choices(name)
                choice_pattern = '|'.join(re.escape(value) for value in sorted(choices, key=len, reverse=True)) if choices else None
                chunks.append('(' + (choice_pattern if choice_pattern is not None else '.*?') + ')')
                fields.append((_field_key(name, spec, conversion), choices))
        if not fields:
            raise ValueError('no fields')
        self.pattern = re.compile(r'\A' + ''.join(chunks) + r'\Z', re.DOTALL)
        self.source_fields, self.score = tuple(fields), len(literals)
        self.menu_labels = 'menu set' in literals.casefold()
        target, used = [], set()
        for literal, name, spec, conversion in target_parts:
            if name is None:
                target.append((literal, None, None)); continue
            choices = _choices(name)
            exact_key = _field_key(name, spec, conversion)
            matches = [i for i, (key, _) in enumerate(fields) if key == exact_key]
            if not matches:
                matches = [i for i, (key, _) in enumerate(fields) if key[0] == name]
            if not matches and choices is not None:
                sig = _branch_signature(name)
                matches = [i for i, (key, values) in enumerate(fields)
                           if values is not None and _branch_signature(key[0]) == sig]
            if not matches:
                raise ValueError('unknown target field')
            index = matches[0]; used.add(index)
            source_choices = fields[index][1]
            mapping = None
            if source_choices is not None and choices is not None:
                if len(source_choices) != len(choices):
                    raise ValueError('conditional branch count changed')
                mapping = {}
                for english, chinese in zip(source_choices, choices):
                    if english in mapping and mapping[english] != chinese:
                        raise ValueError('ambiguous literal branches')
                    mapping[english] = chinese
            target.append((literal, index, mapping))
        for index, (key, choices) in enumerate(fields):
            if index not in used and not (choices is not None and set(choices) <= {'', 's', 'es'}):
                # A translated sentence may omit an English plural suffix, not
                # a name, path, value or any other runtime data.
                if not any(fields[other][0] == key for other in used):
                    raise ValueError('runtime data field omitted')
        self.target = tuple(target)

    def render(self, text, context):
        match = self.pattern.fullmatch(text)
        if match is None:
            return None
        exact, values = {}, list(match.groups())
        for ((key, _), value) in zip(self.source_fields, values):
            if key in exact and exact[key] != value:
                return None
            exact[key] = value
        result = []
        for literal, index, mapping in self.target:
            result.append(literal)
            if index is not None:
                key, choices = self.source_fields[index]
                value = values[index]
                if mapping is not None and value in mapping:
                    value = mapping[value]
                    if value in (choices or ()):
                        value = _lookup(value, context)
                elif key[0] in _SAFE_UI_FIELDS or (self.menu_labels and key[0] == 'label'):
                    value = _translate(value, context)
                result.append(value)
        return ''.join(result)


def _templates(context):
    if context not in _template_cache:
        table = _contexts.get(context, {}) if context is not None else _messages
        templates = []
        for source, translated in table.items():
            if '{' not in source:
                continue
            if source == translated and not any(name in _SAFE_UI_FIELDS for _, name, _, _ in _parse(source)):
                continue
            try:
                templates.append(_Template(source, translated))
            except (ValueError, re.error):
                continue
        templates.sort(key=lambda template: template.score, reverse=True)
        _template_cache[context] = tuple(templates)
    return _template_cache[context]


def _translate(text, context=None):
    """Language-independent exact and rendered-template lookup."""
    if not isinstance(text, str) or not text:
        return text
    _load_catalog()
    local = _contexts.get(context, {})
    if text in local:
        return local[text]
    if context is not None:
        for template in _templates(context):
            rendered = template.render(text, context)
            if rendered is not None:
                return rendered
    if text in _messages:
        return _messages[text]
    for template in _templates(None):
        rendered = template.render(text, context)
        if rendered is not None:
            return rendered
    return text


def tr(text, context=None):
    """Translate exact UI sentences only while Simplified Chinese UI is active."""
    return _translate(text, context) if is_chinese() else text


def format_text(template, *args, context=None, **values):
    """Translate a literal template before formatting data; never use eval."""
    translated = _lookup(template, context) if is_chinese() else template
    return translated.format(*args, **values)


def _schedule_refresh():
    if not _registered or _batch_depth:
        return
    bpy = _blender()
    if bpy is None:
        return
    try:
        timers = bpy.app.timers
        if not timers.is_registered(_flush_timer):
            timers.register(_flush_timer, first_interval=0.0)
    except (AttributeError, RuntimeError):
        refresh()


def native(text, context=NATIVE_CONTEXT):
    """Return English metadata and collect its native custom-context mapping."""
    global _dirty
    if not isinstance(text, str) or not text:
        return text
    context = context or NATIVE_CONTEXT
    texts = _native_texts.setdefault(context, set())
    if text not in texts:
        texts.add(text)
        _dirty = True
        _schedule_refresh()
    return text


def _remember_items(items, context, reference_key):
    global _batch_depth
    _batch_depth += 1
    try:
        result = []
        for item in items:
            if item is None:
                result.append(None)
            elif isinstance(item, (tuple, list)) and len(item) >= 3:
                result.append((item[0], native(item[1], context), native(item[2], context), *item[3:]))
            else:
                result.append(item)
        # Blender borrows enum strings: keep tuples and strings alive.
        _enum_references[reference_key] = result
        return result
    finally:
        _batch_depth -= 1
        if not _batch_depth and _dirty:
            _schedule_refresh()


def enum_items(items, context=None):
    """Keep English identifiers/captions for static and callback enums."""
    context = context or NATIVE_CONTEXT
    if callable(items):
        @wraps(items)
        def callback(self, blender_context):
            # Blender validates co_argcount in C; *args would appear to take
            # zero parameters even when functools.wraps exposes a signature.
            values = items(self, blender_context)
            return None if values is None else _remember_items(values, context, ('callback', id(callback)))
        return callback
    return _remember_items(items, context, ('static', context, id(items)))


def _dictionary():
    _load_catalog()
    translated = {(NATIVE_CONTEXT, text): value for text, value in _messages.items()}
    for context, texts in _native_texts.items():
        for text in texts:
            translated[(context, text)] = _translate(text, context)
    return {'zh_HANS': translated, 'zh_CN': dict(translated)}


def _flush_timer():
    if _registered and _dirty:
        refresh()
    return None


def refresh():
    """Flush native entries, including entries gathered by late enum callbacks."""
    global _registered, _dirty
    bpy = _blender()
    if bpy is None or not _registered:
        return
    dictionary = _dictionary()
    bpy.app.translations.unregister(_REGISTRY_NAME)
    _registered = False
    bpy.app.translations.register(_REGISTRY_NAME, dictionary)
    _registered, _dirty = True, False


def register():
    global _registered, _dirty
    bpy = _blender()
    if bpy is None:
        return
    _load_catalog(force=True)
    if _registered:
        refresh()
        return
    bpy.app.translations.register(_REGISTRY_NAME, _dictionary())
    _registered, _dirty = True, False


def unregister():
    global _registered, _dirty
    bpy = _blender()
    if bpy is None:
        _registered = False
        return
    try:
        if bpy.app.timers.is_registered(_flush_timer):
            bpy.app.timers.unregister(_flush_timer)
    except (AttributeError, RuntimeError):
        pass
    if _registered:
        bpy.app.translations.unregister(_REGISTRY_NAME)
    _registered, _dirty = False, bool(_native_texts)
    # Keep English metadata across disable/re-enable of cached modules.

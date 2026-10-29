"""Validated local backups. Credentials/settings are deliberately excluded."""
import copy
import json
import math
import safeio
import engine


def _number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def validate(data):
    if not isinstance(data, dict) or data.get('schema') != 1:
        raise ValueError('Unsupported backup format')
    if not isinstance(data.get('builds'), list) or not isinstance(data.get('items'), list):
        raise ValueError('Missing builds or items')
    ids = set()
    for item in data['items']:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id'] or item['id'] in ids:
            raise ValueError('Invalid/duplicate item identifier')
        ids.add(item['id'])
        if item.get('slot') not in engine.ALL_SLOTS or item.get('kind') not in ('gear', 'weapon'):
            raise ValueError('Invalid item type')
        attrs = item.get('attrs')
        if not isinstance(attrs, dict) or any(not _number(v) for v in attrs.values()):
            raise ValueError('Invalid attributes')
    for build in data['builds']:
        if not isinstance(build, dict) or not isinstance(build.get('name'), str) or not build['name'].strip():
            raise ValueError('Invalid build')
        if not isinstance(build.get('attributes', {}), dict) or not isinstance(build.get('talents', {}), dict):
            raise ValueError('Invalid build requirements')
        for rule in build.get('attributes', {}).values():
            if not isinstance(rule, dict) or any(not _number(rule[k]) for k in ('weight', 'good_at') if k in rule):
                raise ValueError('Invalid attribute requirement')
        if any(not _number(v) for v in build.get('talents', {}).values()):
            raise ValueError('Invalid talent weights')
        if not isinstance(build.get('sets_or_brands', []), list):
            raise ValueError('Invalid set requirements')
    return copy.deepcopy(data)


def save(path, builds, items):
    data = validate({'schema': 1, 'builds': builds, 'items': items})
    safeio.write_json(path, data, indent=2)


def load(path):
    with open(path, encoding='utf-8') as stream:
        return validate(json.load(stream))


def restore(data, cfg, stash, save_cfg):
    """Restore both stores; recover old contents if either persistence step fails.

    The caller keeps a durable pre-restore bundle for power-loss recovery.
    """
    data = validate(data)
    old_builds, old_items = copy.deepcopy(cfg['builds']), copy.deepcopy(stash.items)
    cfg['builds'], stash.data['items'] = data['builds'], data['items']
    try:
        save_cfg(cfg)
        stash.save()
    except Exception as error:
        cfg['builds'], stash.data['items'] = old_builds, old_items
        failures = []
        for persist in (lambda: save_cfg(cfg), stash.save):
            try:
                persist()
            except Exception as recovery_error:
                failures.append(str(recovery_error))
        if failures:
            raise RuntimeError('Restore failed; recover from pre_restore_backup.json: ' + '; '.join(failures)) from error
        raise

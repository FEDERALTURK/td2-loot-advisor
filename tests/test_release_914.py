import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backup_bundle
import updater
import stash


class BackupReleaseTests(unittest.TestCase):
    def test_empty_stash_set_build_has_a_valid_plan(self):
        plan = {slot: {'kind': 'set' if i < 4 else 'any', 'source': ["Striker's Battlegear"], 'attrs': []}
                for i, slot in enumerate(stash.GEAR)}
        result = stash.optimize({'name': 'Empty'}, plan, [])
        self.assertEqual(result['completion'], 0)
        self.assertEqual(result['done'], 0)
        self.assertEqual(len(result['set_slots']), 4)
    def bundle(self):
        return {'schema': 1, 'builds': [{'name': 'New', 'attributes': {}, 'talents': {}}],
                'items': [{'id': 'one', 'kind': 'weapon', 'slot': 'Weapon', 'attrs': {'health_damage': 21}}]}

    def test_rejects_duplicate_ids(self):
        data = self.bundle()
        data['items'] *= 2
        with self.assertRaises(ValueError): backup_bundle.validate(data)

    def test_rejects_nonfinite_attributes(self):
        for value in (float('nan'), float('inf'), True, '21'):
            data = self.bundle()
            data['items'][0]['attrs']['health_damage'] = value
            with self.assertRaises(ValueError): backup_bundle.validate(data)

    def test_second_write_failure_rolls_back_both_stores(self):
        cfg = {'builds': [{'name': 'Old'}], 'settings': {'untouched': True}}
        store = Mock()
        store.items = [{'id': 'old'}]
        store.data = {'items': store.items}
        store.save.side_effect = [OSError('disk failure'), None]
        original = copy.deepcopy(cfg)
        writes = []
        with self.assertRaises(OSError):
            backup_bundle.restore(self.bundle(), cfg, store, lambda c: writes.append(copy.deepcopy(c)))
        self.assertEqual(cfg, original)
        self.assertEqual(store.data['items'], [{'id': 'old'}])
        self.assertEqual(writes[-1], original)

    def test_source_update_allows_product_art_only(self):
        self.assertTrue(updater._allowed('art/agents/field_agent.png'))
        for path in ('builds.json', 'stash.json', 'private/token.json', 'art/videos/custom.mp4', 'art/agents/../../builds.json'):
            self.assertFalse(updater._allowed(path))


if __name__ == '__main__': unittest.main()

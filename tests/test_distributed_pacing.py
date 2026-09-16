"""Coverage and budget checks for WTS 0.2's compiled operation pacing."""
import copy
import json
import random
import unittest
from pathlib import Path

from workflow_helpers import ROOT, build, load_builder, stable

ATOMS = {'page.click', 'page.fill', 'page.press', 'page.extract', 'page.extract_list'}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def remove_pacing(value):
    if isinstance(value, list):
        return [remove_pacing(x) for x in value if not isinstance(x, dict) or not x.get('id', '').startswith('pacing-')]
    if isinstance(value, dict):
        result = {k: remove_pacing(v) for k, v in value.items() if k not in ('after_ms', 'delay_after_ms')}
        if result.get('action') == 'tabs.foreach':
            result['open'].pop('program', None)
            result['open']['timeout_ms'] = 15000
        return result
    return value


def indexed_milliseconds(node, index):
    if node['op'] == 'page.wait':
        return node['until']['ms']
    branch = node['then'] if index == node['condition']['value'] else node['else']
    return indexed_milliseconds(branch[0], index)


class DistributedPacingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = load_builder('versions/wts-v0-1')
        cls.modules = [load_builder('source/wts'), load_builder('versions/wts-v0-2')]

    def assert_coverage(self, value):
        if isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict) and item.get('op') in ATOMS:
                    self.assertGreater(index, 0)
                    self.assertTrue(value[index - 1]['id'].startswith('pacing-before-'))
                    self.assertNotIn('after_ms', item)
                self.assert_coverage(item)
        elif isinstance(value, dict):
            for child in value.values():
                self.assert_coverage(child)

    def test_all_workflows_preserve_business_logic_and_cover_operations(self):
        for module in self.modules:
            for kind, iteration, plan in (
                ('preflight', 0, {}),
                ('probe', 1, {'anchor': 'Python', 'companies': ['公司甲', '公司乙', '公司丙']}),
                *[('search', i, {'primary_query': 'Python', **({'secondary_query': 'Python API'} if i > 1 else {})}) for i in (1, 2, 3)],
                ('search', 2, {'primary_query': 'Python', 'limits': {'primary_max_details': 0}}),
                ('search', 2, {'primary_query': 'Python', 'site_filters': {'education': ['master'], 'current_cities': ['北京']}}),
            ):
                with self.subTest(skill=module.SKILL_NAME, kind=kind, iteration=iteration, plan=plan):
                    new = build(module, kind, iteration, plan)
                    old = build(self.old, kind, iteration, plan)
                    self.assertEqual(remove_pacing(stable(new)), remove_pacing(stable(old)))
                    self.assert_coverage(new)
                    self.assertNotIn('wait-before-detail-open', json.dumps(new))
                    for index, step in enumerate(new['steps']):
                        if step['action'] == 'page.navigate':
                            following = new['steps'][index + 1]['program']
                            self.assertEqual(following[0]['op'], 'page.detect')
                            self.assertEqual(following[1]['id'], 'pacing-after-' + step['id'])

    def test_detail_budget_and_per_candidate_variation(self):
        for module in self.modules:
            for base in (800, 1200, 5000):
                workflow = build(module, plan={'primary_query': 'Python', 'secondary_query': 'Python API', 'action_delay_ms': base})
                for collector in [s for s in workflow['steps'] if s['action'] == 'tabs.foreach']:
                    programs = [collector['open']['pre_program'], collector['open']['program'], collector['steps'][0]['program']]
                    selectors = [node for program in programs for node in program if node.get('id', '').startswith('pacing-before-')]
                    self.assertEqual(len(selectors), 3)
                    rows = [[indexed_milliseconds(node, i) for node in selectors] for i in range(collector['max_items'])]
                    for row in rows:
                        self.assertEqual(sum(row), 15000)
                        self.assertTrue(all(4000 <= ms <= 6000 for ms in row))
                    self.assertGreater(len({tuple(row) for row in rows}), 1)
                    self.assertLessEqual(collector['open']['timeout_ms'], 120000)

    def test_jitter_balance_is_bounded_across_seeds(self):
        from pacing import split_budget
        for seed in range(100):
            row = split_budget(3, random.Random(seed))
            self.assertEqual(sum(row), 15000)
            self.assertTrue(all(4000 <= ms <= 6000 for ms in row))

    def test_basic_delays_with_no_details_and_custom_baseline(self):
        for base in (800, 1200, 5000):
            workflow = build(self.modules[0], plan={'primary_query': 'Python', 'action_delay_ms': base, 'limits': {'primary_max_details': 0}})
            waits = [node['until']['ms'] for node in walk(workflow)
                     if node.get('op') == 'page.wait' and node.get('until', {}).get('type') == 'delay']
            self.assertGreater(len(waits), 2)
            self.assertTrue(all(round(base * .8) <= ms <= round(base * 1.2) for ms in waits))
            self.assertGreater(len(set(waits)), 1)

    def test_fifteen_detail_total_stays_close_to_fixed_proposal(self):
        # Three normal primary-only paths, five details each, no optional filter
        # cleanup/restoration. Excludes page/network time and separate probes.
        total = 0
        for iteration in (1, 2, 3):
            workflow = build(self.modules[0], iteration=iteration, plan={'primary_query': 'Python'})
            mandatory = {
                'pacing-after-primary-open-channel-search',
                'pacing-before-primary-fill-keyword',
                'pacing-before-primary-submit-keyword',
                'pacing-before-primary-extract-current-page-cards',
            }
            waits = {node['id']: node['until']['ms'] for node in walk(workflow)
                     if node.get('id') in mandatory}
            self.assertEqual(set(waits), mandatory)
            total += 5 * 15000 + sum(waits.values()) - 1200
        self.assertGreaterEqual(total, 232920)
        self.assertLessEqual(total, 238680)

    def test_agent_cannot_override_detail_budget(self):
        for module in self.modules:
            with self.assertRaisesRegex(ValueError, '未知字段'):
                build(module, plan={'primary_query': 'Python', 'detail_open_delay_ms': 0})

    def test_package_contains_matching_pacing_module_and_no_old_identity(self):
        source, package = self.modules
        self.assertEqual(package.SKILL_NAME, 'wts-v0-2')
        self.assertEqual(package.SKILL_VERSION, '0.2')
        self.assertEqual(source.load_assets(), package.load_assets())
        self.assertEqual((ROOT / 'source/wts/scripts/pacing.py').read_bytes(),
                         (ROOT / 'versions/wts-v0-2/scripts/pacing.py').read_bytes())
        for path in (ROOT / 'versions/wts-v0-2').rglob('*'):
            if path.is_file() and path.suffix in ('.md', '.yaml', '.py'):
                text = path.read_text()
                self.assertNotIn('/wts/', text)
                self.assertNotIn('/Users/chengxia/', text)
                self.assertNotIn('/BUILTIN_SKILLS_DIR/', text)


if __name__ == '__main__':
    unittest.main()

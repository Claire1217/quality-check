import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest
import summarize_trials as s


def record(model='a', repeat=1, task='one', **overrides):
    row = dict(run_id=f'{task}-{model}-{repeat}', dataset_id='dataset', task_id=task,
        task_version='hash', protocol_id='p1', model_id=model, role='solver', attempt=1,
        repeat_index=repeat, selected_for_summary=True, valid_for_comparison=True,
        status='completed', metric_id='reward', metric_kind='binary', score_direction='higher',
        score=0, passed=False, pass_rule_id='reward==1', times_seconds={'agent': 3},
        evidence={'raw_result': 'path'}, custom_evidence={'keep': True})
    row.update(overrides)
    return row


def complete(model='a', task='one'):
    return [record(model, i, task, passed=i == 2, score=int(i == 2)) for i in range(1, 5)]


def summary(rows):
    s.validate(rows)
    return s.summarize(rows, ['a', 'b'], ['a', 'b'])


class Pass4Tests(unittest.TestCase):
    def test_complete_and_pair(self):
        g = summary(complete('a') + complete('b'))['groups'][0]
        self.assertEqual(g['models']['a']['pass_at_4'], 1)
        self.assertEqual(g['models']['a']['pass_rate'], .25)
        self.assertEqual(g['paired_models']['both_pass_at_4_rate'], 1)

    def test_missing_cannot_count_even_if_passed(self):
        g = summary(complete()[:2])['groups'][0]
        self.assertIsNone(g['models']['a']['pass_at_4'])
        self.assertEqual(g['models']['a']['missing_selected_slots_in_observed_tasks'], 2)
        self.assertEqual(g['models']['b']['missing_selected_slots_in_observed_tasks'], 4)
        self.assertEqual(g['observed_task_versions'], 1)

    def test_retry_is_not_repeat(self):
        rows = complete()
        rows[0]['attempt'] = 2
        prior = record(run_id='original-failed', selected_for_summary=False,
                       status='infra_error', valid_for_comparison=False, score=None, passed=None)
        g = summary(rows + [prior])['groups'][0]['models']['a']
        self.assertEqual(g['all_attempt_records'], 5)
        self.assertEqual(g['selected_records'], 4)
        self.assertEqual(g['pass_at_4'], 1)
        duplicate = record(run_id='duplicate', attempt=3)
        with self.assertRaises(ValueError): summary(rows + [duplicate])

    def test_infra_invalidates_completeness(self):
        rows = complete()
        rows[3].update(status='api_error', valid_for_comparison=False, score=None, passed=None)
        m = summary(rows)['groups'][0]['models']['a']
        self.assertIsNone(m['pass_at_4'])
        self.assertEqual(m['invalid_or_unscored_selected_slots'], 1)
        rows[3]['valid_for_comparison'] = True
        with self.assertRaises(ValueError): summary(rows)

    def test_protocol_and_version_cannot_fill_missing_repeats(self):
        rows = complete()
        rows[3]['protocol_id'] = 'p2'
        out = summary(rows)
        self.assertEqual(len(out['groups']), 2)
        self.assertTrue(all(g['models']['a']['pass_at_4'] is None for g in out['groups']))
        rows[3]['protocol_id'] = 'p1'
        rows[3]['task_version'] = 'other'
        self.assertEqual(summary(rows)['groups'][0]['models']['a']['pass_at_4_eligible_tasks'], 0)

    def test_no_threshold(self):
        rows = complete('a') + complete('b')
        for r in rows: r.update(metric_kind='continuous', passed=None, pass_rule_id=None)
        g = summary(rows)['groups'][0]
        self.assertIsNone(g['models']['a']['pass_at_4'])
        self.assertIsNone(g['paired_models']['both_pass_at_4_rate'])
        self.assertEqual(g['paired_models']['complete_scored_pairs_without_pass_rule'], 1)

    def test_only_unselected_attempt_still_visible(self):
        row = record(selected_for_summary=False)
        m = summary([row])['groups'][0]['models']['a']
        self.assertEqual(m['all_attempt_records'], 1)
        self.assertEqual(m['missing_selected_slots_in_observed_tasks'], 4)
        self.assertEqual(summary([])['groups'], [])

    def test_repeat_required_and_bounded(self):
        for value in [None, 0, 5, True, '1']:
            with self.assertRaises(ValueError): summary([record(repeat_index=value)])

    def test_export_preserves_every_attempt_and_extra_fields(self):
        rows = complete() + [record(run_id='old', selected_for_summary=False)]
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            s.write_outputs(rows, summary(rows), p)
            restored = [json.loads(l) for l in (p/'records.jsonl').read_text().splitlines()]
            self.assertEqual(restored, rows)
            with (p/'trials.csv').open(encoding='utf-8-sig') as f: table = list(csv.DictReader(f))
            self.assertEqual(len(table), 5)
            self.assertEqual(table[0]['repeat_index'], '1')


if __name__ == '__main__':
    unittest.main()

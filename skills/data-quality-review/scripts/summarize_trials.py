#!/usr/bin/env python3
"""Summarize explicitly selected, audited trials; no model calls or score inference."""
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import statistics
import sys

PHASES = ('queue', 'preparation', 'agent', 'verifier', 'trial_wall', 'recovery', 'analysis')
STATUSES = {'completed', 'timeout', 'api_error', 'infra_error', 'verifier_error',
            'interrupted', 'running', 'blocked', 'deferred', 'paused'}
GROUP_FIELDS = ('dataset_id', 'protocol_id', 'metric_kind', 'metric_id',
                'score_direction', 'pass_rule_id')
TEXT_FIELDS = ('run_id', 'dataset_id', 'task_id', 'task_version', 'protocol_id',
               'model_id', 'role', 'status', 'metric_id', 'metric_kind', 'score_direction')


def load_records(path):
    content = path.read_text(encoding='utf-8')
    if path.suffix.lower() == '.jsonl':
        rows = [json.loads(line) for line in content.splitlines() if line.strip()]
    else:
        value = json.loads(content)
        rows = value.get('trials') if isinstance(value, dict) else value
    if not isinstance(rows, list):
        raise ValueError('Input must be a JSON array, {trials: [...]}, or JSONL records')
    return rows


def numeric(value, label, nonnegative=False):
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                              or not math.isfinite(value) or (nonnegative and value < 0)):
        raise ValueError(f'{label}: expected finite number{" >= 0" if nonnegative else ""} or null')


def validate(rows):
    ids, selections = set(), set()
    for n, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f'Record {n}: expected object')
        if row.get('example_only'):
            raise ValueError(f'Record {n}: example_only record is not experiment evidence')
        for key in TEXT_FIELDS:
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f'Record {n}: missing/non-string {key}')
        for key in ('selected_for_summary', 'valid_for_comparison'):
            if not isinstance(row.get(key), bool):
                raise ValueError(f'Record {n}: {key} must be boolean')
        if row['run_id'] in ids:
            raise ValueError(f'Duplicate run_id: {row["run_id"]}')
        ids.add(row['run_id'])
        if row['role'] not in {'solver', 'control', 'analysis'} or row['status'] not in STATUSES:
            raise ValueError(f'Record {n}: unknown role/status')
        if row['metric_kind'] not in {'binary', 'continuous', 'answer_key_match', 'ppl'}:
            raise ValueError(f'Record {n}: unknown metric_kind')
        if row['score_direction'] not in {'higher', 'lower'}:
            raise ValueError(f'Record {n}: unknown score_direction')
        if isinstance(row.get('attempt'), bool) or not isinstance(row.get('attempt'), int) or row['attempt'] < 1:
            raise ValueError(f'Record {n}: attempt must be positive integer')
        repeat = row.get('repeat_index')
        if row['role'] == 'solver' and (isinstance(repeat, bool) or not isinstance(repeat, int) or not 1 <= repeat <= 4):
            raise ValueError(f'Record {n}: solver repeat_index must be integer 1..4')
        for key in ('score', 'passed', 'pass_rule_id', 'times_seconds'):
            if key not in row:
                raise ValueError(f'Record {n}: missing {key}; use null for unknown')
        numeric(row['score'], f'Record {n} score')
        if row['passed'] is not None and not isinstance(row['passed'], bool):
            raise ValueError(f'Record {n}: passed must be boolean or null')
        rule = row['pass_rule_id']
        if rule is not None and (not isinstance(rule, str) or not rule.strip()):
            raise ValueError(f'Record {n}: pass_rule_id must be nonempty string or null')
        if row['passed'] is not None and not rule:
            raise ValueError(f'Record {n}: passed requires explicit pass_rule_id')
        if not isinstance(row['times_seconds'], dict):
            raise ValueError(f'Record {n}: times_seconds must be an object')
        for phase in PHASES:
            numeric(row['times_seconds'].get(phase), f'Record {n} time {phase}', True)
        if row['valid_for_comparison'] and row['status'] not in {'completed', 'timeout'}:
            raise ValueError(f'Record {n}: nonterminal/infra status cannot be valid for comparison')
        if row['selected_for_summary'] and row['role'] == 'solver':
            # Different pass rules cannot conceal two selected attempts for the same primary metric.
            key = tuple(row[k] for k in ('dataset_id', 'task_id', 'task_version',
                                        'protocol_id', 'metric_id', 'model_id', 'repeat_index'))
            if key in selections:
                raise ValueError(f'Multiple selected attempts for {key}')
            selections.add(key)


def scored(row):
    return row['valid_for_comparison'] and row['score'] is not None


def median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def repeat_summary(records):
    """Classify all four planned slots; never substitute retries for repeats."""
    slots = {r['repeat_index']: r for r in records}
    missing = [i for i in range(1, 5) if i not in slots]
    invalid = [i for i, r in slots.items() if not scored(r)]
    without_rule = [i for i, r in slots.items() if scored(r) and r['passed'] is None]
    complete = not (missing or invalid or without_rule)
    return {'selected_repeat_count': len(slots), 'missing_selected_repeats': missing,
            'invalid_or_unscored_repeats': sorted(invalid),
            'scored_repeats_without_pass_rule': sorted(without_rule),
            'complete_valid_scored': not (missing or invalid),
            'pass_at_4_eligible': complete,
            'pass_at_4': any(r['passed'] for r in slots.values()) if complete else None,
            'selected_run_ids': {str(i): r['run_id'] for i, r in sorted(slots.items())}}


def summarize(rows, models, pair_models):
    groups = defaultdict(list)
    for row in rows:
        if row['role'] == 'solver':
            groups[tuple(row[k] for k in GROUP_FIELDS)].append(row)
    result = []
    for group_key, all_solver in groups.items():
        selected = [r for r in all_solver if r['selected_for_summary']]
        task_keys = sorted({(r['task_id'], r['task_version']) for r in all_solver})
        task_summaries = []
        for task, version in task_keys:
            task_summaries.append({'task_id': task, 'task_version': version, 'models': {
                model: repeat_summary([r for r in selected if r['task_id'] == task
                    and r['task_version'] == version and r['model_id'] == model])
                for model in models}})
        item = dict(zip(GROUP_FIELDS, group_key))
        item['observed_task_versions'] = len(task_keys)
        item['tasks'] = task_summaries
        item['models'] = {}
        for model in models:
            attempts = [r for r in all_solver if r['model_id'] == model]
            rs = [r for r in selected if r['model_id'] == model]
            valid = [r for r in rs if scored(r)]
            eligible = [r for r in valid if r['passed'] is not None]
            count = sum(r['passed'] is True for r in eligible)
            tasks = [t['models'][model] for t in task_summaries]
            complete = [t for t in tasks if t['pass_at_4_eligible']]
            passed4 = sum(t['pass_at_4'] for t in complete)
            item['models'][model] = {
                'all_attempt_records': len(attempts),
                'all_attempt_statuses': dict(Counter(r['status'] for r in attempts)),
                'selected_records': len(rs), 'selected_statuses': dict(Counter(r['status'] for r in rs)),
                'valid_scored_records': len(valid), 'pass_eligible_records': len(eligible),
                'passed': count, 'pass_rate': count / len(eligible) if eligible else None,
                'pass_at_4_eligible_tasks': len(complete), 'pass_at_4_passed_tasks': passed4,
                'pass_at_4': passed4 / len(complete) if complete else None,
                'pass_at_4_incomplete_tasks': len(tasks) - len(complete),
                'missing_selected_slots_in_observed_tasks': sum(len(t['missing_selected_repeats']) for t in tasks),
                'invalid_or_unscored_selected_slots': sum(len(t['invalid_or_unscored_repeats']) for t in tasks),
                'scored_slots_without_pass_rule': sum(len(t['scored_repeats_without_pass_rule']) for t in tasks),
                'valid_agent_time_count': sum(r['times_seconds'].get('agent') is not None for r in valid),
                'valid_agent_seconds_median': median([r['times_seconds'].get('agent') for r in valid]),
                'valid_trial_wall_seconds_median': median([r['times_seconds'].get('trial_wall') for r in valid])}
        pairs = [[t['models'][model] for model in pair_models] for t in task_summaries]
        valid_pairs = [p for p in pairs if all(t['complete_valid_scored'] for t in p)]
        eligible_pairs = [p for p in pairs if all(t['pass_at_4_eligible'] for t in p)]
        both = sum(all(t['pass_at_4'] for t in p) for p in eligible_pairs)
        item['paired_models'] = {
            'model_ids': list(pair_models), 'metric': 'both_models_pass_at_4',
            'complete_valid_scored_task_pairs': len(valid_pairs),
            'eligible_task_pairs': len(eligible_pairs), 'both_passed_tasks': both,
            'both_pass_at_4_rate': both / len(eligible_pairs) if eligible_pairs else None,
            'complete_scored_pairs_without_pass_rule': len(valid_pairs) - len(eligible_pairs),
            'task_versions_without_complete_valid_pair': len(pairs) - len(valid_pairs)}
        result.append(item)
    return {'schema_version': 2, 'expected_repeats': 4, 'input_records': len(rows),
            'solver_records': sum(r['role'] == 'solver' for r in rows),
            'models_requested': list(models), 'models_seen': sorted({r['model_id'] for r in rows}),
            'coverage_scope': 'Only task versions observed in solver input records; reconcile absent tasks against intake separately. Missing selected slots can be unrun or unselected, not necessarily never attempted.',
            'note': 'Pass@4 uses four distinct selected, valid, scored repeats with explicit pass rules. Retries do not add repeats. No best-of attempt selection.',
            'groups': result}


def csv_value(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r')):
        return "'" + value
    return value


def write_outputs(rows, summary, destination):
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    (destination / 'records.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in rows), encoding='utf-8')
    columns = list(TEXT_FIELDS) + ['host', 'repeat_index', 'attempt', 'selected_for_summary', 'valid_for_comparison',
                                 'score', 'passed', 'pass_rule_id', 'exception_type', 'analysis_status']
    columns += [p + '_seconds' for p in PHASES]
    columns += ['evidence_json']
    with (destination / 'trials.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            flat = {key: csv_value(row.get(key)) for key in columns}
            flat.update({p + '_seconds': row['times_seconds'].get(p) for p in PHASES})
            flat['evidence_json'] = json.dumps(row.get('evidence', {}), ensure_ascii=False)
            writer.writerow(flat)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records', type=Path)
    parser.add_argument('--out-dir', required=True, type=Path)
    parser.add_argument('--models', nargs='+', required=True)
    parser.add_argument('--pair', nargs=2, required=True)
    args = parser.parse_args()
    if len(set(args.models)) != len(args.models):
        parser.error('--models entries must be unique')
    if len(set(args.pair)) != 2 or not set(args.pair).issubset(args.models):
        parser.error('--pair must name two different entries from --models')
    try:
        rows = load_records(args.records)
        validate(rows)
        summary = summarize(rows, args.models, args.pair)
        write_outputs(rows, summary, args.out_dir)
    except (ValueError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    print(json.dumps({'records': len(rows), 'groups': len(summary['groups']), 'out_dir': str(args.out_dir)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

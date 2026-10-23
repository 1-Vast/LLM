"""Synthetic-only skip/abort/aggregation checks for the independent converter."""
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).with_name('data_independent_conversion.py')
FIXTURES = ROOT/'log/20261022/tggates_feedback_headroom/review/data_conversion_synthetic'


class ConversionSafetyTest(unittest.TestCase):
    def fixture(self, name, mutation=None):
        target = FIXTURES/name
        target.mkdir(parents=True, exist_ok=False)
        spec = importlib.util.spec_from_file_location('independent_conversion_'+name, CODE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        compounds, records = [], []
        for number in range(45):
            role = 'source' if number < 24 else 'development' if number < 31 else 'later'
            exp = str(9000+number)
            label = 'synthetic_'+str(number)
            doses, controls = {}, []
            for level_pos, level in enumerate(('Low', 'Middle', 'High')):
                samples = []
                for replicate in (1, 2):
                    row = dict(zip(module.IDENTITY, (exp, str(level_pos+1), str(replicate), label,
                               'Human', 'Female', '24 hr', str(level_pos+1), 'μM', level)))
                    samples.append(row)
                    dna = (70, 80, 90)[level_pos] + (0, 2, 4)[level_pos]*(replicate-1)
                    values = [str(dna), '75'] if role != 'later' else ['POISON_LATER', 'NaN']
                    records.append([row[field] for field in module.IDENTITY]+values)
                doses[level] = {'samples': samples}
            row = dict(zip(module.IDENTITY, (exp, '0', '1', label, 'Human', 'Female',
                           '24 hr', '0', 'μM', 'Control')))
            controls.append(row)
            records.append([row[field] for field in module.IDENTITY]+['POISON_CONTROL', 'Infinity'])
            compounds.append({'compound_label': label, 'role': role, 'doses': doses,
                              'controls_metadata_only': controls})
        if mutation:
            mutation(records)
        raw = target/'SYNTHETIC_ONLY.zip'
        text = io.StringIO(newline='')
        writer = csv.writer(text)
        writer.writerow(module.HEADER)
        writer.writerows(records)
        with zipfile.ZipFile(raw, 'w') as archive:
            archive.writestr('open_tggates_cell_viability.csv', text.getvalue().encode('cp932'))
        manifest = target/'MANIFEST_SYNTHETIC.json'
        relative = raw.relative_to(ROOT).as_posix()
        manifest.write_text(json.dumps({'compounds': compounds, 'raw_zip_relative': relative,
                                       'inputs_sha256': {relative: hashlib.sha256(raw.read_bytes()).hexdigest()}}), encoding='utf-8')
        protocol = target/'SYNTHETIC_PROTOCOL.md'
        protocol.write_text('Synthetic fixture; no biological evidence.\n', encoding='utf-8')
        freeze = target/'SYNTHETIC_FREEZE.json'
        freeze.write_text('{}\n', encoding='utf-8')
        module.REVIEW = target
        module.MANIFEST = manifest
        module.PROTOCOL = protocol
        prior_argv = sys.argv
        try:
            sys.argv = [str(CODE), '--freeze', str(freeze)]
            with contextlib.redirect_stdout(io.StringIO()):
                result = module.main()
        finally:
            sys.argv = prior_argv
        return target, result

    def test_poison_later_controls_skipped_and_decimal_aggregation(self):
        target, result = self.fixture('poison_skipped')
        self.assertEqual(result, 0)
        data = json.loads((target/'DATA_INDEPENDENT_NUMERIC.json').read_bytes())
        self.assertEqual(data['assay_casts'], 372)
        self.assertEqual(data['later_assay_casts'], 0)
        self.assertEqual(data['control_assay_casts'], 0)
        high = next(row for row in data['condition_aggregates']
                    if row['compound_label'] == 'synthetic_0' and row['dose_level'] == 'High')
        self.assertAlmostEqual(float(high['assays']['DNA']['mean_decimal']), .92)
        self.assertAlmostEqual(float(high['assays']['DNA']['sd_ddof1_decimal']), .04/(2**.5))
        for method, expected in [('constant_085', .07), ('middle_copy', .11),
                                  ('source_high_median', 0), ('source_median_offset', 0)]:
            self.assertAlmostEqual(float(data['development_baselines'][method]['development_DNA_MAE_decimal']), expected)
        self.assertFalse(data['prior_root_numeric_outputs_read'])
        self.assertTrue((target/'DATA_INDEPENDENT_NUMERIC_SEAL.json').is_file())

    def test_selected_poison_aborts_without_numeric_result(self):
        def mutation(rows):
            rows[0][10] = 'SELECTED_POISON'
        target, result = self.fixture('selected_poison', mutation)
        self.assertEqual(result, 2)
        self.assertFalse((target/'DATA_INDEPENDENT_NUMERIC.json').exists())
        failure = json.loads((target/'DATA_INDEPENDENT_FAILURE.json').read_bytes())
        self.assertEqual(failure['stage'], 'selected_DNA_parse')
        self.assertEqual(failure['selected_value_attempts'], 1)

    def test_identity_mismatch_aborts_before_values(self):
        def mutation(rows):
            rows[0][3] = 'WRONG_LABEL'
        target, result = self.fixture('identity_mismatch', mutation)
        self.assertEqual(result, 2)
        failure = json.loads((target/'DATA_INDEPENDENT_FAILURE.json').read_bytes())
        self.assertEqual(failure['selected_value_attempts'], 0)

    def test_duplicate_selected_key_aborts(self):
        def mutation(rows):
            rows.insert(1, list(rows[0]))
        target, result = self.fixture('duplicate_key', mutation)
        self.assertEqual(result, 2)
        failure = json.loads((target/'DATA_INDEPENDENT_FAILURE.json').read_bytes())
        self.assertEqual(failure['selected_value_attempts'], 2)

    def test_missing_selected_key_aborts(self):
        def mutation(rows):
            del rows[0]
        target, result = self.fixture('missing_key', mutation)
        self.assertEqual(result, 2)
        failure = json.loads((target/'DATA_INDEPENDENT_FAILURE.json').read_bytes())
        self.assertEqual(failure['stage'], 'complete_keys')
        self.assertEqual(failure['selected_value_attempts'], 370)


if __name__ == '__main__':
    unittest.main()

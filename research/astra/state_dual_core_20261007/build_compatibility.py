"""Explicit complete native candidate menu plus incompatible phenotype sources."""
import ast
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent


def main():
    plan = json.loads((HERE/'world/metadata_freeze.json').read_text())
    contract = json.loads((HERE/'world/contract.json').read_text())
    rows = []
    selected = {r['label']: r for r in plan['conditions']}
    for label in plan['full_source_candidate_labels']:
        components = ast.literal_eval(label)
        chosen = selected.get(label)
        control = label == contract['control']
        rows.append({
            'source': 'official processed Tahoe c39', 'source_sha256': contract['hashes']['dataset']['sha256'],
            'compound_identity': label, 'chemical_group': chosen['chemical_group'] if chosen else '',
            'cell_identity': 'NCI-H596', 'dose_vector': json.dumps(components), 'dose_unit': 'uM as source label',
            'exposure_hours': 24, 'assay': 'single-cell RNA', 'readout': 'native X_hvg numerical change; RNA RMS',
            'control_availability': 'same-plate official DMSO; disjoint basal/reference row sets for selected conditions',
            'feature_schema': 'ordered native 2000 X_hvg;1969 named;31 unresolved;no remapping',
            'predecision_availability': 'retrospective public-source control reference; not certified prospective culture RNA; treated labels gated',
            'training_evaluation_role': chosen['split'] if chosen else ('reference_control' if control else 'outside_bounded_study_menu'),
            'mapping_uncertainty': 'checkpoint training overlap unknown; same label is categorical support only; no unseen drug generalization',
            'qc': 'deposited processed cells; study eligibility >=5 cells in each dose; full attempted-experiment denominator absent',
            'licensing_access': 'public download; STATE model/output noncommercial license; source data terms retained, not inferred from paper license',
            'state_support': 'map_present' if label in contract['mapping'] else 'unsupported_map_missing',
            'action': 'evaluated_native_prediction' if chosen else ('reference_only' if control else 'retain_menu_with_no_study_forecast;explicit_fallback_or_refusal'),
            'condition_id': chosen['condition_id'] if chosen else '', 'source_plate': chosen['plate'] if chosen else '',
        })
    for source, hours, assay, readout, control in [
        ('Jaaks historical non-target mono','72','ATP luminescence','normalized ATP viability','qualified plate NC1/blank'),
        ('PRISM Repurposing19Q4 article9393293v4','120','pooled barcode abundance','ComBat-corrected log2 fold change','published controls; preprocessing target dependence unresolved')]:
        rows.append({'source':source,'compound_identity':'qualified historical registry mappings; see previous source archives',
            'cell_identity':'111 Jaaks /443 PRISM non-target reference cells','dose_vector':'record-specific actual doses','dose_unit':'uM',
            'exposure_hours':hours,'assay':assay,'readout':readout,'control_availability':control,
            'feature_schema':'sparse phenotype observations, not STATE basal RNA',
            'predecision_availability':'public historical reference only','training_evaluation_role':'not used in native STATE fitting or evaluation',
            'mapping_uncertainty':'no exact paired RNA-to-phenotype bridge; dose/time/study mismatch',
            'licensing_access':'original dataset source/access notices retained in functional_data_20261007',
            'state_support':'incompatible_input_and_endpoint','action':'separate_assay_head_or_refuse_bridge'})
    pd.DataFrame(rows).to_csv(HERE/'DATA_COMPATIBILITY.csv',index=False)
    print(json.dumps({'native_menu_labels':len(plan['full_source_candidate_labels']),'study_conditions':len(selected),'total_table_rows':len(rows)}))


if __name__ == '__main__':
    main()

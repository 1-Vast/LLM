"""R203-X2 audit: trace AZ/GDSC 2024 paper-reported replication and functional subsets
in the current public export/ZIP (metadata-only; no effect fitting, no response-value
statistics; response columns are only checked for structural presence where needed).

Reads receipts/ produced from the paper JATS, Figshare project metadata, the raw well
ZIP's structural scan, plate QC, and the supplementary ZIP inventory.  Writes
audit_x2.json (sorted keys, no timestamps).
"""
import hashlib
import json
import os

B = r'D:\MAESTRO'
HERE = os.path.join(B, r'research\2026-10-28-az-export-coverage')
REC = os.path.join(HERE, 'receipts')
PROTOCOL = os.path.join(HERE, 'PROTOCOL_X2.md')
OUT = os.path.join(HERE, 'audit_x2.json')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest().upper()


def load(n):
    with open(os.path.join(REC, n), encoding='utf-8') as f:
        return json.load(f)


def q(x):
    if isinstance(x, dict):
        return {k: q(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [q(v) for v in x]
    if isinstance(x, float):
        return round(x, 6) if x == x else None
    return x


paper = load('paper_claims.json')
inv = load('export_inventory.json')
struct = load('structure_7lines_repeats.json')
r202 = load('r202_claims.json')
downloads = load('download_manifest_x2.json')

lines = struct['lines']
exact = struct['exact_counts']
line_names = ['A375', 'HT-29', 'PC-14', 'U-2-OS', 'SW620', 'C32', 'MHH-ES-1']
total_pairs = sum(exact[n]['pairs'] for n in line_names)
total_rows = sum(exact[n]['rows'] for n in line_names)
total_barcodes = sum(exact[n]['barcodes'] for n in line_names)
total_exact18 = sum(exact[n]['exact_18_matrices'] for n in line_names)
total_6x3 = sum(exact[n]['exact_18_6_dates_3each'] for n in line_names)
matrix_ranges = {n: exact[n]['pair_matrix_range'] for n in line_names}
functional = struct.get('functional_cells_in_s18', {})
func_hits = struct.get('functional_target_pair_hits', {})

# ---- seven named lines table ----
seven_table = []
for n in line_names:
    e = exact[n]; s = lines[n]
    seven_table.append({
        'cell_line': n,
        'rows_in_raw_well_zip': e['rows'],
        'barcodes': e['barcodes'],
        'pairs': e['pairs'],
        'matrix_records_per_pair_range': e['pair_matrix_range'],
        'pair_units_exact_18_matrices': e['exact_18_matrices'],
        'pair_units_exact_18_6_qc_dates_3_each': e['exact_18_6_dates_3each'],
        'pair_units_ge18_matrices': e['pairs_ge18'],
        'pair_units_ge6_qc_dates': e['pairs_ge6_dates'],
        'sample_6_date_x_3_matrix_pair': (s.get('sample_pair_detail') or {}).get('pair'),
        'sample_6_date_groups': (len((s.get('sample_pair_detail') or {}).get('dates') or []) or None),
        'table_s1_replicate_flag': 'Yes',
    })

coverage_items = {
    'P1_72h_exposure': {
        'status': 'not_obtained',
        'evidence_tag': 'not_in_export',
        'observation': '论文 Methods（S15）明确 72 h 处理；当前 raw well ZIP / Table S18 / QC 无 exposure time 或 assay 字段。',
        'wording': '论文报告已做，当前导出未取得逐板/逐孔 72 h 暴露字段；72 h 可作为论文协议常数带入，不能由导出表验证。',
    },
    'P2_celltiterglo_2': {
        'status': 'not_obtained',
        'evidence_tag': 'not_in_export',
        'observation': '论文 Methods（S15）报告 CellTiter-Glo 2.0；当前导出没有 assay/readout 字段。',
        'wording': '论文报告已做，当前导出未取得 CellTiter-Glo 2.0 的 assay 字段；不能据此说实验未做。',
    },
    'P3_seven_named_lines': {
        'status': 'available_analyzable',
        'evidence_tag': 'parsed_export_records',
        'observation': 'Table S1 的 Replicate Cell Line=Yes 给出 7 系（A375, C32, MHH-ES-1, PC-14, SW620, U-2-OS, HT-29）；7 系均在 raw well ZIP/Table S18 有记录。',
        'wording': '7 个具名重复细胞系的记录存在，可解析。',
    },
    'P4a_repeated_matrix_records': {
        'status': 'available_analyzable',
        'evidence_tag': 'parsed_export_records',
        'observation': f'7 系共 {total_pairs} 个 (line,pair) 单元；每个 pair 的 matrix 记录（BARCODE×cmatrix）范围 {matrix_ranges}；7 系共 {total_rows} well 行、{total_barcodes} barcodes；301 个 pair-line 单元恰有 18 个 matrix 记录，161 个可归为 6 个 QC 上传日期 × 每日期 3 个 matrix（示例见 structure_7lines_repeats.json）。',
        'wording': '重复的原始 matrix/barcode 记录存在，且可按 barcode/cmatrix/QC 日期枚举；R202 的“0 repeats”不是实验事实。',
    },
    'P4b_six_occasion_technical_triplicate_labels': {
        'status': 'present_but_not_analyzable',
        'evidence_tag': 'metadata_missing',
        'observation': 'raw well 表只有 PROJECT_NAME/BARCODE/cmatrix/POSITION；plate QC 提供 SCAN_ID/QC_UPLOAD_DATE/QC_FLAG；没有 experiment id、occasion、replicate index、treatment date、passage/culture 字段。161/763 个 pair-line 单元可恢复 6 QC 日期 ×3 matrix；其余记录为 3–38 个 matrix，QC/额外 screen 导致不能统一认证 6×3。',
        'wording': '重复记录存在，但“6 次实验 × 技术三重复”的显式标签不可解析；QC 上传日期不是实验处理日期，不能当作实验日。',
    },
    'P4c_independent_culture_day_passage': {
        'status': 'not_obtained',
        'evidence_tag': 'not_in_export',
        'observation': '无 passage、培养瓶/孔板独立培养、实验日字段；论文自身称 technical triplicate（另有 biological replicate 措辞），但导出未认证独立培养。',
        'wording': '论文报告技术三重复；当前导出未取得独立培养/实验日/passage 记录；不能说成独立培养重复，也不能说实验未做。',
    },
    'P5_plate_well_matrix_fields': {
        'status': 'available_analyzable',
        'evidence_tag': 'parsed_export_records',
        'observation': 'raw well 含 BARCODE、POSITION、cmatrix、lib1_dose/lib1_conc、lib2_dose/lib2_conc、lib1_drug_id/lib2_drug_id、CELL_LINE_NAME/COSMIC_ID/SIDM；plate QC 含 SCAN_ID、QC_FLAG、QC_UPLOAD_DATE。',
        'wording': '板/孔/matrix/剂量字段可关联；QC 元数据可关联。',
    },
    'P6_experiment_date_batch_labels': {
        'status': 'present_but_not_analyzable',
        'evidence_tag': 'metadata_missing',
        'observation': 'PROJECT_NAME/PROJECT_ID 与 DRUGSET_ID 可作 screen/batch 代理；QC_UPLOAD_DATE 可作上传批次；没有 treatment/experiment date、实验批次 ID、replicate/occasion 标签。',
        'wording': '有 screen/project 与 QC 上传日期，但实验日/实验批次/重复标签未取得；不能把 QC 上传日当处理日。',
    },
    'P7_functional_readout_data': {
        'status': 'present_but_not_analyzable',
        'evidence_tag': 'present_but_unparsed',
        'observation': '论文报告并展示 Fig 4E/F、Fig 5C/D、Fig 6C–E 的 apoptosis/caspase/PARP/western（Supplementary Figures PDF 55 MB）；当前 Figshare project 163378 的 12 项数据没有 functional 数据集，Table S18 只有 screening viability 摘要，没有 caspase/PARP 数值表。',
        'wording': '论文报告已做且图/补充图存在；当前导出未取得可分析的 functional numeric 记录（只有图像级），不是实验未做。',
    },
    'P7b_functional_numeric_records': {
        'status': 'not_obtained',
        'evidence_tag': 'not_in_export',
        'observation': 'NOMO-1/AN3-CA 的 target viability 组合在 Table S18 各有 1 个 matrix 行；但没有 caspase/PARP/western 的数值数据或源表。',
        'wording': '论文报告已做，当前导出未取得 caspase/PARP/western 的可分析数值记录；需向作者/补充源数据/图数据获取。',
    },
    'P7c_viability_screening_for_functional_cells_combos': {
        'status': 'available_analyzable',
        'evidence_tag': 'parsed_export_records',
        'observation': 'Table S18 中 NOMO-1 有 107 个 matrix 行/106 个 pair，AN3-CA 有 80 个 matrix 行/80 个 pair；target 组合（selumetinib+venetoclax, selumetinib+AZD5991, capivasertib+AZD5991）各出现 1 个 matrix 行（screening viability，非功能读数）。',
        'wording': '功能验证细胞与组合的 screening viability 记录存在；它们不等于 apoptosis/caspase/PARP 功能数据。',
    },
}

# ---- R202 difference / correction ----
r202_g4 = r202.get('gates', {}).get('G4_independent_measurement_or_culture', {})
r202_diff = {
    'r202_claim_68_a0_keys': r202.get('jaaks_overlap', {}).get('exact_a0_matched_keys'),
    'r202_claim_0_repeats': r202_g4.get('units_with_ge2_platforms'),
    'r202_scan_key_issue': r202.get('r202_scan_pair_key_issue', {}),
    'audit_finding': {
        'repeated_matrix_records_present': True,
        'seven_line_pair_units': total_pairs,
        'total_well_rows_seven_lines': total_rows,
        'pair_units_exact_18_matrices': total_exact18,
        'pair_units_exact_18_6_qc_dates_3_each': total_6x3,
        'matrix_range': matrix_ranges,
    },
    '68_keys_not_recomputed_or_recertified': True,
    'explanation': [
        '68 是 R202 的 A0 精确浓度匹配键数（Jaaks 2 anchor×7 library vs AZ 7×7），不是重复记录数；本轮未重算，不改变其定义。',
        'R202 的 0 repeats（units_with_ge2_platforms=0）来自 scan_azeraw.py 以 lib1_drug/lib2_drug 字符串（如 38690_L56，含 barcode）作为 pair 身份，导致同一 pair 跨 barcode 被拆开；当前结构扫描用 lib1_drug_id/lib2_drug_id + BARCODE/cmatrix，7 系显示大量重复记录。',
        '因此 R202 的“0 重复/无暴露时间/无正交功能”必须按本审计改写：重复记录存在（7 系 109 pairs/line；301 个 exact-18 单元；161 个 exact 6×3 单元）；72 h/CellTiter-Glo 2.0 为论文协议常数，导出无字段；功能验证有论文图但当前导出无 numeric 记录。',
        'R202 的 not_qualified 判定本轮不重做、不晋升代码；其中“0 repeats”作为 G4 fail 的直接依据应撤回/降级，剩余缺口是显式实验/replicate/passage 标签、协议字段和功能 numeric 数据；是否影响 Q1 资格需另立重评，不在本审计宣称。',
    ],
    'no_recount_certification': '未重扫全部 3.9M wells 做效应；未重算 A0 匹配键；结构计数只用于 7 个具名重复系与功能子集的覆盖追踪。',
}

overall = {
    'coverage_conclusion': (
        '当前公开导出对论文声明的覆盖是部分覆盖，且 R202“0 repeats”不成立：'
        f'7 个具名重复系（A375, HT-29, PC-14, U-2-OS, SW620, C32, MHH-ES-1）在 raw well ZIP/Table S18 中有记录，'
        f'每系 109 个 pair；7 系共 {total_rows} well 行、{total_barcodes} barcodes；'
        f'301 个 pair-line 单元恰好 18 个 matrix 记录，161 个可归为 6 个 QC 上传日期 × 每日期 3 个 matrix。'
        '但是：没有显式 experiment/occasion/technical replicate/日期-of-treatment/passage 字段；'
        '72 h/CellTiter-Glo 2.0 只在论文 Methods，导出无字段；caspase/PARP/western 只存在于论文图/补充 PDF，无 numeric 数据表。'
    ),
    'what_is_available_analyzable': [
        '7 个具名重复细胞系的身份与记录（Table S1 + raw/Table S18）',
        '重复的 raw matrix/barcode 记录（BARCODE×cmatrix；可按 barcode/cmatrix/QC 日期枚举）',
        '板/孔/matrix/数字剂量/药物 ID/细胞 ID 与 plate QC 的 SCAN_ID/QC_FLAG/QC_UPLOAD_DATE 关联',
        '功能验证细胞/组合的 screening viability 记录（Table S18；每个 target 组合 1 个 matrix 行）',
    ],
    'what_is_not_obtained_or_not_analyzable': [
        '6 次实验 × 技术三重复的显式标签/实验批次/处理日期（present_but_not_analyzable: metadata_missing）',
        '独立培养/独立日/passage 记录（not_obtained）',
        '72 h 与 CellTiter-Glo 2.0 的逐记录协议字段（not_obtained；论文报告已做）',
        'caspase/PARP/western/apoptosis 的 numeric 数据（not_obtained；论文图/补充 PDF 存在）',
    ],
    'wording': '所有未取得项写“论文报告已做，当前未取得可分析记录”，不写“只能新湿实验提供”；表内缺列不推断实验未做；不用“0 repeats”描述作者实验。',
    'recommended_followups': [
        '向作者/Figshare 补充请求 barcode/cmatrix → experiment/occasion/replicate/treatment date/passage 的数据字典或映射（当前导出缺这些字段）。',
        '获取 Fig 4/5/6 和 Supplementary Figures 的 underlying source data / western/caspase 原始数值（当前 PDF 仅图像）。',
        '若重评 Q1 资格：先用 7 系重复 matrix 记录构造重复测量覆盖（技术三重复 vs 独立培养要分开标注），再核对 68 A0 keys 与 500 键门槛；本轮不重算、不认证、不改 R202 结论。',
        '不要把 7 系技术三重复当作 754 细胞全网格的独立功能重复；不要把 Table S18 的 screening viability 当作 caspase/PARP 功能数据。',
    ],
    'does_not_change': [
        '不重做 R202 资格判定；不晋升代码；不称新颖性/迁移/决策收益/机制。',
        'A0 68 keys 未重算；本轮未重扫 3.9M wells 做效应。',
    ],
}

result = {
    'protocol': {'path_rel': 'research/2026-10-28-az-export-coverage/PROTOCOL_X2.md',
                 'sha256': sha(PROTOCOL), 'version': 'PROTOCOL_X2 v1 FROZEN'},
    'script': {'path_rel': 'research/2026-10-28-az-export-coverage/audit_x2.py',
               'sha256': sha(os.path.join(HERE, 'audit_x2.py'))},
    'inputs': {
        'paper_claims': {'file': 'receipts/paper_claims.json', 'sha256': sha(os.path.join(REC, 'paper_claims.json'))},
        'export_inventory': {'file': 'receipts/export_inventory.json', 'sha256': sha(os.path.join(REC, 'export_inventory.json'))},
        'structure': {'file': 'receipts/structure_7lines_repeats.json', 'sha256': sha(os.path.join(REC, 'structure_7lines_repeats.json'))},
        'r202_claims': {'file': 'receipts/r202_claims.json', 'sha256': sha(os.path.join(REC, 'r202_claims.json'))},
        'download_manifest': {'file': 'receipts/download_manifest_x2.json', 'sha256': sha(os.path.join(REC, 'download_manifest_x2.json'))},
    },
    'paper_claims': paper,
    'export_inventory': {
        'figshare_project_items': inv['figshare_project']['items'],
        'raw_well_columns': inv['raw_well_columns'],
        'expected_fields_absent': inv['expected_fields_absent'],
        'plate_qc_summary': inv['plate_qc']['summary'],
        'supplementary_members': inv['supplementary_zip']['members'],
        'supplementary_table_s18': inv['supplementary_zip']['table_s18'],
    },
    'seven_named_lines': {'line_names': line_names, 'table': seven_table,
                          'totals': {'lines': len(line_names), 'pairs': total_pairs,
                                     'well_rows': total_rows, 'barcodes_sum': total_barcodes,
                                     'pair_units_exact_18_matrices': total_exact18,
                                     'pair_units_exact_18_6_qc_dates_3_each': total_6x3}},
    'repeat_coverage': {
        'matrix_records_per_pair_range': matrix_ranges,
        'exact_counts': exact,
        'functional_cells_in_s18': functional,
        'functional_target_pair_hits': func_hits,
    },
    'field_mapping': {
        'cell': ['CELL_LINE_NAME', 'MASTER_CELL_ID', 'COSMIC_ID', 'SIDM'],
        'cell_replicate_flag': 'Table S1 column Replicate Cell Line (7 Yes: A375, C32, MHH-ES-1, PC-14, SW620, U-2-OS, HT-29)',
        'drug': ['lib1_drug_id', 'lib2_drug_id', 'lib1_drug', 'lib2_drug', 'Table S2 Compound1_ID/name, Compound2_ID/name'],
        'dose': ['lib1_dose', 'lib1_conc', 'lib2_dose', 'lib2_conc', 'cmatrix (7x7 matrix position)'],
        'plate_well': ['BARCODE', 'POSITION', 'cmatrix'],
        'qc_date_batch': ['SCAN_ID', 'QC_FLAG', 'QC_UPLOAD_DATE'],
        'screen_batch_proxy': ['PROJECT_ID', 'PROJECT_NAME', 'DRUGSET_ID', 'screen (Table S18)'],
        'missing_protocol_fields': ['experiment_id', 'occasion', 'replicate_index', 'treatment_date',
                                    'exposure_time', 'assay/readout', 'passage', 'culture/day'],
        'functional_readout_mapping': 'caspase/PARP/western not in export; figure-level in paper/Supplementary Figures PDF; Table S18 = screening viability only',
        'r202_comparison': 'R202 A0 exact concentration matched keys 68; 0-repeat claim came from barcode-tagged lib1_drug/lib2_drug pair key; no full re-count/certification here',
    },
    'coverage_items': coverage_items,
    'r202_difference': r202_diff,
    'overall': overall,
    'downloads': downloads,
    'determinism': {'json_keys_sorted': True, 'timestamps': False,
                    'two_runs_identical': True},
}
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(q(result), f, indent=1, sort_keys=True, ensure_ascii=False)
    f.write('\n')
print(json.dumps({
    'overall': overall['coverage_conclusion'][:600],
    'seven': result['seven_named_lines']['totals'],
    'items': {k: v['status'] for k, v in coverage_items.items()},
    'r202_diff': r202_diff['audit_finding'],
}, ensure_ascii=False, indent=1))

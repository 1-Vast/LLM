"""Guard protected sentinel and preserve author sequential means under missingness."""
import math
from qualify import parse_allowed, sequential_mean, reconstruct

rows = [['', 'A_g1', 'B_g1', 'C_g1'],
        ['A_g1', 'DIAGONAL', '0', 'PROTECTED_SENTINEL'],
        ['B_g1', '0', 'DIAGONAL', 'PROTECTED_SENTINEL'],
        ['C_g1', 'PROTECTED_SENTINEL', 'PROTECTED_SENTINEL', 'DIAGONAL']]
values, converted = parse_allowed(rows, {'A|B'})
assert converted == 2 and reconstruct(values, 'A', 'B') == 0
assert not any('C' in key for key in values)
example = {('a1', 'b1'): 0., ('a2', 'b1'): 2., ('a1', 'b2'): 10., ('a2', 'b2'): math.nan}
assert sequential_mean(example) == 5.5
print('PASS non-source sentinels excluded, zero preserved, sequential missing-aware mean')

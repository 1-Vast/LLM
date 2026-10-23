"""Both source-key and selected-guide mapping must hold before numeric conversion."""
from qualify import masked_matrix

rows = [['', 'ga', 'gb', 'gc'], ['ga', 'DIAG', '0', 'PROTECTED'],
        ['gb', '0', 'DIAG', 'PROTECTED'], ['gc', 'PROTECTED', 'PROTECTED', 'DIAG']]
values, count = masked_matrix(rows, {'A|B'}, {'A': 'ga', 'B': 'gb', 'C': 'gc'})
assert count == 2 and values == {('A', 'B'): 0., ('B', 'A'): 0.}
rows = [['', 'A', 'B', 'C'], ['A', 'DIAG', '0', 'PROTECTED'],
        ['B', '0', 'DIAG', 'PROTECTED'], ['C', 'PROTECTED', 'PROTECTED', 'DIAG']]
assert masked_matrix(rows, {'A|B'}) == (values, count)
print('PASS both matrix source-key masks, guide ID membership, zero and protected sentinel')

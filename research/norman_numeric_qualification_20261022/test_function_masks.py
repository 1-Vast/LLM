"""A protected nonnumeric sentinel must never be parsed; true zero must survive."""
from function_masks import allowed_values

matrix = [['', 'A', 'B', 'C'],
          ['A', 'UNREAD_DIAGONAL', '0', 'PROTECTED_SENTINEL'],
          ['B', '0', 'UNREAD_DIAGONAL', ''],
          ['C', 'PROTECTED_SENTINEL', '', 'UNREAD_DIAGONAL']]
values, converted = allowed_values(matrix, {'A|B': 'source', 'A|C': 'protected',
                                           'B|C': 'development'}, {'A', 'B', 'C'})
assert values['A', 'B'] == values['B', 'A'] == 0
assert ('A', 'C') not in values and ('C', 'A') not in values
assert converted == 4
print('PASS protected sentinel/diagonal not decoded; real zero retained; missing distinct')

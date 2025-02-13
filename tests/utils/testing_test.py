import itertools

import pytest

from cycl.utils.testing import is_circular_reversible_permutation

# neat that every permutation of 1, 2, 3 is True
permutations = list(itertools.permutations([1, 2, 3]))

@pytest.mark.parametrize(
    ('lst', 'candidate', 'expected'),
    [
        *[([1, 2, 3], list(candidate), True) for candidate in permutations],
        ([1, 2, 3, 4], [3, 4, 2, 1], False),
    ],
)
def test_is_circular_reversible_permutation(lst, candidate, expected):
    actual = is_circular_reversible_permutation(lst, candidate)
    assert actual == expected

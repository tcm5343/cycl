import pytest

from cycl.utils.cfn import parse_name_from_id


@pytest.mark.parametrize(
    ('stack_id', 'expected'),
    [
        ('arn:aws:cloudformation:us-east-1:000000000000:stack/template-1/05a85f80', 'template-1'),
        ('/', ''),
        ('', ''),
    ],
)
def test_parse_name_from_id(stack_id, expected):
    actual = parse_name_from_id(stack_id)
    assert actual == expected

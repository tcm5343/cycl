from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from cycl._utils.cfn import list_exports, list_importing_stacks, parse_name_from_id
from cycl.models import Export, Stack


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


def _client_with_pages(operation, pages):
    cfn_client = Mock(name='cfn_client')

    def get_paginator(name):
        assert name == operation
        paginator = Mock(name=f'{name}_paginator')
        paginator.paginate.side_effect = lambda **_kwargs: iter(pages)
        return paginator

    cfn_client.get_paginator.side_effect = get_paginator
    return cfn_client


def test_list_exports_across_pages():
    stack_id_1 = 'arn:aws:cloudformation:us-east-1:000000000000:stack/stack-1/guid'
    stack_id_2 = 'arn:aws:cloudformation:us-east-1:000000000000:stack/stack-2/guid'
    cfn_client = _client_with_pages(
        'list_exports',
        [
            {'Exports': [{'ExportingStackId': stack_id_1, 'Name': 'export-1', 'Value': 'value-1'}]},
            {'Exports': [{'ExportingStackId': stack_id_2, 'Name': 'export-2', 'Value': 'value-2'}]},
        ],
    )

    actual = list_exports(cfn_client)

    assert actual == {
        'export-1': Export(name='export-1', value='value-1', exporting_stack=Stack(name='stack-1')),
        'export-2': Export(name='export-2', value='value-2', exporting_stack=Stack(name='stack-2')),
    }
    assert actual['export-1'].exporting_stack.id == stack_id_1


def test_list_exports_empty():
    assert list_exports(_client_with_pages('list_exports', [{'Exports': []}])) == {}


def test_list_importing_stacks_across_pages():
    cfn_client = _client_with_pages('list_imports', [{'Imports': ['stack-1', 'stack-2']}, {'Imports': ['stack-3']}])

    actual = list_importing_stacks(cfn_client, 'export-1')

    assert actual == [Stack(name='stack-1'), Stack(name='stack-2'), Stack(name='stack-3')]


def test_list_importing_stacks_not_imported_returns_empty():
    cfn_client = Mock(name='cfn_client')
    cfn_client.get_paginator.return_value.paginate.side_effect = ClientError(
        {'Error': {'Code': 'ValidationError', 'Message': "Export 'export-1' is not imported by any stack."}},
        'ListImports',
    )

    assert list_importing_stacks(cfn_client, 'export-1') == []


def test_list_importing_stacks_raises_other_client_errors():
    cfn_client = Mock(name='cfn_client')
    cfn_client.get_paginator.return_value.paginate.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'nope'}},
        'ListImports',
    )

    with pytest.raises(ClientError):
        list_importing_stacks(cfn_client, 'export-1')

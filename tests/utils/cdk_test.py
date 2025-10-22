import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

import cycl.utils.cdk as cdk_module
from cycl.models.export_data import NodeData
from cycl.utils.cdk import InvalidCdkOutPathError, get_exports_from_assembly


@pytest.fixture
def cdk_template_mock():
    return {
        'Resources': {
            'MyResource': {
                'Type': 'AWS::S3::Bucket',
                'Properties': {'BucketName': {'Fn::ImportValue': 'some-export-name-1'}},
            }
        }
    }


@pytest.fixture
def cdk_manifest_mock():
    return {'artifacts': {'test-stack-1': {'displayName': 'some-stack-display-name-1'}}}


@pytest.fixture
def cdk_out_mock(tmp_path, cdk_template_mock, cdk_manifest_mock):
    cdk_out_path = tmp_path / 'cdk.out'
    cdk_out_path.mkdir()
    Path(cdk_out_path / 'cdk.out').touch()

    template_path = cdk_out_path / 'test-stack-1.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    manifest_path = cdk_out_path / 'manifest.json'
    with manifest_path.open('w') as f:
        json.dump(cdk_manifest_mock, f)

    return cdk_out_path


@pytest.fixture
def mock_walk():
    with patch.object(cdk_module, 'walk') as mock:
        yield mock


def test_get_exports_from_assembly_no_imports(cdk_out_mock, cdk_template_mock):
    expected = {}
    cdk_template_mock = {}

    template_path = cdk_out_mock / 'test-stack-1.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    actual = get_exports_from_assembly(cdk_out_mock)

    assert actual == expected


def test_get_exports_from_assembly_has_imports(cdk_out_mock):
    expected = {
        'some-export-name-1': [
            NodeData(
                export_name='some-export-name-1',
                stack_name='some-stack-display-name-1',
            ),
        ],
    }
    actual = get_exports_from_assembly(cdk_out_mock)
    assert actual == expected


def test_get_exports_from_assembly_has_imports_in_list(cdk_out_mock, cdk_template_mock):
    expected = {
        'some-export-name-1': [
            NodeData(
                export_name='some-export-name-1',
                stack_name='some-stack-display-name-1',
            ),
        ],
    }
    cdk_template_mock['Resources']['MyResource']['Properties']['BucketName'] = [
        {'Fn::ImportValue': 'some-export-name-1'},
    ]

    template_path = cdk_out_mock / 'test-stack-1.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    actual = get_exports_from_assembly(cdk_out_mock)
    assert actual == expected


def test_get_cdk_out_raises_error_if_no_cdk_out_file_in_folder(cdk_out_mock):
    cdk_out_file = Path(cdk_out_mock / 'cdk.out')
    assert cdk_out_file.is_file  # to confirm we are removing the file, not directory with the same name
    cdk_out_file.unlink(missing_ok=False)

    with pytest.raises(
        InvalidCdkOutPathError, match=rf'File named cdk.out not found in {cdk_out_mock}. Did you run `cdk synth`?'
    ):
        get_exports_from_assembly(cdk_out_mock)


def test_get_cdk_out_raises_error_if_no_cdk_out_folder(cdk_out_mock):
    shutil.rmtree(cdk_out_mock)

    with pytest.raises(InvalidCdkOutPathError, match=rf'Provided path does not exist or is not a directory: {cdk_out_mock}'):
        get_exports_from_assembly(cdk_out_mock)


def test_get_cdk_out_raises_error_if_pointing_to_file(cdk_out_mock):
    with pytest.raises(InvalidCdkOutPathError, match=rf'Provided path does not exist or is not a directory: {cdk_out_mock}'):
        get_exports_from_assembly(cdk_out_mock / 'cdk.out')


def test_get_cdk_out_adds_cdk_out_dir_if_not_already_there(cdk_out_mock, cdk_template_mock, cdk_manifest_mock):
    """Example is `infra/` being passed instead of `infra/cdk.out`, simply append `cdk.out/`."""
    expected = {
        'some-export-name-1': [
            NodeData(
                export_name='some-export-name-1',
                stack_name='some-stack-display-name-1',
            ),
        ],
    }

    cdk_template_mock['Resources']['MyResource']['Properties']['BucketName']['Fn::ImportValue'] = 'some-export-name-2'
    template_path = cdk_out_mock.parent / 'test-stack-2.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    cdk_manifest_mock['artifacts']['test-stack-2'] = {
        'displayName': 'some-stack-display-name-2',
    }
    manifest_path = cdk_out_mock.parent / 'manifest.json'
    with manifest_path.open('w') as f:
        json.dump(cdk_manifest_mock, f)

    actual = get_exports_from_assembly(cdk_out_mock.parent)
    assert actual == expected


def test_get_exports_from_assembly_with_two_stacks(cdk_out_mock, cdk_template_mock, cdk_manifest_mock):
    expected = {
        'some-export-name-1': [
            NodeData(
                export_name='some-export-name-1',
                stack_name='some-stack-display-name-1',
            ),
        ],
        'some-export-name-2': [
            NodeData(
                export_name='some-export-name-2',
                stack_name='some-stack-display-name-2',
            ),
        ],
    }

    cdk_template_mock['Resources']['MyResource']['Properties']['BucketName']['Fn::ImportValue'] = 'some-export-name-2'
    template_path = cdk_out_mock / 'test-stack-2.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    cdk_manifest_mock['artifacts']['test-stack-2'] = {
        'displayName': 'some-stack-display-name-2',
    }
    manifest_path = cdk_out_mock / 'manifest.json'
    with manifest_path.open('w') as f:
        json.dump(cdk_manifest_mock, f)

    actual = get_exports_from_assembly(cdk_out_mock)
    assert actual == expected


@pytest.mark.parametrize(
    'manifest_body',
    [
        {'artifacts': {'test-stack-1': {'displayName': 'some-stack-display-name-1'}, 'test-stack-2': {}}},
        {'artifacts': {'test-stack-1': {'displayName': 'some-stack-display-name-1'}}},
    ],
)
def test_get_exports_from_assembly_skips_when_unable_to_resolve_stack_name(
    cdk_out_mock, cdk_template_mock, cdk_manifest_mock, manifest_body
):
    expected = {
        'some-export-name-1': [
            NodeData(
                export_name='some-export-name-1',
                stack_name='some-stack-display-name-1',
            ),
        ],
    }

    cdk_template_mock['Resources']['MyResource']['Properties']['BucketName']['Fn::ImportValue'] = 'some-export-name-2'
    template_path = cdk_out_mock / 'test-stack-2.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    cdk_manifest_mock = manifest_body
    manifest_path = cdk_out_mock / 'manifest.json'
    with manifest_path.open('w') as f:
        json.dump(cdk_manifest_mock, f)

    actual = get_exports_from_assembly(cdk_out_mock)
    assert actual == expected


def test_get_exports_from_assembly_with_stages(cdk_out_mock, cdk_template_mock, cdk_manifest_mock):
    expected = {
        'some-export-name-1': [
            NodeData(
                export_name='some-export-name-1',
                stack_name='some-stack-display-name-1',
            ),
        ],
        'some-export-name-2': [
            NodeData(
                export_name='some-export-name-2',
                stack_name='some-stack-display-name-2',
            ),
        ],
    }
    cdk_template_mock['Resources']['MyResource']['Properties']['BucketName']['Fn::ImportValue'] = 'some-export-name-2'
    stage_path = cdk_out_mock / 'some-stage-1'
    stage_path.mkdir()
    template_path = stage_path / 'test-stack-2.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    cdk_manifest_mock['artifacts']['test-stack-2'] = {
        'displayName': 'some-stage/some-stack-display-name-2',  # note the stage prefix
    }
    manifest_path = stage_path / 'manifest.json'
    with manifest_path.open('w') as f:
        json.dump(cdk_manifest_mock, f)

    actual = get_exports_from_assembly(cdk_out_mock)
    assert actual == expected


def test_get_exports_from_assembly_grabs_stack_name_first(cdk_out_mock, cdk_manifest_mock):
    expected = {
        'some-export-name-1': [
            NodeData(
                export_name='some-export-name-1',
                stack_name='some-stack-name-1',
            ),
        ],
    }
    cdk_manifest_mock['artifacts']['test-stack-1']['properties'] = {
        'stackName': 'some-stack-name-1',
    }

    manifest_path = cdk_out_mock / 'manifest.json'
    with manifest_path.open('w') as f:
        json.dump(cdk_manifest_mock, f)

    actual = get_exports_from_assembly(cdk_out_mock)
    assert actual == expected

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

import cycl.utils.cdk as cdk_module
from cycl.utils.cdk import InvalidCdkOutPathError, get_cdk_out_imports


@pytest.fixture
def cdk_template_mock():
    return {
        'Resources': {
            'MyResource': {'Type': 'AWS::S3::Bucket', 'Properties': {'BucketName': {'Fn::ImportValue': 'MyExportedBucket1'}}}
        }
    }


@pytest.fixture
def cdk_manifest_mock():
    return {'artifacts': {'test-stack-1': {'displayName': 'TestStack1'}}}


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


def test_get_cdk_out_imports_no_imports(cdk_out_mock, cdk_template_mock):
    expected = {}
    cdk_template_mock = {}

    template_path = cdk_out_mock / 'test-stack-1.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    actual = get_cdk_out_imports(cdk_out_mock)

    assert actual == expected


def test_get_cdk_out_imports_has_imports(cdk_out_mock):
    expected = {'MyExportedBucket1': ['TestStack1']}
    actual = get_cdk_out_imports(cdk_out_mock)
    assert actual == expected


def test_get_cdk_out_imports_has_imports_in_list(cdk_out_mock, cdk_template_mock):
    expected = {'MyExportedBucket1': ['TestStack1']}
    cdk_template_mock['Resources']['MyResource']['Properties']['BucketName'] = [
        {'Fn::ImportValue': 'MyExportedBucket1'},
    ]

    template_path = cdk_out_mock / 'test-stack-1.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    actual = get_cdk_out_imports(cdk_out_mock)
    assert actual == expected


def test_get_cdk_out_raises_error_if_no_cdk_out_file_in_folder(cdk_out_mock):
    cdk_out_file = Path(cdk_out_mock / 'cdk.out')
    assert cdk_out_file.is_file  # to confirm we are removing the file, not directory with the same name
    cdk_out_file.unlink(missing_ok=False)

    with pytest.raises(
        InvalidCdkOutPathError, match='unable to find CDK stack synthesis output in provided directory, did you synth?'
    ):
        get_cdk_out_imports(cdk_out_mock)


def test_get_cdk_out_raises_error_if_no_cdk_out_folder(cdk_out_mock):
    shutil.rmtree(cdk_out_mock)

    with pytest.raises(InvalidCdkOutPathError, match="path doesn't exist"):
        get_cdk_out_imports(cdk_out_mock)


def test_get_cdk_out_raises_error_if_pointing_to_file(cdk_out_mock):
    with pytest.raises(InvalidCdkOutPathError, match='path must be a directory'):
        get_cdk_out_imports(cdk_out_mock / 'cdk.out')


def test_get_cdk_out_adds_cdk_out_dir_if_not_already_there(cdk_out_mock, tmp_path, mock_walk):
    """
    example is infra/ being passed instead of infra/cdk.out, simply append cdk.out/
    """
    get_cdk_out_imports(tmp_path)
    mock_walk.assert_called_once_with(cdk_out_mock)


def test_get_cdk_out_imports_with_two_stacks(cdk_out_mock, cdk_template_mock, cdk_manifest_mock):
    expected = {'MyExportedBucket1': ['TestStack1'], 'MyExportedBucket2': ['TestStack2']}

    cdk_template_mock['Resources']['MyResource']['Properties']['BucketName']['Fn::ImportValue'] = 'MyExportedBucket2'
    template_path = cdk_out_mock / 'test-stack-2.template.json'
    with template_path.open('w') as f:
        json.dump(cdk_template_mock, f)

    cdk_manifest_mock['artifacts']['test-stack-2'] = {
        'displayName': 'TestStack2',
    }
    manifest_path = cdk_out_mock / 'manifest.json'
    with manifest_path.open('w') as f:
        json.dump(cdk_manifest_mock, f)

    actual = get_cdk_out_imports(cdk_out_mock)
    assert actual == expected


@pytest.mark.skip
def test_get_cdk_out_imports_with_stages():
    """TODO: determine what the expected structure is"""

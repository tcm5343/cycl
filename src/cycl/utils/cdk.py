from __future__ import annotations

import json
from os import walk
from pathlib import Path
from logging import getLogger

log = getLogger(__name__)


class InvalidCdkOutPathError(Exception):
    def __init__(self, message: str = 'An error occurred') -> None:
        super().__init__(message)


def __find_import_values(data: dict) -> list[str]:
    """recursively search for all 'Fn::ImportValue' keys and return their values"""
    results = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'Fn::ImportValue':
                results.append(value)
            else:
                results.extend(__find_import_values(value))

    elif isinstance(data, list):
        for item in data:
            results.extend(__find_import_values(item))

    return results


def __get_import_values_from_template(file_path: Path) -> list[str]:
    """todo: handle yaml templates too"""
    with Path.open(file_path) as f:
        json_data = json.load(f)
    return __find_import_values(json_data)


def __get_stack_name_from_manifest(path_to_manifest: Path, template_file_name: str) -> str:
    with Path.open(path_to_manifest) as f:
        json_data = json.load(f)
    return json_data['artifacts'][template_file_name.split('.')[0]]['displayName']


def __validate_cdk_out_path(cdk_out_path: Path) -> Path:
    errors = []
    if Path.exists(cdk_out_path):
        if not cdk_out_path.is_dir():
            errors.append('path must be a directory')
    else:
        errors.append("path doesn't exist")

    # handle if path is where cdk.out/ is or is directly to cdk.out
    if Path(cdk_out_path).name != 'cdk.out':
        cdk_out_path = Path(cdk_out_path) / 'cdk.out'

    if not Path.exists(Path(cdk_out_path) / 'cdk.out'):
        errors.append('unable to find CDK stack synthesis output in provided directory, did you synth?')

    if errors:
        errors_formatted = '\n\t - '.join(errors)
        error_message = f'Invalid path provided for --cdk-out {cdk_out_path}:\n\t - {errors_formatted}'
        raise InvalidCdkOutPathError(error_message)

    return cdk_out_path


def get_cdk_out_imports(cdk_out_path: Path) -> dict[str, list[str]]:
    """
    map an export name to a list of stacks which import it

    function does not take into consideration exports
        - if we found an export, we may not be able to resolve the name of it
        - AWS has built in circular dependency detection inside of a stack
        - a circular dependency couldn't be introduced in a single deployment
    """
    cdk_out_path = __validate_cdk_out_path(cdk_out_path)

    stack_import_mapping = {}
    for root, _dirs, files in walk(cdk_out_path):
        for file in files:
            if file.endswith('template.json'):
                imported_export_names = __get_import_values_from_template(Path(root) / file)
                if imported_export_names:
                    manifest_path = Path(root) / 'manifest.json'
                    stack_name = __get_stack_name_from_manifest(manifest_path, file)
                    for export_name in imported_export_names:
                        stack_import_mapping.setdefault(export_name, []).append(stack_name)
    return stack_import_mapping

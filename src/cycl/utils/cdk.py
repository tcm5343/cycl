from __future__ import annotations

import json
from logging import getLogger
from pathlib import Path

from cycl.models.node_data import NodeData

log = getLogger(__name__)


class InvalidCdkOutPathError(Exception):
    def __init__(self, message: str = 'An error occurred') -> None:
        super().__init__(message)


def __find_import_values(data: dict) -> list[str]:
    """Recursively search for all 'Fn::ImportValue' keys and return their values."""
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
    """todo: handle yaml templates too."""
    with Path.open(file_path) as f:
        json_data = json.load(f)
    return __find_import_values(json_data)


def __get_stack_name_from_manifest(path_to_manifest: Path, template_file_name: str) -> str:
    """Grabs the stack name, if set, or parses stack name from the displayName (construct id) of the stack."""
    with Path.open(path_to_manifest) as f:
        json_data = json.load(f)

    artifact_id = template_file_name.split('.')[0]
    artifact = json_data['artifacts'].get(artifact_id)
    if not artifact:
        log.warning('No artifact found in manifest for %s', template_file_name)
        return ''

    stack_name = artifact.get('properties', {}).get('stackName')
    display_name_split = artifact.get('displayName', '').split('/')[-1]
    return stack_name or display_name_split


def __validate_cdk_out_path(cdk_out_path: Path) -> Path:
    cdk_out_path = Path(cdk_out_path).resolve()
    if not cdk_out_path.exists() or not cdk_out_path.is_dir():
        err_msg = f'Provided path does not exist or is not a directory: {cdk_out_path}'
        raise InvalidCdkOutPathError(err_msg)

    # handle if path is where cdk.out/ is or is directly to cdk.out
    if cdk_out_path.name != 'cdk.out':
        cdk_out_path = cdk_out_path / 'cdk.out'

    if not (cdk_out_path / 'cdk.out').exists():
        err_msg = f'File named cdk.out not found in {cdk_out_path}. Did you run `cdk synth`?'
        raise InvalidCdkOutPathError(err_msg)

    return cdk_out_path


def get_exports_from_assembly(cdk_out_path: Path) -> dict[str, list[NodeData]]:
    """Map an export name to a list of stacks which import it from the cloud assembly.

    function does not take into consideration exports defined in the assembly
        - if we found an export, we may not be able to resolve the name of it
        - AWS has built in circular dependency detection inside of a stack
        - a circular dependency couldn't be introduced in a single deployment
    """
    cdk_out_path = __validate_cdk_out_path(cdk_out_path)

    stack_import_mapping: dict[str, list[NodeData]] = {}
    for template_file in cdk_out_path.rglob('*.template.json'):
        log.info('Processing template: %s', template_file)
        imported_export_names = __get_import_values_from_template(template_file)

        log.info('found imported export names: %s', imported_export_names)
        if imported_export_names:
            manifest_path = template_file.parent / 'manifest.json'
            log.info('looking in manifest: %s', manifest_path)
            stack_name = __get_stack_name_from_manifest(manifest_path, template_file.name)
            if not stack_name:
                log.warning('unable to determine stack name for template: %s', template_file.name)
                continue
            log.info('stack name found: %s', stack_name)
            for export_name in imported_export_names:
                stack_import_mapping.setdefault(export_name, []).append(
                    NodeData(
                        stack_name=stack_name,
                        export_name=export_name,
                    )
                )
    return stack_import_mapping

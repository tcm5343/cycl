#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/../e2e/infra"
export PYTHONPATH=.

rm -rf ./cdk.out
uv run cdk synth --output cdk.out
uv run cdk deploy --app cdk.out 'CyclicStage/**' --ci --require-approval never
uv run cdk deploy --app cdk.out 'AcyclicStage/**' --ci --require-approval never
uv run cdk destroy 'CyclicStage/**' --ci --force
uv run cdk destroy 'AcyclicStage/**' --ci --force
uv run cdk destroy BootstrapE2EStack --ci --force

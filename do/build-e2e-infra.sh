#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")/../e2e/infra"
export PYTHONPATH=.

rm -rf ./cdk.out
uv run cdk synth --output cdk.out
uv run cdk deploy --app cdk.out 'CyclicStage/**' --ci --require-approval never
uv run cdk deploy --app cdk.out 'AcyclicStage/**' --ci --require-approval never
uv run cdk deploy --app cdk.out BootstrapE2EStack --ci --require-approval never

rm -rf ./cdk.out
uv run cdk synth --output cdk.out -c create_cycle=true
uv run cdk deploy --app cdk.out 'CyclicStage/**' --ci --require-approval never
uv run cdk deploy --app cdk.out 'AcyclicStage/**' --ci --require-approval never

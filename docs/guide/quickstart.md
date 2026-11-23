# Quickstart

## Install

To use the CLI, install `cycl` as a tool with [uv](https://docs.astral.sh/uv/), or run it without installing:

```bash
uv tool install cycl
cycl check

# or, without installing
uvx cycl check
```

To use the Python SDK, add `cycl` as a dependency of your project:

```bash
uv add cycl
```

`cycl` can also be installed with `pip install cycl`.

## Permissions

The credentials used need the following IAM permissions:

- `cloudformation:ListExports`
- `cloudformation:ListImports`

## Run

`cycl` reads the CloudFormation exports and imports from the AWS account and region your credentials resolve to
(using the standard `boto3` credential chain, e.g. `AWS_PROFILE` and `AWS_REGION`).

```bash
# exit non-zero if a cycle is found
cycl check

# print the order stacks can be deployed in, if there are no cycles
cycl topo
```

If a cycle is found, each one is printed as `cycle found between nodes: [...]`. `cycl check` then exits with
status `2`, unless `--exit-zero` is passed. `cycl topo` exits with `2` if the graph is cyclic, otherwise it prints
one generation per line, with the stacks in each generation separated by a space.

Pass `--format json` for machine-readable output: `cycl check` prints `{"cycles": [...]}` and `cycl topo` prints
`{"cycles": [...], "generations": [...]}` (`generations` is `null` when the graph is cyclic). Logs are written to
stderr, so stdout only contains the result.

| Exit code | Meaning                                                                                  |
|-----------|------------------------------------------------------------------------------------------|
| `0`       | No cycles found (or `--exit-zero` was passed to `check`)                                 |
| `1`       | An error occurred, e.g. invalid usage or an AWS error                                    |
| `2`       | A cycle was found                                                                        |

Any unexpected error exits `1`, so a non-zero exit is only a cycle when it is `2`. In CI, `cycl check` fails the
step either way; check for `2` explicitly if you need to tell a cycle apart from a failure to run.

Run `cycl --help` or see the [CLI reference](../reference/reference.md) for all options, and the
[tutorial](../tutorial/how.md) for CI/CD usage.

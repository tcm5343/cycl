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
- `cloudformation:DescribeStacks`, only to fetch stack ARNs and tags with the Python SDK (`fetch_exports(describe_stacks=True)`)

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
status `3`, unless `--exit-zero` is passed. `cycl topo` exits with `3` if the graph is cyclic, otherwise it prints
one generation per line, with the stacks in each generation separated by a space.

Pass `--format json` for machine-readable output: `cycl check` prints `{"cycles": [...]}` and `cycl topo` prints
`{"cycles": [...], "generations": [...]}` (`generations` is `null` when the graph is cyclic). Logs are written to
stderr, so stdout only contains the result.

| Exit code | Meaning                                                    |
|-----------|------------------------------------------------------------|
| `0`       | No cycles found (or `--exit-zero` was passed to `check`)   |
| `1`       | An error occurred while running, e.g. an AWS error         |
| `2`       | Invalid usage, e.g. an unknown argument                    |
| `3`       | A cycle was found                                          |

Only a cycle exits `3`, so check for it explicitly if you need to tell a cycle apart from a failure to run. In CI,
any non-zero exit fails the step.

Run `cycl --help` or see the [CLI reference](../reference/reference.md) for all options, and the
[tutorial](../tutorial/how.md) for CI/CD usage.

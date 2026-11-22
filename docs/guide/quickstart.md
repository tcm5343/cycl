# Quickstart

## Install

It is recommended to use `pipx` to install `cycl`, but you can also use `pip` by running `pip install cycl`.

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
status `1`, unless `--exit-zero` is passed. `cycl topo` exits with `1` if the graph is cyclic.

Run `cycl --help` or see the [CLI reference](../reference/reference.md) for all options, and the
[tutorial](../tutorial/how.md) for CI/CD usage.

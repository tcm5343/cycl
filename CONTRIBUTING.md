# Contributing to cycl

Bug reports, feature requests, and pull requests are all welcome.

## Reporting issues

Open an issue on [GitHub](https://github.com/tcm5343/cycl/issues). For bugs, include:

- the `cycl` version (`pip show cycl`) and Python version
- the command or SDK call you ran, and its output (run with `--log-level DEBUG` for more detail)
- what you expected to happen

Redact any values you don't want to share.

## Making changes

1. Fork the repository and create a branch from `main`.
2. Make your change, with tests.
3. Run the checks below and make sure they pass.
4. Open a pull request against `main` describing what changed and why.

### Formatting, linting, and types

```bash
make format     # ruff format + ruff check --fix
make validate   # ruff format --check, ruff check, mypy
```

Ruff runs with almost every rule enabled (see `[tool.ruff]` in `pyproject.toml`). Code uses single quotes, a line
length of 125, and Google-style docstrings. `src/` is type checked with mypy, so annotate new code.

### Unit tests

```bash
make test         # runs both the lowest and latest allowed versions of direct dependencies
```

### Documentation

```bash
make doc-serve   # live-reloading docs at http://127.0.0.1:8000
```

CI builds the docs with warnings treated as errors (`sphinx-build -W`), so check the build output for warnings.
Update the docs alongside any user-facing change:

## End-to-end tests

The e2e tests run `cycl` against real stacks in AWS: an acyclic set in `us-east-1` and a cyclic set in `us-west-2`.
They need AWS credentials and an account bootstrapped for CDK, so they are optional for contributors. CI runs them
against a wheel built from each pull request opened from a branch of this repository (not forks), and against every
release before it is published to PyPI. Both need a maintainer to approve the `aws` environment.

To run them in your own account:

```bash
make build-e2e-infra     # deploy the stacks (requires the AWS CDK CLI: npm install -g aws-cdk)
make run-e2e             # run e2e/tests/ against them, using cycl built from this source tree
make destroy-e2e-infra   # tear them down
```

`make run-e2e` runs in a throwaway environment, so it doesn't touch `.venv`. To test something other than the source
tree, pass it as `CYCL_SPEC`, e.g. a built wheel (`CYCL_SPEC=dist/cycl-1.2.3-py3-none-any.whl`) or a release from PyPI
(`CYCL_SPEC=cycl==1.2.3`).

Creating the cycle requires deploying the stacks twice, which `build-e2e-infra` does for you.

## Releases

Releases are automated. Every merge to `main` that passes CI:

1. bumps the version and tags it (`vX.Y.Z`), creating a GitHub release with generated notes,
2. runs the e2e tests against the built wheel and publishes it to Test PyPI,
3. publishes it to PyPI and redeploys the docs.

The version bump is a patch by default. Include `#minor` or `#major` in the commit message merged to `main` (the pull
request title or description, when squash merging) for a larger bump. The package version comes from the git tag, so
don't set it anywhere by hand.

Pull request titles follow a loose [Conventional Commits](https://www.conventionalcommits.org/) style, e.g.
`feat: ...`, `fix: ...`, `chore: ...`, `docs: ...`.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

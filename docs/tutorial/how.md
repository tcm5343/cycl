# How to use cycl?

There are two main use cases for `cycl`.

## CI/CD via the CLI

`cycl` is best used to detect circular dependencies in your CI/CD pipeline; this ensures that if `cycl` detects a circular dependency, it will prevent the pipeline from passing.

`cycl` reads what is already deployed, so a cycle is detected after the deployment that introduced it. Run `cycl check` after each deployment, so the pipeline fails before anything else is built on top of the cycle. Pre-deployment checks, which would detect a cycle before it is deployed, are a planned feature.

## Custom Analysis via the SDK

The CLI may be limiting when you're trying to perform advanced analysis on your dependencies. This is why `cycl` exposes the functions that the CLI uses through Python, see the [SDK reference](../reference/sdk.md).

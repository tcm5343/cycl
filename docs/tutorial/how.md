# How to use cycl?

There are two main use cases for `cycl`.

## CI/CD via the CLI

is best used to detect circular dependencies in your CI/CD, this ensures that if `cycl` detects a circular dependency, it will prevent the pipeline from passing. Note that this currently only works post deployment.

Pre-deployment checks are the goal. This is hard be If you're using the AWS CDK v2 (v1 support coming soon), simply synthesize you templates to a directory and pass that directory to `cycl` using `--cdk-out-path some-path-here`. This allows `cycl` to find all existing cycles and then those to be introduced by the deployment. This prevents the circular dependency from ever being introduced. If your pipeline deploys more than once, you should execute `cycl` before each deployment.

## Custom Analysis via the SDK

The CLI may be limiting when you're trying to perform advanced analysis on your dependencies. This is why `cycl` exposes the functions that the CLI uses through Python. As the implementation becomes more stable, they will be exposed.

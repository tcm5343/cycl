# cycl

Over the lifetime of a project, circular dependencies may be introduced accidentally. While AWS detects circular dependencies within a stack, cross stack circular dependencies can slip by undetected until the infrastructure needs to change.

An example is disaster recovery testing and potentially needing to deploy all your infrastructure from scratch in a new region. `cycl` detects those cross stack circular dependencies when they are introduced.

```{toctree}
:maxdepth: 2
:caption: Content:

guide/quickstart
tutorial/how
reference/reference
```

# TODO.md

- output the topological generations of the graph
  - `cycl check --generations`
- ignoring known cycles, [this](https://cs.stackexchange.com/questions/90481/how-to-remove-cycles-from-a-directed-graph) may help
  - `cycl check --ignore-cycle-contains`
  - `cycl check --ignore-cycle`
- reducing the stacks, for example, a tag on a stack representing the github repo name
  - `cycl check --reduce-dependencies-on`
  - `cycl check --reduce-generations-on`

- [ ] [fully configure dependabot](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/automating-dependabot-with-github-actions)
- [ ] configure make file
- [ ] dprint for other file formatting
- [ ] automatic release versioning for pypi, run unit tests against package? Is this possible?
- [ ] configuration file using cli, use toml, custom rc file, env vars?
- [ ] CDK v1 support
- [ ] Test with stages that the correct manifest is analyzed
- [ ] What if cdk out synth is for multiple accounts? We may need to determine what account we have credentials for and only analyze those templates
- [ ] automatic documentation generation

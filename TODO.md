# TODO.md

- ignoring known cycles, [this](https://cs.stackexchange.com/questions/90481/how-to-remove-cycles-from-a-directed-graph) may help
  - `cycl check --ignore`
  - `cycl topo --ignore`
- reducing the stacks, for example, a tag on a stack representing the github repo name
  - `cycl check --reduce-on`
  - `cycl check --reduce-on-jq`
  - `cycl check --reduce-on-jmespath`
  - `cycl topo --reduce-on {rootstack}` # can we resolve the root stack through cdk.out

- [ ] [fully configure dependabot](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/automating-dependabot-with-github-actions)
- [ ] configure make file
- [ ] dprint for other file formatting
- [ ] automatic release versioning for pypi, run unit tests against package? Is this possible?
- [ ] configuration file using cli, use toml, custom rc file, env vars?
- [ ] CDK v1 support
- [ ] Test with stages that the correct manifest is analyzed
- [ ] What if cdk out synth is for multiple accounts? We may need to determine what account we have credentials for and only analyze those templates
- [ ] automatic documentation generation
- [ ] configure tox

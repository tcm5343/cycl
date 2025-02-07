# TODO.md

- [ ] [fully configure dependabot](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/automating-dependabot-with-github-actions)
- [ ] configure make file
- [ ] dprint for other file formatting
- [ ] automatic release versioning for pypi, run unit tests against package? Is this possible?
- [ ] isort
- [ ] configuration file using cli, use toml, custom rc file, env vars?


Next steps:
1. Add `cycl --check` as first feature, publish v1.0.0 to pypi
2. Add ability to ignore known cycles, how to break the cycle?
3. Add ability to reduce via tags, check out jquery --reduce-on maybe?

# ruff check --fix  # to fix

cycl check
cycl check --exit-zero

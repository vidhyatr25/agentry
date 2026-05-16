## Summary
<!-- One-line summary of the change. -->

## What changed
<!-- Specific list of changes. -->
-
-
-

## Type
- [ ] Bug fix
- [ ] New feature
- [ ] New plugin (provider / tool / publisher / step)
- [ ] Docs / examples
- [ ] CI / infra
- [ ] Refactor

## Checklist
- [ ] `python -m pytest tests/ -q` passes locally
- [ ] If a new plugin: included a test in `tests/`
- [ ] If a new workflow: `python -m agentry.cli validate workflows/yours.json` passes
- [ ] No secrets in the diff; secrets referenced as `${ENV_NAME}` only
- [ ] `CHANGELOG.md` updated under an *Unreleased* section
- [ ] Updated relevant docs (`README.md`, `docs/*`) if user-facing

## Notes for reviewer
<!-- Tradeoffs, alternatives, follow-ups. -->

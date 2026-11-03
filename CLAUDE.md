# Claude Code

pstack model settings (edit that file to change them):
@.claude/pstack-models.md

## Monid (cloud sessions)

The `monid` skill lives in `.claude/skills/monid/`. Cloud containers start fresh, so before using it:

1. If `monid` is missing, install it: `npm install -g @monid-ai/cli@latest`.
2. If `monid keys list` shows no key, load it from the environment: `monid keys add -k "$MONID_API_KEY" -l main`. Never print the key or ask for it in chat.

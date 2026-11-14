# Security

## Reporting a problem

Please report security or privacy problems **privately** through GitHub:
**Security → Report a vulnerability** on this repository. Don't open a public
issue for them.

Examples of what to report:

- A skill instruction that could lead Claude to take an unsafe action
- Personal, employer or other sensitive data committed to the repository
- A problem in the scripts under `scripts/` or the CI workflow

You can expect an acknowledgment within a week. This is a single-maintainer
project, so fixes are best-effort.

## How this repository protects itself

- **No sensitive data in content.** A privacy check runs in pre-commit and CI;
  see `CLAUDE.md` → "Public-ready and private-free".
- **Least-privilege CI.** Workflows read the repository only.
- **Pinned tooling.** Dev tool versions are pinned and kept current by
  Dependabot.

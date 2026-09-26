# Contributing — Branching Strategy & Workflow

Agreed for the 4-week competition build. Small repo, 5 people: keep the rules short and follow them exactly.

## 1. Branching Strategy — trunk-based

- `main` is the only long-lived branch. **Never push directly to `main`.**
- Branch off the latest `main` for every piece of work.
- Branch naming: `<type>/<ticket>-<short-slug>`

  | type | use for |
  | --- | --- |
  | `feat` | new functionality |
  | `fix` | bug fixes |
  | `test` | test cases, QA artifacts, test fixtures |
  | `docs` | documentation-only changes |
  | `chore` | repo/CI/tooling setup |

  Examples: `feat/12-review-screen-shell`, `test/18-contraindication-cases`.

- If there is no ticket yet, create the issue first. No orphan branches.
- Delete branches after merge.

## 2. Commits & Pull Requests

- Commit messages: imperative mood, concise, reference the issue (`Add review screen shell (#12)`).
- Small, frequent commits. Do not batch a whole day into one commit.
- Every branch becomes a PR. **At least one review from a different teammate** before merge.
- PR title must state what changed and why. Link the issue with `Closes #12`.
- Resolve review comments before merge; do not self-approve.

## 3. Project Board Workflow

All work is a GitHub issue on the project board. Columns:

`Backlog` → `This Week` → `In Progress` → `Review` → `Done`

- Move your own tickets as status changes — the board is the daily standup.
- A ticket sits in `In Progress` only while someone is actively on it.
- `Done` requires merged code (or, for docs/QA artifacts, committed to `main`).

## 4. Roles & Ownership

| Role | Owns |
| --- | --- |
| A — ML Engineer | datasets, training, inference |
| B — Backend Engineer | schema, API, recommendation engine |
| C — Frontend Engineer | React app, review/confirmation screens |
| D — Integration/QA | repo health, board, test cases, demo script |
| E — Team Lead / Clinical Liaison | dentist meeting, validated clinical tables, risk log |

Cross-role changes (e.g. Backend editing `docs/qa/`) require a ping to the owner first.

## 5. Documentation Rules

- `docs/` is the source of truth. If it isn't documented, it isn't agreed.
- Clinical tables (finding-to-treatment, drug list, contraindications) are owned by the Team Lead and can only be edited from validated dentist output. Mark anything unvalidated with **`UNVALIDATED`**.
- No real patient data anywhere in this repo — synthetic/anonymized only.

## 6. What Must Never Land

- Drug-interaction API clients (endpoint retired — see README)
- 3D visualization code
- Patient-app / NFC code
- Custom image annotation tooling
- Live model retraining infrastructure

See [docs/Week1_Execution_Plan.md](docs/Week1_Execution_Plan.md) §8 for the full list.

# Repository cleanup — 2026-11

What was reorganised, what was removed, and what was deliberately left alone.
Behaviour was held constant: the locked-50 benchmark output is byte-identical
before and after, and the frozen pipeline returns the same JSON for a fixture
image.

## Branch

Everything below landed on `refactor/full-clean`, branched from `develop`
(`83abc72`). `develop` itself was not touched.

## The ML service: `dentex_week3/` → `ml/`

| Before | After |
| --- | --- |
| `dentex_week3/production/inference_pipeline.py` | `ml/pipeline/inference.py` |
| `dentex_week3/production/pipeline_config.json` | `ml/pipeline/pipeline_config.json` |
| `dentex_week3/production/*.pt` | `ml/weights/*.pt` (untracked) |
| `dentex_week3/production/weights.sha256` | `ml/weights/weights.sha256` |
| `dentex_week3/production/final_evaluation.json` | `ml/eval/final_evaluation.json` |
| `dentex_week3/api/` | `ml/service/` |
| `dentex_week3/evaluate.py` | `ml/eval/evaluate.py` |
| `dentex_week3/paired_significance.py` | `ml/eval/significance.py` |
| `dentex_week3/{rerank_caries,pick_caries_threshold,missing_teeth_*}.py` | `ml/research/` |
| `dentex_week3/verify_setup.py` | `ml/tools/verify_setup.py` |
| `dentex_week3/tests/` | `ml/tests/` |

Generated evidence files (`evaluation_report_v*.md`, `*.json`, `*.jsonl`) keep
their names: `submission/FACTS.md` and `submission/VERIFICATION.md` cite them by
filename.

Every consumer was updated in the same commit: `docker-compose.yml`,
`deploy/ml.Dockerfile`, `deploy/cloudbuild.yaml`, `.github/workflows/ci.yml`,
the six `notebooks/fetch_*.sh` scripts, the seven training notebooks,
`backend/start.sh` and the backend path references, `scripts/demo_check.sh`,
`.gcloudignore`, `.gitignore`, and the living docs.

## Removed

| Item | Why |
| --- | --- |
| `datasets/` (4.9 GB) | moved to `~/Projects/dental-model-research/data/dentex_yolo`; see `docs/DATASETS.md` |
| `archive/` (129 MB) | v1/v2 freeze; v1 is recoverable from tag `ml-v1-baseline` |
| `runs/` (48 MB) | stray Ultralytics predict output |
| `.env.cloud.bak` | ignored backup |
| `ml/` (v1 model card + report) | moved to `docs/history/` |
| `MLv2/` (v2 report + training logs) | moved to `docs/evidence/mlv2/` |
| `docs/PHASE2..6_STATUS.md` | moved to `docs/history/` |
| `CHANGELOG_MODEL_SWITCH.md` | moved to `docs/history/` |
| `ml/service/venv/` (5.9 GB) | local venv, never tracked; recreate after the rename |

Nothing was deleted that cannot be recovered: tracked deletions are all moves
(git records them as renames), and the ignored directories are reproducible.

## Code quality

- `ml/eval/metrics.py` is the single home for `iou`, `greedy_match`,
  `wilson_ci`, `fmt_pct`, `average_precision`, `prf` and `macro_mean`. Three
  copies of the box maths and AP integration are gone.
- `evaluate()` (218 lines) is split into `collect_stats()` (one pass) plus
  `detection_metrics()` / `label_metrics()` / `sweep_metrics()` and a thin
  orchestrator.
- `pyproject.toml` holds the ruff + black + pytest configuration; `ruff check`
  and `black --check` are clean across `backend/`, `ml/` and `scripts/`.
- CI gained a `lint` job and a coverage report on the ML tests.
- `requirements-dev.txt` pins the dev tooling.
- The service uses `logging` instead of `print`, and every `HTTPException`
  raised inside an `except` block chains its cause.

## Deliberately not done

| Improvement | Why it waits |
| --- | --- |
| Renaming the shipped endpoint/response fields | The v3 output contract is frozen and validated; a rename invalidates the recorded numbers |
| `PipelineConfig` dataclass instead of `CONFIG.get()` lookups | Touches the frozen pipeline for no measurable gain |
| Batched `/predict/batch` endpoint | Real win for 250-image evaluation, but new behaviour before the conference |
| Structured JSON logging with request IDs | Needs a logging design decision across backend + ML service |
| Coverage gate | Needs an agreed baseline; the pipeline requires torch, so unit coverage is inherently partial |
| Pre-commit hooks | Duplicates CI; worth adding once the lint config has settled |
| Dependency lock file (`uv.lock`) | Should be introduced together with a reproducible demo install, not mid-cleanup |
| Multi-stage Docker build | Image size is not a bottleneck today |
| TS types generated from the Pydantic schemas | Cross-cutting change across backend and frontend |

## Verification performed

```bash
# locked-50 benchmark, before vs after
diff <(evaluation_results.json before) <(evaluation_results.json after)   # identical
diff <(evaluation_report.md after) ml/eval/evaluation_report_v3.md        # identical

# frozen pipeline on one fixture image
diff <(pipeline JSON before) <(pipeline JSON after)                       # identical

# weights: the release assets match weights.sha256 and are tensor-identical
# to the local training outputs (byte-different, all tensors element-wise equal)
gh release download weights-v3 --pattern '*.pt' --dir /tmp/relcheck
(cd /tmp/relcheck && sha256sum -c .../ml/weights/weights.sha256)          # OK

pytest -q ml/tests        # 37 passed, 1 xfailed
pytest -q backend/tests   # 176 passed
npm run typecheck && npm test   # 29 passed
ruff check ... && black --check ...
```

The one xfail documents a **known defect** in `average_precision`: it divides
recall by the number of matched positives instead of the ground-truth count, so
it returns the class precision. The reported `mAP@0.5 = 54.2` is therefore mean
per-class precision; the true VOC-style value on the same predictions is 60.9.
That is a metric bug, not a refactor artefact, and it is left for a separate,
explicit decision because fixing it moves every published number.

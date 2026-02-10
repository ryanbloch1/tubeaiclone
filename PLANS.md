# TubeAI Clone Stabilization Plan (phase2)

Date: 2026-02-10
Branch: phase2

## Checklist
- [x] PR1: Build + runtime baseline + planning artifact
- [x] PR2: Contract consistency (status + ownership + types)
- [x] PR3: SSE streaming + URL normalization + dead code prune

## Known Risks
- API/runtime depends on Supabase env vars at runtime (`SUPABASE_URL`, keys) and warns/fails when missing.
- No authenticated E2E flow coverage yet; current smoke tests validate anonymous and public route behavior.
- FastAPI models still use Pydantic V1 `@validator` APIs (deprecation warnings under Pydantic V2).

## Verification Log
- 2026-02-10: `cd apps/web && npm run lint` passes with no warnings.
- 2026-02-10: `cd apps/web && npm run build` succeeds.
- 2026-02-10: `cd apps/web && npm run test:e2e -- --list` discovers 3 Playwright tests.
- 2026-02-10: `cd apps/web && npm run test:e2e -- tests/e2e` passes (3/3).
- 2026-02-10: `cd apps/api && python -m unittest discover -s tests` passes (2 tests).
- 2026-02-10: `python -c "import apps.api.main"` completes (warns when Supabase env vars are unset).
- 2026-02-10: `cd apps/api && python -c "import main, routes.images, routes.video, routes.script, routes.voiceover, routes.projects"` succeeds.

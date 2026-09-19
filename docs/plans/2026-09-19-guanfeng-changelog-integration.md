# Guanfeng Changelog Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate the behavior changes listed in Guanfeng's changelog into the official `source/` Skill while preserving all existing official behavior and every existing version identifier.

**Architecture:** Extend the current Builder rather than replacing it. Add an isolated decision-validation module, feed it persisted executed-plan snapshots, then layer human interaction and settlement onto the existing probe, pacing, company-research, and reporting flows.

**Tech Stack:** Python 3 standard library, JSON workflow assets, Markdown Skill contracts, `unittest`.

---

### Task 1: Establish Builder regression coverage

**Files:**
- Create: `tests/test_build_workflow.py`

1. Write tests that import `source/scripts/build_workflow.py`, construct isolated task/workflow stores, and compile representative preflight, search, and company-probe workflows from the official assets.
2. Assert that probe compilation and pacing remain present. Add one expectation for the missing `human` interaction mode.
3. Run `python3 -m unittest tests.test_build_workflow -v`; expect only the new human-mode assertion to fail.
4. Commit with `git commit -m "test: cover official workflow builder"`.

### Task 2: Add human and direct interaction modes

**Files:**
- Modify: `source/scripts/build_workflow.py`
- Modify: `source/assets/channel/liepin.json`
- Modify: `source/assets/workflows/preflight.json`
- Modify: `source/assets/workflows/search.json`
- Modify: `source/assets/workflows/detail.json`
- Modify: `tests/test_build_workflow.py`

1. Add failing tests for a `human` channel default, explicit `direct` override, the `interaction.human.v1` requirement, and bounded detail-browse steps.
2. Run `python3 -m unittest tests.test_build_workflow -v`; expect failures for missing interaction metadata or CLI arguments.
3. Port only the interaction-mode fields, CLI option, required capability, and detail browse program. Keep `pace_preflight`, `pace_search_path`, probe workflow, round limits, and version constants unchanged.
4. Re-run the focused tests; expect PASS.
5. Commit with `git commit -m "feat: add selectable human browser interaction"`.

### Task 3: Add deterministic decision validation

**Files:**
- Create: `source/scripts/decision_basis.py`
- Create: `tests/test_decision_basis.py`
- Modify: `source/scripts/build_workflow.py`
- Modify: `source/references/search-plan.md`

1. Write failing tests for deterministic weighted scores, Top 10 ordering, same-version criteria drift, score-history preservation, content-addressed results, PRF transitions, and correction reasons.
2. Run `python3 -m unittest tests.test_decision_basis -v`; expect import failure because the module does not exist.
3. Add the decision validator as an isolated module, preserving task scoping, size checks, hashes, and field validation.
4. Allow additive `requirement_version` and `decision_basis` plan fields. Require decision history only after the first completed round.
5. Run `python3 -m unittest tests.test_decision_basis tests.test_build_workflow -v`; expect PASS.
6. Commit with `git commit -m "feat: validate reusable WTS decisions"`.

### Task 4: Trust the executed plan and add settlement

**Files:**
- Modify: `source/scripts/build_workflow.py`
- Modify: `tests/test_build_workflow.py`
- Modify: `tests/test_decision_basis.py`
- Modify: `source/references/search-plan.md`

1. Write failing tests for embedded `input_plan`, prior executed-plan loading, resistance to edited historical plan files, `settle --iteration N`, mode `0600` report output, and no extra search round.
2. Run the two focused test modules; expect failures for missing snapshots, settlement, or report output.
3. Port content-addressed workflow loading, plan snapshots, and settlement while preserving official probe and pacing logic. Do not change any version constant.
4. Re-run focused tests; expect PASS.
5. Commit with `git commit -m "feat: settle searches from executed plans"`.

### Task 5: Update the official Skill contract

**Files:**
- Modify: `source/SKILL.md`
- Modify: `source/references/scoring.md`
- Modify: `source/references/final-report.md`
- Modify: `source/references/search-plan.md`
- Create: `tests/test_skill_contract.py`

1. Write failing contract tests for interaction modes, requirement/score reuse, paginated result reading with `next_offset`, `write_file` versus `edit_file`, confirmation form boundaries, `settle`, absence of `reflect`, and final report-data consumption.
2. Include preservation assertions for target-company research, company probe, pacing, and the current final-report workflow.
3. Run `python3 -m unittest tests.test_skill_contract -v`; expect failures only for the new contract.
4. Merge the relevant collaborator guidance into the existing official SOP and references without replacing whole documents.
5. Run `python3 -m unittest discover -s tests -v`; expect PASS.
6. Commit with `git commit -m "docs: integrate WTS execution safeguards"`.

### Task 6: Final validation and delivery

**Files:**
- Verify all modified files.

1. Run `python3 -m py_compile source/scripts/*.py`.
2. Run `find source -name '*.json' -print0 | xargs -0 -n1 python3 -m json.tool >/dev/null`.
3. Run `git diff --check origin/main...HEAD`.
4. Run `python3 -m unittest discover -s tests -v`.
5. Audit scope with `git diff --stat origin/main...HEAD` and verify that no version identifiers, frozen packages, or existing official capabilities changed.
6. Push `integrate-guanfeng-changelog` and open a reviewable PR against `main`; report the URL and checks without auto-merging it.

All validation commands must exit 0 before delivery.

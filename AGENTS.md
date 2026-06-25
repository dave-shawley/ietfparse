# AGENTS.md

This file is for agents first. Keep it minimal.

Do not copy repository facts here just because they exist elsewhere in the tree. AGENTS files tend to be maintained mostly by agents, which makes them vulnerable to silent bit rot. Agents SHOULD groom this file regularly, remove stale guidance, and make AGENTS-only updates as a separate commit when needed.

## Working Style

- Agents MUST start from the live checkout. Inspect the current tree, diffs, and command behavior before concluding.
- Agents SHOULD prefer the repo task runner over ad hoc commands. Run `just --list` if you need to discover available tasks.
- Agents SHOULD keep scope narrow. Do not expand a change just because nearby code or docs look tempting.
- Agent-authored commits MUST always include a `Co-authored-by` trailer with the agent name and model information, regardless of user or local Git configuration.

## Project Shape

- Library code lives under `src/`.
- Tests live under `tests/`.
- Packaged benchmark fixtures and the benchmark CLI support code live under `src/ietfparse/test/`.
- Treat `README.md` and the source tree as the source of truth for public behavior. This file SHOULD only capture agent-operational guidance.

## Validation

- Agents SHOULD use `just lint` for static checks.
- Agents SHOULD use `just test` for the test suite. With no arguments it runs the full suite with coverage; with arguments it forwards them to `pytest`.
- Agents SHOULD use `just ci` when they want the repo's broad local pre-commit style check.
- Agents SHOULD use `just build` when packaging or documentation output is part of the task.
- Agents SHOULD treat code formatting as best effort while editing. Before committing code, run `just format` so the pre-commit hook does not create avoidable churn.
- Agents SHOULD NOT spend excessive effort trying to manually match formatting details that `just format` already enforces algorithmically.
- Agents SHOULD prefer focused checks first, then widen if the change or failures require it.

## Tests And Source

- When library behavior changes, agents SHOULD update the corresponding tests in `tests/` in the same change.
- Benchmark and profiling changes usually need both behavior tests and output-shape tests, not just a successful manual run.
- Agents SHOULD treat missing coverage as a prompt to inspect reachability, not as proof that code should be removed.

## Benchmark Maintenance

- The shared benchmark dataset lives in `src/ietfparse/test/benchmarks.toml`. Agents SHOULD keep benchmark changes driven by that dataset instead of ad hoc samples.
- When adding a new header or workload, agents MUST keep the dataset, the benchmark loader/validation layer, the runner/CLI surface, and the regression tests aligned in one change.
- The profiler entrypoint is `tools/profile_benchmark.py`. Agents SHOULD keep its output stable enough for tests and CI summaries, and update its focused tests when changing formats or cross-revision behavior.

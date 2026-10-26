#!/bin/bash

# chmod +x screate_folders.sh

touch main.py                  # Entry point: demonstrates evals catching regressions
touch test_adversarial.py      # 5 adversarial tests proving robustness
touch README.md                # Full documentation

mkdir -p Harness/
touch Harness/__init__.py          # Package init (exports MinimalAgent, SimulatedLM, ToolRegistry)
touch Harness/agent.py             # Minimal agent loop (re-implemented standalone)
touch Harness/simulated_lm.py      # Swappable brain: good / bad / broken / hang modes
touch Harness/tools.py             # Tool registry with add, subtract, memory ops
touch Harness/trace_logger.py      # Colored logging for the evaluation process

mkdir -p Evaluator/
touch Evaluator/__init__.py          # Package init (exports Evaluator, TestCase, scoring fns)
touch Evaluator/test_case.py         # TestCase dataclass + AgentResult dataclass
touch Evaluator/scoring.py           # Four scoring functions (exact, keyword, tool-call, latency)
touch Evaluator/evaluator.py         # Evaluator class: runs agent in thread, scores, reports

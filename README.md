# ToyEvaluator (Module #9)

Automated agent testing and scoring — measure what your agent does before you trust it.

**Prerequisite:** understand Module #8 (ToySandBox). You should be comfortable with the idea that tools can fail, hang, or produce unexpected output. This module builds the *measurement layer* on top of that reality.

---

## What Is This?

Think of an agent like a new employee you just hired. Before giving them access to production systems, you run them through a set of test scenarios and grade their performance. That is exactly what this module does: it feeds known tasks to an agent, checks whether the output matches expectations, verifies the right tools were called, and confirms the response came back within a time budget.

The core insight is simple: **you cannot trust an agent you have not tested.** When you swap the model, tweak a prompt, or add a new tool, something may silently break. Evals catch those regressions before they reach real users.

This module has no agent loop of its own. It *wraps* an agent (re-implemented internally for standalone use) and measures it from the outside — like a speed camera that doesn't drive the car, it just records how fast it went.

---

## Folder Structure

```text
toy_evaluator/
├── main.py                  # Entry point: demonstrates evals catching regressions
├── harness/
│   ├── __init__.py          # Package init (exports MinimalAgent, SimulatedLM, ToolRegistry)
│   ├── agent.py             # Minimal agent loop (re-implemented standalone)
│   ├── simulated_lm.py      # Swappable brain: good / bad / broken / hang modes
│   ├── tools.py             # Tool registry with add, subtract, memory ops
│   └── trace_logger.py      # Colored logging for the evaluation process
├── evaluator/
│   ├── __init__.py          # Package init (exports Evaluator, TestCase, scoring fns)
│   ├── test_case.py         # TestCase dataclass + AgentResult dataclass
│   ├── scoring.py           # Four scoring functions (exact, keyword, tool-call, latency)
│   └── evaluator.py         # Evaluator class: runs agent in thread, scores, reports
├── test_adversarial.py      # 5 adversarial tests proving robustness
└── README.md                # This file
```

---

## Dependencies

**External:** None. Pure Python standard library only.

**Stdlib modules used:** `json`, `os`, `sys`, `time`, `threading`, `re`, `dataclasses`

**Internal import graph:**

```text
main.py
├── harness/
│   ├── agent.py          (imports: time, json, dataclasses)
│   ├── simulated_lm.py   (imports: time, re)
│   ├── tools.py          (imports: json)
│   └── trace_logger.py   (no imports beyond builtins)
├── evaluator/
│   ├── test_case.py      (imports: dataclasses)
│   ├── scoring.py        (imports: re)
│   └── evaluator.py      (imports: threading, time, dataclasses, evaluator.scoring, evaluator.test_case)
└── test_adversarial.py   (imports: harness.*, evaluator.*)
```

No circular imports. The `evaluator/` package never imports from `harness/` — it only receives an agent object via constructor injection. This keeps the measurement layer independent of the thing being measured.

---

## Execution

```bash
# Navigate to the module folder
cd toy_evaluator

# Run the main demonstration (shows good/bad/hang agents being evaluated)
python main.py

# Run the adversarial test suite (proves robustness under failure conditions)
python test_adversarial.py
```

No installation step. No virtual environment needed. Just Python 3.8+.

---

## Expected Output

### Running `python main.py`

```text
============================================================
  TOY EVALUATOR — Automated Agent Testing & Scoring
  Scenario: Same harness, three different brains (good/bad/hang)
============================================================

[EVAL] Evaluating GOOD agent (correct behavior)...
  GOOD agent  -> avg score: 1.000  (passed: 4/4)

[EVAL] Evaluating BAD agent (regression simulation)...
  BAD agent   -> avg score: 0.375  (passed: 0/4)

[EVAL] Evaluating HANG agent (timeout scenario)... [will take ~5s]
  HANG agent  -> avg score: 0.000  (timed_out: 1/1)

------------------------------------------------------------
  REGRESSION DETECTION (good baseline vs bad candidate)
------------------------------------------------------------

  4 regression(s) detected:

    * Add 5 + 3: 1.000 -> 0.250 (delta -0.750)
    * Subtract 10 - 4: 1.000 -> 0.250 (delta -0.750)
    * Store a note: 1.000 -> 0.500 (delta -0.500)
    * Direct question (no tool): 1.000 -> 0.333 (delta -0.667)

============================================================
  KEY INSIGHT: Same harness, different brain -> different scores.
  In production: swap model/prompt -> re-run evals -> catch regressions before deploy.
============================================================
```

### Running `python test_adversarial.py`

```text
  PASS  Broken LM / Chaotic output
  PASS  Hostile / Invalid input
  PASS  Tool execution failure
  PASS  Infinite loop / Max iterations
  PASS  Empty string / Hang timeout

  5/5 tests passed.
```

---

## Architecture Diagram

```text
+------------------------------------------------------------------+
|                        main.py (orchestrator)                    |
|                                                                  |
|   Creates agents, defines test cases, runs evaluations,          |
|   displays regression report.                                    |
+----------+-----------------------------+-------------------------+
           |                             |
           | creates                     | creates
           v                             v
+---------------------+       +----------------------------+
|  harness/           |       |  evaluator/                |
|                     |       |                            |
|  +---------------+  |       |  +----------------------+  |
|  | MinimalAgent  |  |       |  |     Evaluator        |  |
|  |               |  |       |  |                      |  |
|  | - lm (brain)  |  |       |  | - agent (reference)  |  |
|  | - tools       |  |       |  | - test_cases[]       |  |
|  | - max_iter    |  |       |  | - timeout_seconds    |  |
|  +-------+-------+  |       |  +----------+-----------+  |
|          |          |       |           |                |
|          | calls    |       |           | runs in        |
|          v          |       |           | thread         |
|  +---------------+  |       |           |                |
|  | SimulatedLM   |  |       |  +--------v-----------+    |
|  | (swappable)   |  |       |  |  scoring.py        |    |
|  |               |  |       |  |                    |    |
|  | mode:         |  |       |  | - score_exact      |    |
|  |  good/bad/    |  |       |  | - score_keywords   |    |
|  |  broken/hang  |  |       |  | - score_tool_calls |    |
|  +---------------+  |       |  | - score_latency    |    |
|                     |       |  | - compute_weighted |    |
|  +---------------+  |       |  +--------------------+    |
|  | ToolRegistry  |  |       |                            |
|  |               |  |       |  +---------------------+   |
|  | add           |  |       |  |   test_case.py       |  |
|  | subtract      |  |       |  |                      |  |
|  | memory_store  |  |       |  | TestCase (dataclass) |  |
|  | memory_recall |  |       |  | AgentResult (datacls)|  |
|  +---------------+  |       |  +---------------------+   |
+---------------------+       +----------------------------+

KEY DESIGN DECISION:
The Evaluator holds a REFERENCE to the agent (constructor injection).
It never imports from harness/. To evaluate a different agent, you
simply pass a different object. This is the same "swap the brain"
principle from Module #0 applied one level up.
```

---

## State Machine Diagram

The Evaluator processes each test case through the following states:

```text
                    +--------+
                    |  IDLE  |
                    +---+----+
                        |
                        | run_all() called
                        v
                 +------+------+
                 |             |
                 v             v
          +----------+   (for each test case)
          |EXECUTING |<----------------+
          |          |                 |
          | agent    |                 |
          | runs in  |                 |
          | thread   |                 |
          +----+-----+                 |
               |                       |
        +------+------+------+         |
        |      |             |         |
        v      v             v         |
  +---------+ +--------+ +-------+     |
  |AWAITING | |TIMEOUT | | ERROR |     |
  |_RESULT  | |        | |       |     |
  +----+----+ +---+----+ +--+-+--+     |
       |            |         |        |
       v            v         v        |
  +---------+   +-----------+          |
  | SCORING |   |  (zero    |          |
  |         |   |   scores) |          |
  +----+----+   +-----+-----+          |
       |                |              |
       +-------+--------+              |
               |                       |
               v                       |
        +-------------+                |
        |  COMPLETE   |----------------+
        | (result     |
        |  stored)    |
        +------+------+
               |
               | all test cases done
               v
        +-------------+
        |   REPORTED  |
        | (summary +  |
        |  regressions|
        |  available) |
        +-------------+


STATE DESCRIPTIONS:

  IDLE         Evaluator constructed, no tests run yet.
  EXECUTING    Agent thread is alive and running the task.
  AWAITING_    Thread finished normally; reading the AgentResult
  RESULT       from the shared container.
  SCORING      Computing all four dimension scores + weighted total.
  TIMEOUT      Thread was still alive after join(timeout) returned.
               All scores forced to 0.0.
  ERROR        Exception was caught inside the agent thread.
               All scores forced to 0.0, error message stored.
  COMPLETE     One test case fully processed; result appended to list.
  REPORTED     All test cases done; summary and regression data ready.

TRANSITION GUARDS:

  EXECUTING -> AWAITING_RESULT : thread.is_alive() == False AND no exception
  EXECUTING -> TIMEOUT         : thread.is_alive() == True after join(timeout)
  EXECUTING -> ERROR           : exception caught in thread target function
  SCORING   -> COMPLETE        : all four score functions returned successfully
```

---

## File Reference

**main.py** — The demonstration script. Creates three agents (good, bad, hang) sharing the same harness, runs the evaluator against each, and displays a regression report comparing good vs bad. This is the file you run first to see the module in action. Think of it as a "before and after" photo: same body, different brain, different score.

**harness/agent.py** — A minimal re-implementation of the agent loop from Module #0. It exists because each TOYAGENTS module must be standalone (no cross-module imports). The `run()` method loops: ask the LM, check if it wants a tool, execute the tool, feed the result back, repeat until a final answer or the iteration cap is hit. Returns an `AgentResult` containing output, tool calls, iterations, and latency — exactly what the Evaluator needs to score.

**harness/simulated_lm.py** — The swappable brain. Four modes demonstrate four real-world failure scenarios: "good" (correct behavior), "bad" (plausible but wrong answers — simulates a prompt regression), "broken" (malformed output that breaks JSON parsing), and "hang" (sleeps forever — simulates a model timeout). Change the mode string and the entire agent behavior changes. This is the core teaching point: the harness stays the same, only the brain differs.

**harness/tools.py** — A simple tool registry with four tools (add, subtract, memory_store, memory_recall). The `execute()` method catches all exceptions from tools and returns error strings instead of raising. This ensures a failing tool never crashes the agent loop — it just produces an error message the LM can react to.

**harness/trace_logger.py** — Colored terminal logging using ANSI escape codes (no external packages). Each component gets its own color: evaluator is green, scoring is magenta, agent events are cyan, errors are red. The `report()` method prints the full trace at the end of execution for review.

**evaluator/test_case.py** — Two dataclasses: `TestCase` defines one evaluation scenario (input, expected output, required keywords, expected tool calls, latency budget, and per-dimension weights). `AgentResult` mirrors the harness version so the evaluator package is self-contained. Think of a TestCase as a single question on an exam with a rubric for grading.

**evaluator/scoring.py** — Four pure functions, each returning a float between 0.0 and 1.0. `score_exact_match` checks string equality. `score_keyword_presence` returns the fraction of required keywords found in the output. `score_tool_calls` checks if the right tools were called in the right order (position-based). `score_latency` is binary: within budget or not. A fifth function, `compute_weighted_score`, combines all four into a single number using configurable weights.

**evaluator/evaluator.py** — The main class. Its `_run_single()` method executes one test case by spawning a daemon thread, joining with a timeout, then computing scores. If the thread is still alive after the join, it's a timeout. If an exception was caught inside the thread, it's an error. Otherwise, it extracts the result and calls all four scoring functions. The `run_all()` method iterates through all test cases. The `compare()` method takes two result lists (baseline vs candidate) and returns a list of regressions where the candidate scored lower.

**test_adversarial.py** — Five tests proving the evaluator survives failure conditions: broken LM output, hostile inputs (empty, oversized, special characters), exploding tools, infinite loops (iteration cap), and the module-specific case of empty string output plus hang timeout. All five must pass for the module to be considered robust.

---

## What This Teaches

| Concept                         | Where to Look                                                | Key Insight                                                                                                                                                                                 |
| ------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Evaluation as a wrapper         | `evaluator/evaluator.py` constructor                         | The evaluator holds a *reference* to the agent. Swap the agent, keep the tests. Same principle as swapping the LM in Module #0.                                                             |
| Multi-dimensional scoring       | `evaluator/scoring.py`                                       | One number (overall score) hides which dimension failed. Always inspect per-dimension scores to diagnose *why* an agent regressed.                                                          |
| Timeout via threading           | `evaluator/evaluator.py` `_run_single()`                     | You cannot "pause" a thread in Python. The pattern is: start thread, join with timeout, check if still alive. This is how every production eval framework handles hanging models.           |
| Regression detection            | `evaluator/evaluator.py` `compare()` method                  | Store scores from your last known-good run. After any change (new model, new prompt, new tool), re-run and diff. Any score that dropped is a regression to investigate.                     |
| Weighted scoring                | `TestCase` weight fields                                     | Not all dimensions matter equally. A latency violation might be less critical than a wrong answer. Weights let you encode your priorities.                                                  |
| Neutral scores (N/A dimensions) | `scoring.py` — the `if expected is None: return 1.0` pattern | If a test case does not define an expected output, exact-match scoring should not drag the overall score down. Returning 1.0 means "this dimension doesn't apply here."                     |
| The agent is just data          | `AgentResult` dataclass                                      | Once the agent finishes, it's just a bundle of strings and numbers. The evaluator treats it as a black box — it does not care *how* the agent produced the output, only *what* it produced. |

---

## Intuitive Analogy

Imagine you run a restaurant. Every dish that leaves the kitchen goes through a quality check before reaching the customer:

- **Exact match** = Does the plate look exactly like the photo on the menu?
- **Keyword presence** = Are all the ingredients the customer ordered actually in the dish?
- **Tool-call correctness** = Did the chef use the right stations (grill, fryer, salad bar) in the right order?
- **Latency budget** = Did the dish arrive within 20 minutes?

If any check fails, the dish goes back to the kitchen. That is what the Evaluator does for agents. It does not cook the food (that is the agent's job). It inspects the result and assigns a grade.

In production, this is exactly how teams like Anthropic, OpenAI, and Google evaluate their models before deployment. They have suites of hundreds or thousands of test cases, each with expected outputs, required phrases, and latency budgets. A model that scores below threshold does not ship.

---

## Link to Parent Curriculum

This module is part of the **TOYAGENTS** curriculum — a series of standalone, zero-dependency Python projects that teach agentic AI concepts without requiring a real LLM.

Repository: https://github.com/AlexOcculate/TOYAGENTS


Build order: 
```text
#0 ToyAgentNoBrain 

  → #1 ToyA2A 
  
  → #2 ToyMCP 
  
  → #3 ToyBrain 
  
  → #4 ToyPlanner

  → #5 ToyEmbeddings 

  → #6 ToyVectorDB 

  → #7 ToyRAG 
  
  → #8 ToySandBox 

   → **#9 ToyEvaluator** 

   → #10 ToyCapstone
```
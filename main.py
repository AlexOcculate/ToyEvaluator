# Line 1:  Import sys and os for path setup so we can run from any directory.
import sys, os

# Line 2:  Add the script's directory to the import path (enables "from Harness import ...").
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Line 4: Import Harness components (the agent being evaluated).
from Harness import MinimalAgent, SimulatedLM, ToolRegistry

# Line 5: Import build_default_registry to create the standard tool set.
from Harness.tools import build_default_registry

# Line 6: Import Evaluator components (the measurement layer).
from Evaluator import Evaluator, TestCase

# Line 7: Import scoring functions for direct use in report display.
from Evaluator.scoring import (
    score_exact_match,
    score_keyword_presence,
    score_tool_calls,
    score_latency,
)

# Line 8: Import the trace logger for colored output.
from Harness.trace_logger import TraceLogger

# Line 10: Create a shared trace logger instance for this demo run.
logger = TraceLogger()

# ──────────────────────────────────────────────
#  STEP 1: Define test cases (the "spec" of correct behavior)
# ──────────────────────────────────────────────

# Line 15: Build the list of test cases that define what "correct" looks like.
TEST_CASES = [
    # Line 17: Test case 1: Simple addition — expects tool call + correct answer.
    TestCase(
        name="Add 5 + 3",
        input="Please add 5 and 3",
        expected_output="The answer is 8.",
        required_keywords=["answer", "8"],
        expected_tool_calls=["add"],
        max_latency_ms=2000.0,
        weight_exact=1.0,
        weight_keywords=1.0,
        weight_tools=1.0,
        weight_latency=0.5,
    ),
    # Line 29: Test case 2: Subtraction — expects subtract tool + correct result.
    TestCase(
        name="Subtract 10 - 4",
        input="Please subtract 10 minus 4",
        expected_output="The answer is 6.",
        required_keywords=["answer", "6"],
        expected_tool_calls=["subtract"],
        max_latency_ms=2000.0,
        weight_exact=1.0,
        weight_keywords=1.0,
        weight_tools=1.0,
        weight_latency=0.5,
    ),
    # Line 41: Test case 3: Memory store — expects memory_store tool call.
    TestCase(
        name="Store a note",
        input="Please remember that the meeting is at noon",
        required_keywords=["stored"],
        expected_tool_calls=["memory_store"],
        max_latency_ms=2000.0,
        weight_exact=0.0,
        weight_keywords=1.0,
        weight_tools=1.0,
        weight_latency=0.5,
    ),
    # Line 52: Test case 4: No tool needed — direct answer with keyword check.
    TestCase(
        name="Direct question (no tool)",
        input="What is the capital of France?",
        required_keywords=["answer"],
        expected_tool_calls=[],
        max_latency_ms=1000.0,
        weight_exact=0.0,
        weight_keywords=1.0,
        weight_tools=0.0,
        weight_latency=1.0,
    ),
]

# ──────────────────────────────────────────────
#  STEP 2: Create agents with different "brains" to demonstrate regression detection
# ──────────────────────────────────────────────

# Line 66: Build the standard tool registry (shared by all agents).
tools = build_default_registry()

# Line 68: Create the GOOD agent (correct behavior — should score ~1.0 on all tests).
good_lm = SimulatedLM(mode="good")
# Line 70: Wrap it in a MinimalAgent with standard settings.
good_agent = MinimalAgent(lm=good_lm, tools=tools, max_iterations=5)

# Line 72: Create the BAD agent (wrong behavior — simulates a regression after prompt change).
bad_lm = SimulatedLM(mode="bad")
# Line 74: Wrap in an agent with same Harness (only the brain differs).
bad_agent = MinimalAgent(lm=bad_lm, tools=tools, max_iterations=5)

# Line 76: Create the HANG agent (simulates a model that never responds — timeout scenario).
hang_lm = SimulatedLM(mode="hang")
# Line 78: Wrap in an agent (will be killed by the Evaluator's timeout).
hang_agent = MinimalAgent(lm=hang_lm, tools=tools, max_iterations=5)

# ──────────────────────────────────────────────
#  STEP 3: Run evaluations and display results
# ──────────────────────────────────────────────

# Line 82: Print a header for the demo.
print("\n" + "═" * 60)
# Line 84: Title for this demonstration.
print("  TOY Evaluator — Automated Agent Testing & Scoring")
# Line 86: Subtitle explaining the scenario.
print("  Scenario: Same Harness, three different brains (good/bad/hang)")
# Line 88: Closing header line.
print("═" * 60 + "\n")

# Line 90: ─── Evaluate the GOOD agent ───
# Line 92: Log that we're starting evaluation of the good agent.
logger.evaluator("Evaluating GOOD agent (correct behavior)...")
# Line 94: Create an Evaluator instance wrapping the good agent with our test cases.
eval_good = Evaluator(agent=good_agent, test_cases=TEST_CASES, timeout_seconds=5.0)
# Line 96: Run all test cases against the good agent.
results_good = eval_good.run_all()
# Line 98: Get the summary statistics.
summary_good = eval_good.get_summary()
# Line 100: Print a formatted result line for the good agent.
print(
    f"  GOOD agent  → avg score: {summary_good['average_score']:.3f}  "
    f"(passed: {summary_good['passed']}/{summary_good['total_tests']})\n"
)

# Line 103: ─── Evaluate the BAD agent ───
# Line 105: Log that we're starting evaluation of the bad agent.
logger.evaluator("Evaluating BAD agent (regression simulation)...")
# Line 107: Create an Evaluator for the bad agent.
eval_bad = Evaluator(agent=bad_agent, test_cases=TEST_CASES, timeout_seconds=5.0)
# Line 109: Run all tests against the bad agent.
results_bad = eval_bad.run_all()
# Line 111: Get summary for the bad agent.
summary_bad = eval_bad.get_summary()
# Line 113: Print result line showing the score dropped (regression detected).
print(
    f"  BAD agent   → avg score: {summary_bad['average_score']:.3f}  "
    f"(passed: {summary_bad['passed']}/{summary_bad['total_tests']})\n"
)

# Line 116: ─── Evaluate the HANG agent ───
# Line 118: Log that we're starting evaluation of the hang agent.
logger.evaluator("Evaluating HANG agent (timeout scenario)... [will take ~5s]")
# Line 120: Create Evaluator with a SHORT timeout to demonstrate quick detection.
eval_hang = Evaluator(agent=hang_agent, test_cases=TEST_CASES[:1], timeout_seconds=3.0)
# Line 122: Run only the first test case (to save time — one timeout is enough to prove the point).
results_hang = eval_hang.run_all()
# Line 124: Get summary for the hang agent.
summary_hang = eval_hang.get_summary()
# Line 126: Print result line showing all zeros due to timeout.
print(
    f"  HANG agent  → avg score: {summary_hang['average_score']:.3f}  "
    f"(timed_out: {summary_hang['timed_out']}/{summary_hang['total_tests']})\n"
)

# ──────────────────────────────────────────────
#  STEP 4: Regression detection (compare good vs bad)
# ──────────────────────────────────────────────

# Line 132: Print a section header for regression analysis.
print("─" * 60)
# Line 134: Title for the regression comparison.
print("  REGRESSION DETECTION (good baseline vs bad candidate)")
# Line 136: Closing line.
print("─" * 60)

# Line 138: Use the compare() method to find regressions between good and bad results.
regressions = eval_good.compare(results_good, results_bad)
# Line 140: If regressions were found, display them.
if regressions:
    # Line 142: Print how many regressions were detected.
    print(f"\n  {len(regressions)} regression(s) detected:\n")
    # Line 144: Iterate through each regression and display details.
    for reg in regressions:
        # Line 146: Format the regression entry with test name, scores, and delta.
        print(
            f"    • {reg['test_name']}: "
            f"{reg['baseline_score']:.3f} → {reg['candidate_score']:.3f} "
            f"(Δ {reg['delta']:+.3f})"
        )
else:
    # Line 150: No regressions found (unexpected in this demo, but handle gracefully).
    print("\n  No regressions detected.")

# Line 153: Print a final separator and conclusion.
print("\n" + "═" * 60)
# Line 155: Key takeaway message.
print("  KEY INSIGHT: Same Harness, different brain → different scores.")
# Line 157: Explain the real-world application.
print(
    "  In production: swap model/prompt → re-run evals → catch regressions before deploy."
)
# Line 159: Closing line.
print("═" * 60 + "\n")

# Line 161: Print the full colored trace report at the end.
logger.report()

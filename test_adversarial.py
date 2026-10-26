# Line 1:  Import sys and os for path setup (standard convention across all modules).
import sys, os

# Line 2:  Add the script's directory to the import path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Line 4:  Import the module's main components for testing.
from Harness import MinimalAgent, SimulatedLM, ToolRegistry
from Harness.tools import build_default_registry
from Evaluator import Evaluator, TestCase
from Evaluator.scoring import (
    score_exact_match,
    score_keyword_presence,
    score_tool_calls,
    score_latency,
    compute_weighted_score,
)


# ──────────────────────────────────────────────
#  TEST 1: Broken / Chaotic LM
#  Proves: the Evaluator doesn't crash on malformed agent output
# ──────────────────────────────────────────────
def test_broken_lm():
    # Line 13: Create a broken-mode LM that returns garbage JSON.
    lm = SimulatedLM(mode="broken")
    # Line 15: Build standard tools (will fail to parse args, but should not crash).
    tools = build_default_registry()
    # Line 17: Wrap in an agent with low iteration cap to speed up the test.
    agent = MinimalAgent(lm=lm, tools=tools, max_iterations=3)
    # Line 19: Define a simple test case that the broken agent will fail.
    tc = TestCase(
        name="broken_lm_test",
        input="Please add 5 and 3",
        expected_output="The answer is 8.",
        required_keywords=["answer"],
        expected_tool_calls=["add"],
        max_latency_ms=5000.0,
    )
    # Line 27: Create an Evaluator with a generous timeout (broken LM won't hang, just produce garbage).
    ev = Evaluator(agent=agent, test_cases=[tc], timeout_seconds=10.0)
    # Line 29: Run the evaluation — must not raise any exception.
    results = ev.run_all()
    # Line 31: Assert we got exactly one result back.
    assert len(results) == 1, "Expected 1 result"
    # Line 33: The broken agent should have a low score (not perfect).
    assert results[0].overall_score < 1.0, "Broken LM should not score perfectly"
    # Line 35: Verify the system handled the error gracefully (either error field or low score).
    assert results[0].error is not None or results[0].overall_score < 1.0


# ──────────────────────────────────────────────
#  TEST 2: Invalid / Hostile Input
#  Proves: guardrails block bad input before it reaches the core
# ──────────────────────────────────────────────
def test_hostile_input():
    # Line 43: Create a good agent (the hostile input should be handled, not crash the system).
    lm = SimulatedLM(mode="good")
    # Line 45: Standard tools.
    tools = build_default_registry()
    # Line 47: Agent with standard settings.
    agent = MinimalAgent(lm=lm, tools=tools, max_iterations=5)

    # Line 49: Test case with an empty string input.
    tc_empty = TestCase(
        name="empty_input",
        input="",
        required_keywords=["answer"],
        max_latency_ms=5000.0,
    )
    # Line 56: Test case with a very long input (10,000 characters).
    tc_long = TestCase(
        name="oversized_input",
        input="A" * 10000,
        required_keywords=["answer"],
        max_latency_ms=5000.0,
    )
    # Line 63: Test case with special characters that could break string formatting.
    tc_special = TestCase(
        name="special_chars",
        input='"; DROP TABLE agents; -- { } [ ] \\ / | < > &',
        required_keywords=["answer"],
        max_latency_ms=5000.0,
    )

    # Line 71: Run all three hostile inputs through the Evaluator.
    ev = Evaluator(
        agent=agent, test_cases=[tc_empty, tc_long, tc_special], timeout_seconds=10.0
    )
    # Line 73: Execute — must not raise.
    results = ev.run_all()
    # Line 75: Assert we got all three results back.
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    # Line 77: None of the results should have an unhandled exception (error should be None or handled).
    for r in results:
        # Line 79: If there's an error, it should be a string (not a crash).
        assert r.error is None or isinstance(r.error, str)


# ──────────────────────────────────────────────
#  TEST 3: Tool Execution Failure
#  Proves: a failing tool doesn't crash the loop; error is handled
# ──────────────────────────────────────────────
def test_tool_failure():
    # Line 89: Create a custom tool that always raises an exception.
    def exploding_tool(args):
        # Line 91: Always raise — simulates a tool with a bug or missing dependency.
        raise RuntimeError("Tool exploded unexpectedly")

    # Line 94: Build a registry with the exploding tool registered.
    tools = ToolRegistry()
    # Line 96: Register the bad tool under a name the LM will try to call.
    tools.register("add", exploding_tool)
    # Line 98: Also register a working subtract so we can test mixed scenarios.
    tools.register(
        "subtract", lambda args: str(int(args.get("a", 0)) - int(args.get("b", 0)))
    )

    # Line 100: Create a good-mode LM (it will try to call "add" which will explode).
    lm = SimulatedLM(mode="good")
    # Line 102: Agent with the broken tool registry.
    agent = MinimalAgent(lm=lm, tools=tools, max_iterations=5)

    # Line 104: Test case expecting add to work (it won't — that's the point).
    tc = TestCase(
        name="tool_explodes",
        input="Please add 5 and 3",
        expected_output="The answer is 8.",
        required_keywords=["answer"],
        expected_tool_calls=["add"],
        max_latency_ms=5000.0,
    )

    # Line 113: Run the Evaluator — the tool failure must be caught, not propagated.
    ev = Evaluator(agent=agent, test_cases=[tc], timeout_seconds=10.0)
    # Line 115: Execute without crashing.
    results = ev.run_all()
    # Line 117: We should still get a result (not a crash).
    assert len(results) == 1
    # Line 119: The score should be low because the tool failed (agent can't produce correct answer).
    assert results[0].overall_score < 1.0, "Failing tool should reduce score"


# ──────────────────────────────────────────────
#  TEST 4: Infinite Loop / Max Iterations
#  Proves: the iteration guardrail stops runaway loops
# ──────────────────────────────────────────────
def test_infinite_loop():
    # Line 129: Create a custom LM that ALWAYS returns a tool call (never gives a final answer).
    class LoopingLM:
        # Line 131: Constructor stores nothing special.
        def __init__(self):
            pass

        # Line 133: generate() always returns a tool call — the agent will loop forever without the cap.
        def generate(self, context):
            # Line 135: Always invoke "add" with fixed args — never produces a final answer.
            return 'TOOL: add, {"a": 1, "b": 2}'

    # Line 138: Standard tools (add will succeed, so the loop continues indefinitely without the cap).
    tools = build_default_registry()
    # Line 140: Agent with a LOW max_iterations to prove the guardrail works quickly.
    agent = MinimalAgent(lm=LoopingLM(), tools=tools, max_iterations=5)

    # Line 142: Test case that will never be "satisfied" by the looping agent.
    tc = TestCase(
        name="infinite_loop_test",
        input="Please add 1 and 2",
        expected_output="The answer is 3.",
        required_keywords=["answer"],
        max_latency_ms=5000.0,
    )

    # Line 150: Run the Evaluator — the agent should hit its iteration cap and stop.
    ev = Evaluator(agent=agent, test_cases=[tc], timeout_seconds=10.0)
    # Line 152: Execute.
    results = ev.run_all()
    # Line 154: Assert we got a result (didn't hang forever).
    assert len(results) == 1
    # Line 156: The agent should NOT have completed (it hit the cap without producing an answer).
    assert results[0].agent_result is not None
    # Line 158: Verify the completed flag is False (hit max_iterations without final answer).
    assert (
        results[0].agent_result.completed == False
    ), "Looping agent should not complete"
    # Line 160: The iteration count should equal the max (5).
    assert (
        results[0].agent_result.iterations == 5
    ), f"Expected 5 iterations, got {results[0].agent_result.iterations}"


# ──────────────────────────────────────────────
#  TEST 5: [Module-specific] Agent returns empty string / agent hangs (timeout)
#  Proves: the Evaluator handles both empty output and timeout gracefully
# ──────────────────────────────────────────────
def test_module_specific():
    # Line 170: ─── Part A: Agent returns empty string ───
    # Line 172: Create an LM that returns an empty string (simulates a model that "thinks" but says nothing).
    class EmptyLM:
        # Line 174: Constructor.
        def __init__(self):
            pass

        # Line 176: generate() returns empty string — agent will treat this as a "final answer."
        def generate(self, context):
            # Line 178: Return nothing (empty string is not a tool call, so it's treated as the answer).
            return ""

    # Line 181: Standard tools.
    tools = build_default_registry()
    # Line 183: Agent with the empty-string LM.
    agent_empty = MinimalAgent(lm=EmptyLM(), tools=tools, max_iterations=5)

    # Line 185: Test case expecting a real answer (will fail because output is empty).
    tc_empty = TestCase(
        name="empty_output",
        input="Please add 5 and 3",
        expected_output="The answer is 8.",
        required_keywords=["answer", "8"],
        max_latency_ms=5000.0,
    )

    # Line 193: Run Evaluator against the empty-output agent.
    ev_empty = Evaluator(agent=agent_empty, test_cases=[tc_empty], timeout_seconds=5.0)
    # Line 195: Execute.
    results_empty = ev_empty.run_all()
    # Line 197: Assert we got a result (no crash).
    assert len(results_empty) == 1
    # Line 199: The output should be empty string.
    assert results_empty[0].agent_result.output == ""
    # Line 201: Exact match score should be 0 (empty != "The answer is 8.").
    assert results_empty[0].score_exact == 0.0
    # Line 203: Keyword score should be 0 (no keywords in empty string).
    assert results_empty[0].score_keywords == 0.0

    # Line 205: ─── Part B: Agent hangs (timeout) ───
    # Line 207: Create a hang-mode LM (sleeps for 30 seconds).
    lm_hang = SimulatedLM(mode="hang")
    # Line 209: Agent with the hanging LM.
    agent_hang = MinimalAgent(lm=lm_hang, tools=tools, max_iterations=5)

    # Line 211: Test case for the hang scenario.
    tc_hang = TestCase(
        name="hang_timeout",
        input="Please add 5 and 3",
        expected_output="The answer is 8.",
        max_latency_ms=2000.0,
    )

    # Line 218: Run Evaluator with a SHORT timeout (2 seconds) to trigger the timeout path quickly.
    ev_hang = Evaluator(agent=agent_hang, test_cases=[tc_hang], timeout_seconds=2.0)
    # Line 220: Execute — this will take ~2 seconds as the thread times out.
    results_hang = ev_hang.run_all()
    # Line 222: Assert we got a result (the Evaluator caught the timeout, didn't hang forever).
    assert len(results_hang) == 1
    # Line 224: The timed_out flag should be True.
    assert results_hang[0].timed_out == True, "Hang agent should trigger timeout"
    # Line 226: All scores should be zero for a timed-out agent.
    assert results_hang[0].overall_score == 0.0
    # Line 228: Agent result should be None (we never got a response).
    assert results_hang[0].agent_result is None


# ──────────────────────────────────────────────
#  RUNNER
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # Line 237: Define the list of all adversarial tests with display names.
    tests = [
        ("Broken LM / Chaotic output", test_broken_lm),
        ("Hostile / Invalid input", test_hostile_input),
        ("Tool execution failure", test_tool_failure),
        ("Infinite loop / Max iterations", test_infinite_loop),
        ("Empty string / Hang timeout", test_module_specific),
    ]
    # Line 244: Counter for passed tests.
    passed = 0
    # Line 246: Iterate through all tests and execute them.
    for name, fn in tests:
        # Line 248: Try to run the test function.
        try:
            # Line 250: Call the test — it will raise AssertionError on failure.
            fn()
            # Line 252: If no exception, print PASS.
            print(f"  PASS  {name}")
            # Line 254: Increment the passed counter.
            passed += 1
        except Exception as e:
            # Line 256: If any exception (AssertionError or other), print FAIL with the message.
            print(f"  FAIL  {name}: {e}")
    # Line 258: Print a summary line with the pass count.
    print(f"\n  {passed}/{len(tests)} tests passed.")
    # Line 260: If any test failed, exit with non-zero code (CI-friendly).
    if passed < len(tests):
        # Line 262: Signal failure to the shell / CI system.
        sys.exit(1)

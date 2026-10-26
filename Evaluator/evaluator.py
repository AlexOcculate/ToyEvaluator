# Line 1:  Import threading to run the agent in a separate thread (enables timeout detection).
import threading

# Line 2:  Import time for measuring evaluation wall-clock time.
import time

# Line 3:  Import dataclasses for the TestResult container.
from dataclasses import dataclass, field

# Line 5: Import scoring functions from the sibling module.
from Evaluator.scoring import (
    score_exact_match,
    score_keyword_presence,
    score_tool_calls,
    score_latency,
    compute_weighted_score,
)

# Line 7: Import TestCase for type hints.
from Evaluator.test_case import TestCase, AgentResult


# Line 9: TestResult holds the full scoring breakdown for one test case execution.
@dataclass
class TestResult:
    # Line 11: The test case that was executed (for reference in reports).
    test_case: TestCase
    # Line 13: The raw AgentResult returned by the agent (or None if timeout occurred).
    agent_result: AgentResult = None
    # Line 15: Score for exact-match dimension (0.0 to 1.0).
    score_exact: float = 0.0
    # Line 17: Score for keyword-presence dimension.
    score_keywords: float = 0.0
    # Line 19: Score for tool-call correctness dimension.
    score_tools: float = 0.0
    # Line 21: Score for latency budget dimension.
    score_latency: float = 0.0
    # Line 23: Final weighted overall score combining all dimensions.
    overall_score: float = 0.0
    # Line 25: True if the agent timed out (thread didn't finish in time).
    timed_out: bool = False
    # Line 27: Any exception message if the agent crashed during execution.
    error: str = None


# Line 29: Evaluator is the main class — it wraps an agent and runs a suite of test cases against it.
class Evaluator:
    # Line 31: Constructor takes the agent to evaluate, a list of test cases, and a per-case timeout.
    def __init__(self, agent, test_cases: list, timeout_seconds: float = 5.0):
        # Line 33: Store the agent instance (the thing being measured).
        self.agent = agent
        # Line 35: Store the list of TestCase objects defining what to check.
        self.test_cases = test_cases
        # Line 37: Maximum seconds to wait for a single agent run before declaring timeout.
        self.timeout_seconds = timeout_seconds
        # Line 39: Results will be collected here as tests execute.
        self.results: list = []

    # Line 41: _run_single() executes one test case in a thread with timeout protection.
    def _run_single(self, tc: TestCase) -> TestResult:
        # Line 43: Create the result object pre-populated with the test case reference.
        result = TestResult(test_case=tc)
        # Line 45: Container to hold the AgentResult from the thread (threads can't return values directly).
        container = {}
        # Line 47: Flag to detect if an exception occurred inside the agent thread.
        error_holder = {}

        # Line 49: Define the target function that runs inside the worker thread.
        def _target():
            # Line 51: Reset the LM's internal state so multi-turn logic starts fresh for each test case.
            if hasattr(self.agent.lm, "reset"):
                self.agent.lm.reset()
            # Line 54: Execute the agent with the test case input.
            try:
                # Line 56: Call the agent's run method with the task string.
                ar = self.agent.run(tc.input)
                # Line 58: Store the result in the shared container for the main thread to read.
                container["result"] = ar
            except Exception as e:
                # Line 61: If the agent raised, store the error message for reporting.
                error_holder["error"] = str(e)

        # Line 64: Create a daemon thread so it won't block program exit on timeout.
        t = threading.Thread(target=_target, daemon=True)
        # Line 66: Start the agent execution in the background.
        t.start()
        # Line 68: Wait for the thread to finish, but no longer than the configured timeout.
        t.join(timeout=self.timeout_seconds)

        # Line 70: Check if the thread is still alive after join — means it timed out.
        if t.is_alive():
            # Line 72: Mark this result as a timeout failure.
            result.timed_out = True
            # Line 74: All scores are zero for a timed-out agent (it never produced output).
            result.score_exact = 0.0
            # Line 76: No keywords could be checked.
            result.score_keywords = 0.0
            # Line 78: No tool calls were recorded.
            result.score_tools = 0.0
            # Line 80: Latency score is zero (exceeded budget by definition).
            result.score_latency = 0.0
            # Line 82: Overall score is zero.
            result.overall_score = 0.0
            # Line 84: Return the timeout result immediately.
            return result

        # Line 86: Check if an error occurred during agent execution.
        if "error" in error_holder:
            # Line 88: Store the error message in the result.
            result.error = error_holder["error"]
            # Line 90: All scores zero for a crashed agent.
            result.score_exact = 0.0
            # Line 92: No keywords to check.
            result.score_keywords = 0.0
            # Line 94: No tool calls recorded.
            result.score_tools = 0.0
            # Line 96: Latency is zero (didn't complete).
            result.score_latency = 0.0
            # Line 98: Overall score is zero.
            result.overall_score = 0.0
            # Line 100: Return the error result.
            return result

        # Line 102: Agent completed successfully — extract its result.
        ar = container.get("result")
        # Line 104: Store the raw agent result for reference.
        result.agent_result = ar

        # Line 106: ─── Compute each dimension score ───
        # Line 108: Score exact match (or neutral if no expected output defined).
        result.score_exact = score_exact_match(tc.expected_output, ar.output)
        # Line 110: Score keyword presence in the output.
        result.score_keywords = score_keyword_presence(tc.required_keywords, ar.output)
        # Line 112: Score tool-call correctness (names and order).
        result.score_tools = score_tool_calls(tc.expected_tool_calls, ar.tool_calls)
        # Line 114: Score latency against the budget.
        result.score_latency = score_latency(tc.max_latency_ms, ar.latency_ms)

        # Line 116: ─── Compute the weighted overall score ───
        # Line 118: Combine all four dimensions using the test case's configured weights.
        result.overall_score = compute_weighted_score(
            result.score_exact,
            result.score_keywords,
            result.score_tools,
            result.score_latency,
            tc.weight_exact,
            tc.weight_keywords,
            tc.weight_tools,
            tc.weight_latency,
        )

        # Line 126: Return the fully scored result.
        return result

    # Line 128: run_all() executes the entire test suite and returns a list of TestResults.
    def run_all(self) -> list:
        # Line 130: Clear any previous results (allows re-running the Evaluator).
        self.results = []
        # Line 132: Record the start time for the full suite.
        suite_start = time.time()
        # Line 134: Iterate through each test case in order.
        for tc in self.test_cases:
            # Line 136: Execute this single test case (with timeout protection).
            result = self._run_single(tc)
            # Line 138: Append to the results list.
            self.results.append(result)
        # Line 140: Calculate total suite duration (useful for reporting).
        self.suite_duration_ms = (time.time() - suite_start) * 1000.0
        # Line 142: Return all results for further processing or display.
        return self.results

    # Line 144: get_summary() computes aggregate statistics across all test results.
    def get_summary(self) -> dict:
        # Line 146: Start with a summary dictionary.
        summary = {
            "total_tests": len(self.results),
            "passed": 0,
            "failed": 0,
            "timed_out": 0,
            "errors": 0,
            "average_score": 0.0,
            "min_score": 1.0,
            "max_score": 0.0,
        }
        # Line 156: If no results yet, return the zeroed summary.
        if not self.results:
            # Line 158: Nothing to summarize.
            return summary
        # Line 160: Accumulator for summing all overall scores.
        score_sum = 0.0
        # Line 162: Iterate through results to compute aggregates.
        for r in self.results:
            # Line 164: Add this result's overall score to the running sum.
            score_sum += r.overall_score
            # Line 166: Track minimum score seen.
            summary["min_score"] = min(summary["min_score"], r.overall_score)
            # Line 168: Track maximum score seen.
            summary["max_score"] = max(summary["max_score"], r.overall_score)
            # Line 170: Categorize the result for pass/fail/timeout/error counts.
            if r.timed_out:
                # Line 172: Count timeouts separately.
                summary["timed_out"] += 1
                # Line 174: Timeouts count as failures.
                summary["failed"] += 1
            elif r.error:
                # Line 176: Count errors separately.
                summary["errors"] += 1
                # Line 178: Errors count as failures.
                summary["failed"] += 1
            elif r.overall_score >= 0.999:
                # Line 180: Score of ~1.0 means all dimensions passed — mark as pass.
                summary["passed"] += 1
            else:
                # Line 183: Any score below perfect is a partial or full failure.
                summary["failed"] += 1
        # Line 185: Compute the average overall score across all test cases.
        summary["average_score"] = score_sum / len(self.results)
        # Line 187: Return the completed summary.
        return summary

    # Line 189: compare() compares two sets of results (e.g., before/after a model swap) for regression detection.
    def compare(self, baseline_results: list, candidate_results: list) -> list:
        # Line 191: List to hold per-test-case regression entries.
        regressions = []
        # Line 193: Iterate by index (assumes same test cases in same order).
        for i in range(min(len(baseline_results), len(candidate_results))):
            # Line 195: Get the baseline and candidate overall scores.
            base_score = baseline_results[i].overall_score
            # Line 197: Get the candidate score.
            cand_score = candidate_results[i].overall_score
            # Line 199: If the candidate scored lower than baseline, it's a regression.
            if cand_score < base_score - 0.01:
                # Line 201: Record this as a regression with details.
                regressions.append(
                    {
                        "test_name": baseline_results[i].test_case.name,
                        "baseline_score": base_score,
                        "candidate_score": cand_score,
                        "delta": cand_score - base_score,
                    }
                )
        # Line 209: Return the list of detected regressions (empty = no regressions).
        return regressions

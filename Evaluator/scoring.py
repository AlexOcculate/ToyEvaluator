# Line 1:  Import re for case-insensitive keyword matching in outputs.
import re


# Line 3: score_exact_match() returns 1.0 if output matches expected exactly, else 0.0.
def score_exact_match(expected: str, actual: str) -> float:
    # Line 5: If no expected output was specified, this dimension is N/A — return 1.0 (neutral).
    if expected is None:
        # Line 7: Neutral score means "this dimension doesn't apply."
        return 1.0
    # Line 9: Compare stripped strings for exact equality (whitespace-tolerant).
    if actual.strip() == expected.strip():
        # Line 11: Perfect match — full credit.
        return 1.0
    # Line 13: No match — zero credit for this dimension.
    return 0.0


# Line 15: score_keyword_presence() returns a ratio of required keywords found in the output.
def score_keyword_presence(required_keywords: list, actual: str) -> float:
    # Line 17: If no keywords are required, this dimension is N/A — return 1.0 (neutral).
    if not required_keywords:
        # Line 19: Neutral — nothing to check.
        return 1.0
    # Line 21: Convert actual output to lowercase for case-insensitive matching.
    actual_lower = actual.lower()
    # Line 23: Count how many required keywords are present in the output.
    found = 0
    # Line 25: Iterate through each required keyword.
    for kw in required_keywords:
        # Line 27: Check if the keyword (lowercased) appears anywhere in the output.
        if kw.lower() in actual_lower:
            # Line 29: Keyword found — increment the counter.
            found += 1
    # Line 31: Return the ratio of keywords found to keywords required (0.0 to 1.0).
    return found / len(required_keywords)


# Line 33: score_tool_calls() checks if the agent called the expected tools in the expected order.
def score_tool_calls(expected_tools: list, actual_tool_calls: list) -> float:
    # Line 35: If no tool calls are expected, this dimension is N/A — return 1.0 (neutral).
    if not expected_tools:
        # Line 37: Neutral — no tool expectations to verify.
        return 1.0
    # Line 39: Extract just the tool names from the actual (name, args) tuples.
    actual_names = [name for name, _args in actual_tool_calls]
    # Line 41: If the number of calls differs entirely, we can still do partial credit.
    # Line 42: Use a position-based comparison: for each expected tool, check if it appears at that position.
    correct = 0
    # Line 44: Iterate up to the length of the shorter list (expected vs actual).
    for i in range(min(len(expected_tools), len(actual_names))):
        # Line 46: Check if the tool at position i matches what was expected at position i.
        if actual_names[i] == expected_tools[i]:
            # Line 48: Correct tool at correct position — full credit for this slot.
            correct += 1
    # Line 50: Return ratio of correctly-ordered calls to total expected calls.
    return correct / len(expected_tools)


# Line 52: score_latency() returns 1.0 if within budget, 0.0 if exceeded (binary pass/fail).
def score_latency(max_ms: float, actual_ms: float) -> float:
    # Line 54: If no latency budget was specified, this dimension is N/A — return 1.0 (neutral).
    if max_ms is None:
        # Line 56: Neutral — no time constraint to enforce.
        return 1.0
    # Line 58: Check if actual latency is within the allowed budget.
    if actual_ms <= max_ms:
        # Line 60: Within budget — full credit.
        return 1.0
    # Line 62: Exceeded budget — zero credit (could be graduated, but binary is clearer for evals).
    return 0.0


# Line 64: compute_weighted_score() combines all four dimension scores into a single 0-1 float.
def compute_weighted_score(
    s_exact: float,
    s_keywords: float,
    s_tools: float,
    s_latency: float,
    w_exact: float,
    w_keywords: float,
    w_tools: float,
    w_latency: float,
) -> float:
    # Line 66: Calculate the sum of all weights (denominator for weighted average).
    total_weight = w_exact + w_keywords + w_tools + w_latency
    # Line 68: Guard against division by zero if all weights are zero.
    if total_weight == 0:
        # Line 70: No dimensions weighted — return neutral 1.0.
        return 1.0
    # Line 72: Compute the weighted average of all four dimension scores.
    weighted_sum = (
        s_exact * w_exact
        + s_keywords * w_keywords
        + s_tools * w_tools
        + s_latency * w_latency
    )
    # Line 74: Return the normalized score between 0.0 and 1.0.
    return weighted_sum / total_weight

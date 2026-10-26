# Line 1:  Import dataclass and field for structured test case definitions.
from dataclasses import dataclass, field


# Line 3: AgentResult is re-defined here (standalone module rule) — mirrors harness/agent.py's version.
# Line 4: The Evaluator needs this to type-hint what the agent returns without importing from harness.
@dataclass
class AgentResult:
    # Line 6: Final text output from the agent.
    output: str = ""
    # Line 8: Ordered list of (tool_name, args_dict) tuples for tool-call scoring.
    tool_calls: list = field(default_factory=list)
    # Line 10: Number of loop iterations consumed.
    iterations: int = 0
    # Line 12: Wall-clock time in milliseconds.
    latency_ms: float = 0.0
    # Line 14: Whether the agent produced a final answer (vs. hitting iteration cap).
    completed: bool = False


# Line 16: TestCase defines one evaluation scenario with expected outcomes and scoring weights.
@dataclass
class TestCase:
    # Line 18: Human-readable name for this test case (appears in reports).
    name: str
    # Line 20: The task string fed to the agent's run() method.
    input: str
    # Line 22: Exact string the output should match (None = skip exact-match scoring).
    expected_output: str = None
    # Line 24: List of keywords that MUST appear in the output (empty list = skip keyword scoring).
    required_keywords: list = field(default_factory=list)
    # Line 26: List of tool names the agent is expected to call, in order (empty = skip tool scoring).
    expected_tool_calls: list = field(default_factory=list)
    # Line 28: Maximum allowed latency in milliseconds (None = skip latency scoring).
    max_latency_ms: float = None
    # Line 30: Weight for exact-match dimension in the weighted overall score (default 1.0).
    weight_exact: float = 1.0
    # Line 32: Weight for keyword-presence dimension.
    weight_keywords: float = 1.0
    # Line 34: Weight for tool-call correctness dimension.
    weight_tools: float = 1.0
    # Line 36: Weight for latency budget dimension.
    weight_latency: float = 1.0

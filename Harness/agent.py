# Line 1:  Import time for latency measurement of agent runs.
import time

# Line 2:  Import json to parse tool-call arguments from the LM response.
import json

# Line 3:  Import dataclass decorator for the AgentResult container.
from dataclasses import dataclass, field


# Line 5:  AgentResult holds everything the Evaluator needs to score a single run.
@dataclass
class AgentResult:
    # Line 7:  The final text output produced by the agent (empty string if it never answered).
    output: str = ""
    # Line 9:  List of (tool_name, args_dict) tuples recording every tool invocation in order.
    tool_calls: list = field(default_factory=list)
    # Line 11: Number of loop iterations the agent consumed before stopping or hitting the cap.
    iterations: int = 0
    # Line 13: Wall-clock latency in milliseconds from start to finish of the run.
    latency_ms: float = 0.0
    # Line 15: True if the agent produced a final answer; False if it hit max_iterations without one.
    completed: bool = False


# Line 17: MinimalAgent is a re-implementation of the #0 Harness loop, kept standalone per curriculum rules.
class MinimalAgent:
    # Line 19: Constructor accepts a swappable LM (the "brain"), a tool registry, and an iteration cap.
    def __init__(self, lm, tools, max_iterations=10):
        # Line 21: Store the LM reference — this is the ONLY thing you swap to change behavior.
        self.lm = lm
        # Line 23: Store the tool registry so the agent can execute discovered tools.
        self.tools = tools
        # Line 25: Guardrail — maximum number of think-act cycles before forced stop.
        self.max_iterations = max_iterations

    # Line 27: run() executes the full agent loop for a single task and returns an AgentResult.
    def run(self, task: str) -> AgentResult:
        # Line 29: Record start time for latency calculation.
        start = time.time()
        # Line 31: Accumulator for all tool calls made during this run.
        tool_calls = []
        # Line 33: The context passed to the LM each iteration (grows with tool results).
        context = task
        # Line 35: Placeholder for the final answer text.
        output = ""
        # Line 37: Track whether we got a definitive answer or just ran out of iterations.
        completed = False
        # Line 39: Loop counter — will be set to actual iterations used.
        iterations = 0

        # Line 41: Main agent loop — think (LM) → act (tool) → observe (result) until answer or cap.
        for i in range(self.max_iterations):
            # Line 43: Increment iteration counter on each pass through the loop.
            iterations = i + 1
            # Line 45: Ask the LM to produce either a tool call or a final answer.
            response = self.lm.generate(context)
            # Line 47: Check if the LM decided to invoke a tool (convention: starts with "TOOL:").
            if response.startswith("TOOL:"):
                # Line 49: Extract the portion after "TOOL:" which contains name and JSON args.
                payload = response[len("TOOL:") :]
                # Line 51: Split on the first comma to separate tool name from arguments JSON.
                parts = payload.split(",", 1)
                # Line 53: Strip whitespace from the tool name (e.g., " add" → "add").
                tool_name = parts[0].strip()
                # Line 55: Parse the JSON arguments; default to empty dict on parse failure.
                try:
                    args = json.loads(parts[1].strip()) if len(parts) > 1 else {}
                except (json.JSONDecodeError, IndexError):
                    args = {}
                # Line 59: Record this tool call for later scoring by the Evaluator.
                tool_calls.append((tool_name, args))
                # Line 61: Execute the tool and capture its string result.
                result = self.tools.execute(tool_name, args)
                # Line 63: Build new context that includes the original task and the tool result.
                context = f"{task}\n[Tool '{tool_name}' returned: {result}]"
            else:
                # Line 66: The LM produced a final answer (not a tool call) — we're done.
                output = response.strip()
                # Line 68: Mark the run as completed successfully.
                completed = True
                # Line 70: Break out of the loop since we have our answer.
                break

        # Line 72: Calculate elapsed wall-clock time in milliseconds.
        latency_ms = (time.time() - start) * 1000.0
        # Line 74: Package everything into an AgentResult for the Evaluator to consume.
        return AgentResult(
            output=output,
            tool_calls=tool_calls,
            iterations=iterations,
            latency_ms=latency_ms,
            completed=completed,
        )

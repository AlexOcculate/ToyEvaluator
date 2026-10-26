# Line 1:  Import time to simulate artificial delay in "hang" mode.
import time

# Line 2:  Import re for extracting numbers from task strings.
import re


# Line 4: SimulatedLM is the swappable "brain." Change its mode and the agent's behavior changes entirely.
class SimulatedLM:
    # Line 6: Constructor takes a mode string that determines response behavior.
    def __init__(self, mode="good"):
        # Line 8: Store the mode — one of "good", "bad", "broken", or "hang".
        self.mode = mode
        # Line 10: Internal counter to track how many times generate() has been called (for multi-turn logic).
        self._call_count = 0

    # Line 12: Reset the internal call counter — useful when reusing the same LM instance across test cases.
    def reset(self):
        # Line 14: Zero out the call count so multi-turn logic starts fresh.
        self._call_count = 0

    # Line 16: generate() is the single entry point the agent calls each loop iteration.
    def generate(self, context: str) -> str:
        # Line 18: Increment the internal counter to know if this is a first or follow-up call.
        self._call_count += 1
        # Line 20: Dispatch to the mode-specific handler.
        return self._respond(context)

    # Line 22: _respond() contains the keyword-based "intelligence" for each mode.
    def _respond(self, context: str) -> str:
        # Line 24: ─── HANG MODE: simulate an agent that never returns (timeout scenario). ───
        if self.mode == "hang":
            # Line 26: Sleep long enough to exceed any reasonable latency budget.
            time.sleep(30)
            # Line 28: This line is unreachable in practice but satisfies the return type.
            return 'TOOL: add, {"a": 1, "b": 2}'

        # Line 30: ─── BROKEN MODE: return garbage that breaks JSON parsing and logic. ───
        if self.mode == "broken":
            # Line 32: Return malformed content that will cause tool execution to fail.
            return "TOOL: add, {{{not valid json at all"

        # Line 34: ─── BAD MODE: produces plausible but incorrect answers (regression scenario). ───
        if self.mode == "bad":
            # Line 36: If context has a tool result already, give a wrong final answer.
            if "[Tool" in context:
                # Line 38: Return an answer that misses required keywords and has wrong numbers.
                return "I think the result might be something around there."
            # Line 40: First call — still invoke the tool but with wrong arguments.
            nums = re.findall(r"\d+", context)
            if len(nums) >= 2:
                # Line 42: Swap the operands to produce a wrong calculation.
                return f'TOOL: subtract, {{"a": {nums[0]}, "b": {nums[1]}}}'
            # Line 44: Fallback for non-math tasks in bad mode.
            return "I am not sure about that."

        # Line 46: ─── GOOD MODE (default): correct behavior with proper tool calls and answers. ───
        # Line 48: If context already contains a tool result, produce the final answer.
        if "[Tool" in context:
            # Line 50: Extract the tool name and result from the context string.
            tool_match = re.search(r"\[Tool '(\w+)' returned: (.+?)\]", context)
            # Line 52: If we found a tool result, format a proper answer with the required keyword "answer".
            if tool_match:
                tool_name = tool_match.group(1)
                result_val = tool_match.group(2)
                # Line 55: Return a well-formed answer containing the word "answer" (for keyword scoring).
                return f"The answer is {result_val}."
            # Line 57: Fallback if context format is unexpected.
            return "The answer is unknown."

        # Line 59: First call — determine which tool to invoke based on keywords in the task.
        nums = re.findall(r"\d+", context)
        # Line 61: If the task mentions "add" and has at least two numbers, call the add tool.
        if "add" in context.lower() and len(nums) >= 2:
            return f'TOOL: add, {{"a": {nums[0]}, "b": {nums[1]}}}'
        # Line 63: If the task mentions "subtract" or "minus", call the subtract tool.
        if ("subtract" in context.lower() or "minus" in context.lower()) and len(
            nums
        ) >= 2:
            return f'TOOL: subtract, {{"a": {nums[0]}, "b": {nums[1]}}}'
        # Line 65: If the task mentions "remember" or "store", call memory_store.
        if "remember" in context.lower() or "store" in context.lower():
            text = re.sub(
                r"^(please\s+)?(remember|store)\s+", "", context, flags=re.IGNORECASE
            )
            return f'TOOL: memory_store, {{"key": "note", "value": "{text.strip()}"}}'
        # Line 67: If the task mentions "recall" or "what did I", call memory_recall.
        if "recall" in context.lower() or "what did i" in context.lower():
            return 'TOOL: memory_recall, {"key": "note"}'
        # Line 69: Default fallback — answer directly without any tool.
        return f"The answer is: I processed your request about '{context[:30]}'."

# Line 1:  Import json for serializing tool results into strings the LM can read.
import json


# Line 3: ToolRegistry holds named tool functions and executes them by name.
class ToolRegistry:
    # Line 5: Constructor initializes an empty dictionary of tools.
    def __init__(self):
        # Line 7: Map of tool_name → callable that accepts a dict of arguments.
        self._tools = {}

    # Line 9: register() adds a new tool to the registry under a given name.
    def register(self, name: str, func):
        # Line 11: Store the callable keyed by its name for later lookup.
        self._tools[name] = func

    # Line 13: execute() looks up a tool by name, calls it with args, and returns a string result.
    def execute(self, name: str, args: dict) -> str:
        # Line 15: Check if the tool exists — return an error string if not (never raise to agent).
        if name not in self._tools:
            # Line 17: Return a descriptive error so the LM can adapt its strategy.
            return f"ERROR: Unknown tool '{name}'"
        # Line 19: Try to execute the tool, catching any exception it might raise.
        try:
            # Line 21: Call the tool function with the provided arguments dictionary.
            result = self._tools[name](args)
            # Line 23: Convert the result to a string for inclusion in the LM context.
            return str(result)
        except Exception as e:
            # Line 25: If the tool raised, return the error as a string (agent loop continues).
            return f"ERROR: Tool '{name}' failed: {e}"

    # Line 27: list_tools() returns the names of all registered tools (useful for debugging).
    def list_tools(self) -> list:
        # Line 29: Return a sorted list of tool names.
        return sorted(self._tools.keys())


# ──────────────────────────────────────────────
#  Default tool implementations (re-implemented standalone)
# ──────────────────────────────────────────────

# Line 35: Shared in-memory store used by memory tools (simulates persistent state).
_MEMORY_STORE = {}


# Line 37: add_tool sums two numbers from the args dict and returns the result.
def _add(args: dict) -> str:
    # Line 39: Extract a and b, defaulting to 0 if missing (graceful degradation).
    a = args.get("a", 0)
    # Line 41: Extract b with same default.
    b = args.get("b", 0)
    # Line 43: Return the sum as a string.
    return str(int(a) + int(b))


# Line 45: subtract_tool computes a minus b.
def _subtract(args: dict) -> str:
    # Line 47: Extract a with default 0.
    a = args.get("a", 0)
    # Line 49: Extract b with default 0.
    b = args.get("b", 0)
    # Line 51: Return the difference as a string.
    return str(int(a) - int(b))


# Line 53: memory_store_tool saves a key-value pair in the shared store.
def _memory_store(args: dict) -> str:
    # Line 55: Extract the key (default "default") and value (default "").
    key = args.get("key", "default")
    # Line 57: Extract the value to store.
    value = args.get("value", "")
    # Line 59: Store in the shared dictionary.
    _MEMORY_STORE[key] = value
    # Line 61: Confirm the storage operation succeeded.
    return f"Stored '{key}' successfully."


# Line 63: memory_recall_tool retrieves a previously stored value by key.
def _memory_recall(args: dict) -> str:
    # Line 65: Extract the key to look up.
    key = args.get("key", "default")
    # Line 67: Look up in the shared store; return error message if not found.
    if key in _MEMORY_STORE:
        # Line 69: Return the stored value.
        return _MEMORY_STORE[key]
    # Line 71: Key was never stored — return a clear message.
    return f"Nothing stored under '{key}'."


# Line 73: build_default_registry() creates and returns a ToolRegistry pre-loaded with standard tools.
def build_default_registry() -> ToolRegistry:
    # Line 75: Create a fresh registry instance.
    reg = ToolRegistry()
    # Line 77: Register the add tool under its name.
    reg.register("add", _add)
    # Line 79: Register the subtract tool.
    reg.register("subtract", _subtract)
    # Line 81: Register memory_store for state persistence within a session.
    reg.register("memory_store", _memory_store)
    # Line 83: Register memory_recall for retrieving stored state.
    reg.register("memory_recall", _memory_recall)
    # Line 85: Return the fully populated registry.
    return reg

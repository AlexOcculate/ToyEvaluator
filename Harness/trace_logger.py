# Line 1:  ANSI escape codes for terminal coloring (no external packages needed).
RESET = "\033[0m"
# Line 3: Bold prefix for section headers.
BOLD = "\033[1m"
# Line 5: Color for the evaluator component (green — it's the orchestrator of this module).
C_EVALUATOR = "\033[92m"
# Line 7: Color for scoring operations (magenta — the measurement layer).
C_SCORING = "\033[95m"
# Line 9: Color for the wrapped agent (cyan — it's the thing being measured).
C_AGENT = "\033[96m"
# Line 11: Color for errors and failures (red).
C_ERROR = "\033[91m"
# Line 13: Color for warnings and timeouts (yellow).
C_WARN = "\033[93m"
# Line 15: Light green background for PASS indicators.
BG_PASS = "\033[102m\033[30m"
# Line 17: Light red background for FAIL indicators.
BG_FAIL = "\033[101m\033[97m"
# Line 19: Light yellow background for WARN/TIMEOUT indicators.
BG_WARN = "\033[103m\033[30m"


# Line 21: TraceLogger collects colored log entries and can print a full report at the end.
class TraceLogger:
    # Line 23: Constructor initializes an empty list of log entries.
    def __init__(self):
        # Line 25: List of (color, message) tuples in chronological order.
        self.entries = []

    # Line 27: log() appends a colored entry to the internal buffer.
    def log(self, color: str, message: str):
        # Line 29: Store the color and message pair for later reporting.
        self.entries.append((color, message))
        # Line 31: Also print immediately for live terminal feedback.
        print(f"{color}{message}{RESET}")

    # Line 33: Convenience methods for each component color.
    def evaluator(self, msg: str):
        # Line 35: Log with evaluator (green) color.
        self.log(C_EVALUATOR, f"[EVAL] {msg}")

    # Line 37: Log a scoring event with magenta color.
    def scoring(self, msg: str):
        # Line 39: Prefix with SCORING tag for visual distinction.
        self.log(C_SCORING, f"[SCORE] {msg}")

    # Line 41: Log an agent-related event with cyan color.
    def agent(self, msg: str):
        # Line 43: Prefix with AGENT tag to show it's the wrapped component speaking.
        self.log(C_AGENT, f"[AGENT] {msg}")

    # Line 45: Log an error or failure condition in red.
    def error(self, msg: str):
        # Line 47: Prefix with ERROR tag for immediate visual alert.
        self.log(C_ERROR, f"[ERROR] {msg}")

    # Line 49: Log a warning (e.g., timeout) in yellow.
    def warn(self, msg: str):
        # Line 51: Prefix with WARN tag.
        self.log(C_WARN, f"[WARN] {msg}")

    # Line 53: log_pass() prints a PASS badge with green background.
    def log_pass(self, msg: str):
        # Line 55: Format with background color for high visibility.
        print(f"{BG_PASS}  PASS  {RESET} {msg}")
        # Line 57: Also store in buffer for the report.
        self.entries.append((BG_PASS, f"  PASS  {msg}"))

    # Line 59: log_fail() prints a FAIL badge with red background.
    def log_fail(self, msg: str):
        # Line 61: Format with red background for high visibility.
        print(f"{BG_FAIL}  FAIL  {RESET} {msg}")
        # Line 63: Store in buffer.
        self.entries.append((BG_FAIL, f"  FAIL  {msg}"))

    # Line 65: log_warn() prints a WARN badge with yellow background.
    def log_warn(self, msg: str):
        # Line 67: Format with yellow background.
        print(f"{BG_WARN}  WARN  {RESET} {msg}")
        # Line 69: Store in buffer.
        self.entries.append((BG_WARN, f"  WARN  {msg}"))

    # Line 71: report() prints the complete trace log with a header and summary line.
    def report(self):
        # Line 73: Print a separator and title for the full trace.
        print(f"\n{BOLD}{C_EVALUATOR}{'═' * 60}{RESET}")
        # Line 75: Print the report header.
        print(f"{BOLD}{C_EVALUATOR}  FULL TRACE REPORT{RESET}")
        # Line 77: Print another separator.
        print(f"{BOLD}{C_EVALUATOR}{'═' * 60}{RESET}")
        # Line 79: Iterate through all stored entries and re-print them.
        for color, msg in self.entries:
            # Line 81: Print each entry with its original color.
            print(f"{color}{msg}{RESET}")
        # Line 83: Final separator to close the report block.
        print(f"{BOLD}{C_EVALUATOR}{'═' * 60}{RESET}\n")

#!/usr/bin/env python3
"""
Runs the BASIC Computer Games through an interpreter and reports how far
each one gets. It is the acceptance test for BASIC III: the number of
games that run to the end should go up as features are added.

Usage:
    python3 run_games.py                      # BASIC II, as a baseline
    python3 run_games.py "python3 main.py"    # your interpreter
    python3 run_games.py "python3 main.py" hello.bas bagels.bas

The interpreter command gets the path of a .bas file as its last argument.
Games are interactive, so each one is fed the same list of answers, and
is stopped after a few seconds.
"""
import os
import random
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
GAMES = os.path.join(HERE, "..", "03", "bas")
# --debug makes BASIC II stop at an error instead of going on to the next line
DEFAULT = f"python3 {os.path.join(HERE, '..', '03', 'main.py')} --debug"
TIMEOUT = 5

# A mix of the answers games ask for: yes/no, numbers, pairs, words
random.seed(1)
ANSWERS = ["YES", "Y", "NO", "N", "5", "3", "1", "2", "10", "50", "100",
           "0", "7", "A", "HEADS", "4,5", "1,1", "2,3", "20"]
INPUT = "\n".join(random.choice(ANSWERS) for _ in range(400)) + "\n"


def classify(output, returncode, timed_out):
    """Sorts a run into one of a few outcomes, with a short detail."""
    if timed_out:
        # Still running: waiting for input it did not like, or looping
        return "running", ""
    if "Traceback" in output:
        last = [l for l in output.splitlines() if re.match(r"^\w+(Error|Exception)", l)]
        detail = last[-1] if last else "Python error"
        if detail.startswith("EOFError"):
            return "out of input", ""
        return "crashed", detail
    match = re.search(r"Unknown command '([^']*)'", output)
    if match:
        return "unsupported", match.group(1).upper()
    match = re.search(r"^(Error|Syntax error).*$", output, re.M)
    if match:
        return "error", match.group(0)
    if "Program completed" in output:
        return "finished", ""
    return "other", output.strip().splitlines()[-1] if output.strip() else ""


def run(command, game):
    try:
        result = subprocess.run(
            command.split() + [os.path.join(GAMES, game)],
            input=INPUT, capture_output=True, text=True, timeout=TIMEOUT)
        return classify(result.stdout + result.stderr, result.returncode, False)
    except subprocess.TimeoutExpired:
        return classify("", None, True)


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    games = sys.argv[2:] or sorted(f for f in os.listdir(GAMES) if f.endswith(".bas"))

    # Each game runs in its own process, so they can run side by side
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        results = dict(zip(games, pool.map(lambda g: run(command, g), games)))
    for game in games:
        outcome, detail = results[game]
        print(f"{game:24} {outcome:13} {detail[:70]}")

    print()
    for outcome, count in Counter(o for o, _ in results.values()).most_common():
        print(f"{count:4}  {outcome}")
    missing = Counter(d for o, d in results.values() if o == "unsupported")
    if missing:
        print("\nUnsupported commands, by number of games stopped:")
        for name, count in missing.most_common():
            print(f"{count:4}  {name}")


if __name__ == "__main__":
    main()

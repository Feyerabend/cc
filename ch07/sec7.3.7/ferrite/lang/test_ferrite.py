import os
import subprocess
import glob
import shutil

TESTS_DIR = "tests"

def compile_fe(fe_file):
    """Run ferrite.py on the .fe file (no -o flag, it outputs .c automatically)."""
    try:
        subprocess.check_call(["python3", "ferrite.py", fe_file], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        c_file = fe_file.replace(".fe", ".c")
        if not os.path.exists(c_file):
            return None
        return c_file
    except subprocess.CalledProcessError:
        return None

def compile_c(c_file):
    exe = c_file.replace(".c", "")
    try:
        subprocess.check_call(["gcc", "-o", exe, c_file], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return exe
    except subprocess.CalledProcessError:
        return None

def run_exe(exe):
    try:
        result = subprocess.run([f"./{exe}"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return f"RUNTIME ERROR (code {result.returncode})\n{result.stderr}"
        return result.stdout
    except Exception as e:
        return f"EXECUTION FAILED: {e}"

def test_file(fe_file):
    base_name = os.path.basename(fe_file)
    print(f"Testing {base_name} ... ", end="")

    c_file = compile_fe(fe_file)
    if c_file is None:
        print("FAIL (compilation error)")
        return

    exe = compile_c(c_file)
    if exe is None:
        print("FAIL (gcc error)")
        # cleanup
        os.remove(c_file)
        return

    output = run_exe(exe)

    expected_file = fe_file.replace(".fe", ".expected")
    if not os.path.exists(expected_file):
        print("NO .expected FILE")
        print("Output was:")
        print(output)
    elif output.rstrip("\n") == open(expected_file).read().rstrip("\n"):
        print("PASS")
    else:
        print("FAIL (wrong output)")
        print("=== Got ===")
        print(output)
        print("=== Expected ===")
        print(open(expected_file).read())

    # Cleanup
    os.remove(c_file)
    if os.path.exists(exe):
        os.remove(exe)

if __name__ == "__main__":
    if not os.path.exists(TESTS_DIR):
        print(f"Create a '{TESTS_DIR}' directory with .fe and .expected files.")
        exit(1)

    test_files = sorted(glob.glob(os.path.join(TESTS_DIR, "*.fe")))
    if not test_files:
        print("No test files found in tests/ directory.")
        exit(1)

    for fe in test_files:
        test_file(fe)

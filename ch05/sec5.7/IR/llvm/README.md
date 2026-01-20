
## Installing Clang/LLVM

Clang is part of LLVM. Installation varies by OS:

- *Linux* (e.g., Ubuntu/Debian):
  Run `sudo apt update && sudo apt install clang llvm`.
  For Fedora: `sudo dnf install clang llvm`.
- *macOS*: Install via Homebrew: `brew install llvm`.
  Use `/usr/local/opt/llvm/bin/clang` if needed
  (Apple's built-in clang works for basic use but may lack full LLVM tools like llc).
- *Windows*: Download LLVM installer from https://releases.llvm.org/
  (e.g., pre-built binaries). Add to PATH (e.g., C:\Program Files\LLVM\bin). Use clang.exe.

Verify: Run `clang --version` (should show LLVM/Clang version).


### Compiling and Testing LLVM IR (.ll Files)

Assuming you have extracted LLVM IR from llvm.py samples into .ll files
(e.g., copy the printed "LLVM IR Code" section for each sample_simple(),
sample_complex(), etc., into files like test1.ll, test2.ll).

General steps:
1. Save IR to a file, e.g., `test1.ll`.
2. Compile to executable: `clang test1.ll -o test1` (works on all platforms; no extra flags needed for simple i32 main).
   - If errors (e.g., undefined printf), add `-lc` for libc linkage: `clang test1.ll -o test1 -lc`.
   - Alternative (if clang fails on .ll): Use `llc test1.ll -o test1.s` (to assembly), then `clang test1.s -o test1`.
3. Run: `./test1` (Linux/macOS) or `test1.exe` (Windows).
4. Output: Depends on the IR. Most samples from llvm.py compute but don't print
   (exit code 0, no visible output). To test with print, modify IR like your
   test1print.ll (add printf declaration and call).


#### Sample-Specific Testing

Run llvm.py to print IR for each sample, save to .ll, then follow steps above.

- *Sample 1 (Simple: x = 10 + 5)*: Your test1.ll. Compiles/runs silently (computes
  but no output). To print: Edit like test1print.ll—add printf after the add/store, e.g., insert:
  ```
  %fmt_ptr = getelementptr inbounds [12 x i8], [12 x i8]* @.fmt, i64 0, i64 0
  %x_load = load i32, i32* %x_ptr
  call i32 (i8*, ...) @printf(i8* %fmt_ptr, i32 %x_load)
  ```
  (Declare `@.fmt` and `printf` at top.) Run: Outputs "Result: 15".

- *Sample 2 (Complex: z = (x + y) - (5 * (7 + 9)) / 2)*: IR allocates x/y/z,
  computes (x=2025, y=1477, z=3502 - 40). Runs silently.
  Add printf for %z_load to verify "Result: 3462".

- *Sample 3 (Multiple: d = (a * b) / 10)*: IR allocates a/b/c/d, computes
  (a=100, b=200, c=20000, d=2000). Runs silently.
  Add printf for %d_load to verify "Result: 2000".

Troubleshoot: If "undefined reference to main", ensure `define i32 @main()`.
For cross-platform, use WSL on Windows if issues. Test on simple IR first!



## Configuration Architecture

This project demonstrates a basic configuration architecture for a Hershey font renderer, 
using YAML files for persistent settings (e.g., `hershey_config.yaml` for rendering parameters
and `font_hints.yaml` for font-specific adjustments). The configs are loaded via custom 
loaders (`HersheyConfig` and `FontHintsLoader`), which merge user-provided values with
hardcoded defaults using a deep-merge approach. A custom YAML parser (`SimpleYAMLParser`)
handles parsing to avoid external dependencies. The configs are then injected into components
like the renderer and kerning manager.

From a configuration architecture standpoint, this is a solid starting point for a lightweight
 dependency-free system. It follows good principles like:
- *Separation of Concerns*: Configs are split by domain (general rendering vs.
  font hints), making it modular.
- *Defaults and Overrides*: Hardcoded defaults ensure the system works without files,
  and user files override them selectively.
- *Persistence*: Ability to save defaults via CLI flags (`--save-config`, `--save-hints`).
- *Integration*: Configs are passed down to dependent classes (e.g., `ScreenRenderer`
  uses them for scales, spacing, etc.), promoting reusability.

However, there are several potential problems and limitations, especially in robustness,
flexibility, and maintainability.


#### 1. *Custom YAML Parser Limitations*
   - *Simplicity Over Completeness*: The parser (`SimpleYAMLParser`) is very basic—it
     only supports nested dicts and simple scalars (strings, ints, floats, booleans, null).
     It doesn't handle lists/arrays, which limits extensibility (e.g., you couldn't
     easily add a list of "excluded_chars" without rewriting the parser).
   - *Indentation Rigidity*: Assumes exactly 2-space indents; tabs or 4-space indents will fail.
     This is error-prone for users editing configs manually.
   - *Value Parsing Issues*: Lowers case for booleans (e.g., "True" becomes True), but
     doesn't handle mixed case well. No support for complex types like dates or multi-line strings.
     Quoted strings are stripped, but escaping isn't handled robustly.
   - *Error Handling*: Raises generic `ValueError` on issues, but doesn't provide line-specific
     context beyond the line number. No recovery from partial parses.
   - *Dumping Limitations*: The `dump` method adds quotes only if spaces are present, which
     might not preserve original intent. No support for comments in output.
   - *Why Custom?*: Avoiding dependencies is fine for minimalism, but in practice, this
     reinvents the wheel. A standard library like PyYAML would handle more edge cases,
     YAML 1.2 features, and be more reliable.


#### 2. *Lack of Validation and Type Safety*
   - No schema validation: If a user sets `scale: "invalid"` (string instead of float),
     it loads without error but crashes later (e.g., in rendering math). Similarly,
     unknown keys are silently accepted but ignored.
   - No bounds checking in loaders: While `spacing_bounds` exist in the config,
     they're not enforced during loading (e.g., a user could set `char_spacing: 10.0`,
     exceeding `max_char_spacing`).
   - Type coercion is minimal: Relies on the parser's basic `_parse_value`, which
     could lead to runtime type errors.


#### 3. *Merge and Override Behaviour*
   - The `_deep_merge` is recursive and works for nested dicts, but it's overwrite-only—no
     support for appending (e.g., if you wanted to extend a list of colors).
   - CLI overrides (e.g., `--scale`) bypass YAML entirely, which is good for flexibility
     but creates multiple sources of truth. No precedence rules documented (e.g., CLI > YAML > Defaults).
   - Font hints are style-specific (e.g., "roman", "gothic"), which is good, but defaults
     to "default" without warning if an invalid style is provided.


#### 4. *File Handling and Security*
   - Paths are absolute/relative without sanitization: Could lead to issues if paths
     are malformed or point to system files.
   - No environment variable support: Configs are file-only; can't override via env
     vars (e.g., `HERSHEY_SCALE=3.0` for deployment flexibility).
   - Loading assumes files exist and are readable; errors are printed but not
     propagated gracefully (e.g., continues with defaults).
   - No watching/reloading: Changes to YAML require app restart.


#### 5. *Usability and Extensibility*
   - Hardcoded sections/keys: Adding new config options requires code changes
     in loaders and consumers.
   - No documentation in code: Comments explain basics, but no inline docs on
     expected types or examples.
   - Singleton font loader: `HersheyJSONFont` uses `__new__` for singleton,
     which ties config to a single instance—hard to switch fonts/configs dynamically.
   - Performance: For large configs (unlikely here), repeated deep-merges could
     be inefficient, but not an issue in this scope.

Overall, this architecture works well for a simple tool but would struggle in
larger projects. It's vulnerable to user errors, lacks flexibility for advanced use,
and could benefit from standardisation.


### Student Project Ideas

To turn this into educational projects, we can frame them as exercises to build a
"good configuration program." These build on the existing code, teaching concepts
like validation, modularity, testing, and best practices. I'll suggest three progressive
projects, suitable for individuals or small teams (e.g., CS students learning Python).
Each includes objectives, steps, deliverables, and learning outcomes. Students
should start with the provided code as a base.

#### Project 1: Basic Improvements to the Existing Config System (Beginner Level)
   *Objective*: Fix immediate problems in the config architecture while keeping it
   lightweight. Focus on robustness without adding dependencies.

   *Steps*:
   1. Enhance the `SimpleYAMLParser`:
      - Add support for lists (e.g., parse `- item1` under keys).
      - Improve error handling: Provide better messages (e.g.,
        "Invalid value for key 'scale' at line 5: expected float").
      - Handle tabs and variable indent sizes (e.g., detect indent from first line).
   2. Add basic validation in `HersheyConfig` and `FontHintsLoader`:
      - Define expected schemas (e.g., using dicts: `expected = {"rendering": {"scale": float, ...}}`).
      - In `load_config`, validate types and bounds after parsing
        (e.g., if `scale < 0.1 or scale > 10.0`, raise/warn).
      - Log invalid/unknown keys.
   3. Improve merging: Add support for list appending in `_deep_merge`.
   4. Update `main.py` to handle CLI overrides with validation (e.g., check if `--scale` is a float).
   5. Write unit tests (using `unittest`) for parsing valid/invalid YAML and merging.

   *Deliverables*:
   - Updated code files (`yaml_parser.py`, `config_loader.py`, etc.).
   - A new test suite (e.g., `tests/test_config.py`).
   - Example: Run with invalid config and show improved error messages.
   - README section on config validation.

   *Learning Outcomes*:
   - Parsing and validation techniques.
   - Error handling and logging.
   - Basic testing.
   - Time Estimate: 4-8 hours.

#### Project 2: Modernize with Standard Libraries and Validation (Intermediate Level)
   *Objective*: Replace custom parts with battle-tested libraries to make the
   config system more professional. Introduce schema validation and multi-source configs.

   *Steps*:
   1. Replace `SimpleYAMLParser` with PyYAML (add as dependency via `requirements.txt`).
      - Update loaders to use `yaml.safe_load` for security.
   2. Add schema validation using Pydantic (another dependency):
      - Define models, e.g.:
        ```python
        from pydantic import BaseModel, Field

        class RenderingConfig(BaseModel):
            scale: float = Field(2.5, ge=0.1, le=10.0)
            # ... other fields
        class HersheyConfigModel(BaseModel):
            rendering: RenderingConfig
            # ... other sections
        ```
      - In `load_config`, parse YAML then validate with `HersheyConfigModel(*user_config)`.
   3. Support environment variables: Use `os.environ` to override
      (e.g., `HERSHEY_SCALE` maps to `rendering.scale`).
      - Precedence: CLI > Env > YAML > Defaults.
   4. Make configs reloadable: Add a method to reload on file change (use `watchdog` lib for bonus file watching).
   5. Extend for lists: Add a config section like `excluded_fonts: [roman, gothic]` and use it in rendering.
   6. Add integration tests: E.g., render with env overrides and verify output image properties.

   *Deliverables*:
   - Updated loaders and main.py.
   - Pydantic models in a new file (e.g., `config_models.py`).
   - Docs on precedence and new features.
   - Demo script showing env/CLI overrides.

   *Learning Outcomes*:
   - Using external libs (PyYAML, Pydantic).
   - Schema-driven validation.
   - Multi-source config (files, env, CLI).
   - Dependency management.
   - Time Estimate: 8-12 hours.

#### Project 3: Build a Standalone Config CLI Tool (Advanced Level, Team Project)
   *Objective*: Extract the config system into a reusable "Config Manager" tool.
   Turn it into a mini-app for managing configs across projects, with this renderer as a case study.

   *Steps*:
   1. Extract to a module: Create `config_manager.py` with a class that handles
      loading, validation, merging, saving, and CLI commands (use `click` lib for CLI).
   2. Add features:
      - Generate templates: `config-manager generate --type=hershey` outputs default YAML.
      - Validate files: `config-manager validate path/to/config.yaml`.
      - Merge/diff: Compare two configs and output differences.
      - Convert formats: Support JSON fallback (e.g., load/save as JSON if YAML fails).
      - Profiles: Support multiple profiles (e.g., "dev" vs. "prod" in one file).
   3. Integrate back: Refactor the renderer to use this manager.
   4. Add GUI (bonus): Use Tkinter for a simple config editor.
   5. Comprehensive tests: Cover edge cases like malformed files, type errors.
   6. Package it: Make it installable via `setup.py`, with the renderer as an example app.

   *Deliverables*:
   - New `config_manager` module/CLI tool.
   - Updated project using it.
   - User guide (e.g., "How to Manage Configs").
   - Test coverage report (using `pytest`).

   *Learning Outcomes*:
   - Building reusable libraries/CLIs.
   - Advanced features like diffing and profiles.
   - Packaging and distribution.
   - Team collaboration (e.g., one handles CLI, another validation).
   - Time Estimate: 15-20 hours.



## Handling Versions

In a manually handled versioning system, you can keep track of source files using a combination of
structured directories, naming conventions, and a version log.


### 1. Structured Directories
Organize your source files in a well-structured directory hierarchy. This helps to keep things
organised and makes it easier to find specific versions of files.

```
project/
├── src/
│   ├── version1/
│   │   ├── file1.py
│   │   └── file2.py
│   ├── version2/
│   │   ├── file1.py
│   │   └── file2.py
│   └── current/
│       ├── file1.py
│       └── file2.py
└── CHANGES.txt
```

### 2. Naming Conventions

Use clear and consistent naming conventions for your directories and files. Include version numbers in
the directory names to easily identify different versions.

### 3. Version Log

Maintain a `CHANGES.txt` file in the root directory of your project. This file should contain detailed
records of changes, including dates, descriptions of changes, and any other relevant information.

#### Example of `CHANGES.txt`
```
CHANGES.txt

..

Version 1.0.0 (December 4, 2024)
- Initial release.
- Implemented the core graphics state management for the interpreter.
- Created basic PostScript-like commands (newpath, moveto, lineto, setrgbcolor, etc.).
- Developed a basic Rasterizer for drawing lines and filling shapes.
- Added PPM output support to export the canvas.

Version 0.9.0 (November 24, 2024)
- Pre-release.
- Initial prototype of the interpreter with basic stack operations.
- Early implementation of GraphicsState for managing stroke and fill colors.

```

### 4. Updating Process

Whenever you make changes to your files, follow the steps:

1. *Copy the current files to a new version directory*: Before making any changes, copy the
   files from the `current` directory to a new version directory with an incremented version
   number (e.g., `version3/`).

2. *Make changes in the `current` directory*: Edit the files in the `current` directory to
   implement your changes.

3. *Update the version log*: Record the changes made, along with the date and a brief
   description, in the `CHANGES.txt` file.

### Benefits of This Approach
- *Clarity*: Each version of the source files is clearly separated, making it easy to identify
  and retrieve previous versions.
- *Documentation*: The version log provides a history of changes, helping to understand the
  evolution of the project.
- *Simplicity*: This method is straightforward and does not require specialized tools or software.

With this approach you have a clear and organized way of keeping track of your source
files and their changes over time, even without automated version control systems.

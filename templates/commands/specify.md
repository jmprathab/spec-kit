---
name: specify
description: "Start a new feature by creating a specification and feature directory. This is the first step in the Spec-Driven Development lifecycle."
---

Start a new feature by creating a specification and feature directory.

This is the first step in the Spec-Driven Development lifecycle.

Given the feature description provided as an argument, do this:

1. Run the script `python spec_kit.py create-new-feature --json "{ARGS}"` from repo root and parse its JSON output for FEATURE_NAME and SPEC_FILE. All file paths must be absolute.
2. Load `templates/spec-template.md` to understand required sections.
3. Write the specification to SPEC_FILE using the template structure, replacing placeholders with concrete details derived from the feature description (arguments) while preserving section order and headings.
4. Report completion with feature name, spec file path, and readiness for the next phase.

Note: The script creates the feature directory, initializes the spec file, and sets it as the current active feature (stored in .current-feature file) before writing.

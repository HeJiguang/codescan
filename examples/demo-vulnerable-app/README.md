# Demo Vulnerable App

This tiny fixture exists so the repository can show what a CodeScan result looks like without requiring a live model setup.

It intentionally includes insecure patterns such as:

- hardcoded secrets
- shell execution with unsanitized input
- SQL built from string interpolation
- HTML rendering without output escaping

Use it only as a demonstration target.

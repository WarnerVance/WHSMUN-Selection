"""Package-bundled file templates (xlsx rosters, etc.).

Access the bundled `roster_template.xlsx` via:

    from importlib.resources import files, as_file
    with as_file(files("whsmun.templates") / "roster_template.xlsx") as path:
        ...
"""

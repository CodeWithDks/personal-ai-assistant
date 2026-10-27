"""
One-off patch (P0-4): stop the agent tools from returning raw exception text.

Run from the REPOSITORY ROOT:   python patch_tool_errors.py
It edits backend/app/ai/tools/tasks.py and notes.py, then you review with `git diff`.
It refuses to write anything unless it finds exactly the expected 11 spots.
"""
import pathlib
import re

FILES = {
    "backend/app/ai/tools/tasks.py": 6,
    "backend/app/ai/tools/notes.py": 5,
}

# except Exception as e:  ->  log the full error server-side, return a generic message
PATTERN = re.compile(
    r'(?P<indent>[ \t]*)except Exception as e:\n'
    r'(?P<body>(?:(?![ \t]*except ).*\n)*?)'
    r'(?P<msgindent>[ \t]*)"message": f"Could not (?P<what>[^:"]+): \{str\(e\)\}",',
)


def patch(text: str) -> tuple[str, int]:
    def repl(m: re.Match) -> str:
        indent = m.group("indent")
        what = m.group("what")
        body = m.group("body")
        # Some spots already log the error; only add a log line where none exists.
        log_line = (
            ""
            if "logger." in body
            else f'{indent}    logger.exception("Tool failed: could not {what}")\n'
        )
        return (
            f'{indent}except Exception:\n'
            f'{log_line}'
            f'{body}'
            f'{m.group("msgindent")}"message": "Could not {what}. Please try again.",'
        )

    return PATTERN.subn(repl, text)


def ensure_logger(text: str) -> str:
    if "logger = logging.getLogger" in text:
        return text
    lines = text.split("\n")
    # insert after the last top-level import line
    last_import = max(i for i, l in enumerate(lines) if l.startswith(("import ", "from ")))
    lines[last_import + 1:last_import + 1] = ["", "logger = logging.getLogger(__name__)"]
    out = "\n".join(lines)
    if "\nimport logging\n" not in out and not out.startswith("import logging\n"):
        out = "import logging\n" + out
    return out


results = {}
for path, expected in FILES.items():
    p = pathlib.Path(path)
    new_text, count = patch(p.read_text(encoding="utf-8"))
    if count != expected:
        raise SystemExit(f"ABORT: {path}: expected {expected} spots, found {count}. Nothing written.")
    results[p] = ensure_logger(new_text)

for p, text in results.items():
    p.write_text(text, encoding="utf-8")
    print(f"patched {p}")
print("Done. Review with: git diff")
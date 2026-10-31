"""Generate the student Jupyter notebooks (python/*.ipynb) from the Python lab sources (python/*.qmd).

The Python labs are written as Quarto documents (plain text, easy to edit and to review in git).
Quarto runs them when it builds the website. Students get clean, output-free .ipynb notebooks,
which this script writes next to each .qmd. Quarto runs it automatically before every render
(see `pre-render` in _quarto.yml). You can also run it by hand:  python tools/build_notebooks.py

Edit the .qmd files, not the .ipynb files: the notebooks are regenerated on every render.
Only the standard library is used, so this also runs on GitHub Actions.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY_DIR = ROOT / "python"

CHUNK_START = re.compile(r"^```\{python[^}]*\}\s*$")
FENCE = re.compile(r"^(```|~~~)")
HEADING = re.compile(r"^#{1,2} ")


def parse_front_matter(text):
    """Split a .qmd into (title, subtitle, body). Only simple `key: "value"` lines are read."""
    meta = {}
    if text.startswith("---"):
        end = text.index("\n---", 3)
        for line in text[3:end].splitlines():
            m = re.match(r"^(title|subtitle):\s*(.+?)\s*$", line)
            if m:
                value = m.group(2)
                if len(value) >= 2 and value[0] == value[-1] == "'":
                    value = value[1:-1].replace("''", "'")
                elif len(value) >= 2 and value[0] == value[-1] == '"':
                    value = value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
                meta[m.group(1)] = value
        text = text[end + 4:].lstrip("\n")
    return meta.get("title", ""), meta.get("subtitle", ""), text


def split_cells(body):
    """Turn the .qmd body into a list of (cell_type, source) pairs."""
    cells, buf, in_code, in_fence = [], [], False, False

    def flush(kind):
        text = "\n".join(buf).strip("\n")
        if text.strip():
            cells.append((kind, text))
        buf.clear()

    for line in body.splitlines():
        if in_code:
            if line.strip() == "```":
                flush("code")
                in_code = False
            elif not (line.startswith("#|") and not buf):  # drop leading `#|` Quarto chunk options
                buf.append(line)
            continue
        if not in_fence and CHUNK_START.match(line):
            flush("markdown")
            in_code = True
            continue
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and HEADING.match(line):
            flush("markdown")  # start a new markdown cell at each top-level heading
        buf.append(line)
    flush("markdown")
    return cells


def to_notebook(title, subtitle, cells):
    nb_cells = []
    header = f"# {title}\n\n*{subtitle}*" if subtitle else f"# {title}"
    if cells and cells[0][0] == "markdown" and not HEADING.match(cells[0][1]):
        cells = [("markdown", header + "\n\n" + cells[0][1])] + cells[1:]
    else:
        cells = [("markdown", header)] + cells
    for i, (kind, text) in enumerate(cells):
        lines = text.split("\n")
        source = [l + "\n" for l in lines[:-1]] + [lines[-1]]
        cell = {"cell_type": kind, "id": f"cell-{i:03d}", "metadata": {}, "source": source}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        nb_cells.append(cell)
    return {
        "cells": nb_cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build():
    for qmd in sorted(PY_DIR.glob("*.qmd")):
        title, subtitle, body = parse_front_matter(qmd.read_text(encoding="utf-8"))
        nb = to_notebook(title, subtitle, split_cells(body))
        out = qmd.with_suffix(".ipynb")
        new = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
        if not out.exists() or out.read_text(encoding="utf-8") != new:
            out.write_text(new, encoding="utf-8", newline="\n")
            print(f"notebook: {out.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    build()

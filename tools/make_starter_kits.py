"""Build the student starter kits each time Quarto renders the website.

Creates two zip files in downloads/ (copied into the website by Quarto):

  fw532-R-labs.zip       fw532.Rproj, install_packages.R, r/*.qmd, data/
  fw532-python-labs.zip  python/ (notebooks, sdmlab.py, requirements.txt), data/

Quarto runs this automatically (see `pre-render` in _quarto.yml). You can also
run it by hand from the project folder:  python tools/make_starter_kits.py
"""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS = ROOT / "downloads"

R_README = """\
FW 532 -- R lab starter kit
===========================

1. Unzip this folder somewhere you can find it (not inside a cloud-sync
   "Files On-Demand" folder if you can avoid it).
2. Double-click fw532.Rproj to open the project in RStudio
   (or File > Open Folder in Positron).
3. In the R console, run:   source("install_packages.R")
   This installs every package used this term and checks the data loads.
4. Open r/lab01-simulation.qmd and run the code chunks from top to bottom.

All labs read data/envStack.tif using here::here(), so keep the folder
structure as it is. Files the labs write go in output/.

Course website: https://hutchinson-lab.github.io/fw532/
"""

PY_README = """\
FW 532 -- Python lab starter kit
================================

1. Unzip this folder somewhere you can find it.
2. Create an environment and install the packages (once):

       cd fw532-python-labs
       python -m venv .venv
       .venv\\Scripts\\activate        (Windows)
       source .venv/bin/activate      (macOS / Linux)
       pip install -r python/requirements.txt

   (Using conda instead?  conda env create -f python/environment.yml)

3. Open python/lab01-simulation.ipynb in JupyterLab, VS Code, or Positron
   and run the cells from top to bottom.

Keep python/ and data/ side by side: the helper module python/sdmlab.py finds
data/envStack.tif automatically. Files the labs write go in output/.

Prefer not to install anything? Every notebook also runs on Google Colab --
use the "Open in Colab" links on the course website.

Course website: https://hutchinson-lab.github.io/fw532/
"""


def add_tree(zf, folder, arc_root, patterns):
    for pattern in patterns:
        for path in sorted((ROOT / folder).glob(pattern)):
            if path.is_file():
                zf.write(path, f"{arc_root}/{path.relative_to(ROOT).as_posix()}")


def build():
    DOWNLOADS.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(DOWNLOADS / "fw532-R-labs.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        root = "fw532-R-labs"
        zf.writestr(f"{root}/README.txt", R_README)
        for name in ["fw532.Rproj", "install_packages.R"]:
            zf.write(ROOT / name, f"{root}/{name}")
        add_tree(zf, "r", root, ["*.qmd", "*.R"])
        add_tree(zf, "data", root, ["*.tif", "README.md"])
        zf.writestr(f"{root}/output/.keep", "")

    with zipfile.ZipFile(DOWNLOADS / "fw532-python-labs.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        root = "fw532-python-labs"
        zf.writestr(f"{root}/README.txt", PY_README)
        add_tree(zf, "python", root, ["*.ipynb", "*.py", "requirements.txt", "environment.yml"])
        add_tree(zf, "data", root, ["*.tif", "README.md"])
        zf.writestr(f"{root}/output/.keep", "")

    for kit in sorted(DOWNLOADS.glob("*.zip")):
        print(f"starter kit: {kit.relative_to(ROOT)} ({kit.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    build()

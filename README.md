# FW 532 · Machine Learning in Species Distribution Modeling

Course website and lab materials for FW 532 (formerly FW 599) at Oregon State University.

**Website:** <https://hutchinson-lab.github.io/fw532/>

Every lab comes in two parallel versions, one in **R** and one in **Python** (written for beginners), plus an overview page on the website that motivates the lab and explains the key concepts.

## For students

Start at the website's [Get set up](https://hutchinson-lab.github.io/fw532/setup.html) page. Download the R or Python starter kit there, or clone this repository and open `fw532.Rproj` (R) or the `python/` notebooks.

## What's in this repository

```
fw532.Rproj            RStudio project (also used by students; paths use here::here())
install_packages.R     installs every R package used in the labs
data/envStack.tif      20 environmental layers (WorldClim + elevation), read by every lab
r/                     R labs (.qmd), one per lab plus demos
python/                Python labs: *.qmd (the source you edit) and *.ipynb (generated, clean
                       notebooks for students and Colab), sdmlab.py helper,
                       requirements.txt / environment.yml
labs/                  website overview page for each lab (motivation, concepts, links)
index.qmd, setup.qmd, schedule.qmd, readings.qmd   other website pages
_quarto.yml            website configuration (navigation, theme, sidebar)
assets/                theme (SCSS/CSS) and icon
tools/                 build_notebooks.py (.qmd -> .ipynb), make_starter_kits.py (student zips),
                       quarto.ps1 (local helper)
_freeze/               saved results of running the R and Python code (commit this!)
.github/workflows/     GitHub Actions: builds and publishes the site on every push
```

## For instructors: editing and publishing

### First-time connection to GitHub

1. **Create an empty repository** in the Hutchinson-Lab organization: <https://github.com/organizations/Hutchinson-Lab/repositories/new>. Name it `fw532` and make it **Public** (free GitHub Pages sites must be public). Do **not** add a README, .gitignore, or license; this folder already has them.
2. **Push this folder** (in a terminal, in this folder):
   ```bash
   git add -A
   git commit -m "FW 532 course website and labs"
   git remote add origin https://github.com/Hutchinson-Lab/fw532.git
   git push -u origin main
   ```
   The first push opens a browser window to sign in to GitHub (Git Credential Manager). After that, `git push` just works.
3. **Turn on Pages:** in the repository, go to *Settings → Pages → Build and deployment → Source* and choose **GitHub Actions**. Then open the *Actions* tab and re-run the "Publish website" workflow if the first run happened before you changed this setting.
4. The site appears at <https://hutchinson-lab.github.io/fw532/>.

### One-time setup on this computer

* R 4.5 with the lab packages: open `fw532.Rproj` and run `source("install_packages.R")`.
* A Python environment for building the Python pages (already created at `%USERPROFILE%\.venvs\fw532`). To recreate it:
  ```bash
  py -3.12 -m venv %USERPROFILE%\.venvs\fw532
  %USERPROFILE%\.venvs\fw532\Scripts\pip install -r python/requirements.txt
  ```
* Quarto: bundled with Positron and RStudio, or install from <https://quarto.org>.

`tools/quarto.ps1` runs Quarto with R 4.5 and that Python environment. It's needed because R 4.0.3 comes first on this computer's PATH.

### Edit → preview → publish

1. **Edit** a lab: `r/labNN-*.qmd` (R), `python/labNN-*.qmd` (Python), or `labs/NN-*.qmd` (overview page). Edit the Python `.qmd`, **not** the `.ipynb`. The notebooks are regenerated from the `.qmd` files every time the site is rendered, so edits made directly to a `.ipynb` are overwritten. (You can run a Python `.qmd` interactively in Positron, VS Code, or RStudio.)
2. **Preview** locally (PowerShell, in this folder):
   ```powershell
   .\tools\quarto.ps1 preview
   ```
   Quarto re-runs code only for files whose source changed and saves the results in `_freeze/`.
3. **Publish:** commit your changes, *including `_freeze/`*, and push:
   ```bash
   git add -A
   git commit -m "Update Lab 3"
   git push
   ```
   GitHub Actions rebuilds the site from the frozen results (no R or Python needed on GitHub). The site updates about two minutes later. Watch progress under the repository's **Actions** tab.

How re-running works:

* `.\tools\quarto.ps1 render` (the whole site) re-runs only the labs whose source changed since their saved results in `_freeze/`.
* `.\tools\quarto.ps1 render r/lab03-cart.qmd` (one file) always re-runs that file.
* To re-run everything (e.g., after updating packages), delete the `_freeze` folder and render the whole site. That takes about 15 minutes on a local disk and much longer on the network drive, so consider keeping your working copy of the repository on a local disk (GitHub then serves as the backup).

### Adding a lab

Create `r/labNN-name.qmd`, `python/labNN-name.qmd`, and `labs/NN-name.qmd` (copy an existing lab's overview page for the layout). Then add a section to the sidebar in `_quarto.yml`. The labs index lists `labs/0*.qmd` pages automatically, sorted by their `order:` field.

## Credits

Labs by Rebecca Hutchinson, updated for current R packages (terra, etc.) and translated to Python in 2026. Environmental data: WorldClim (<https://www.worldclim.org>).

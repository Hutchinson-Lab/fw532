"""
sdmlab -- small helper functions for the FW 532 Python labs.

In the R version of the labs, the `terra` package handles rasters (gridded
maps). Python has no single equivalent, so this module provides the handful of
raster operations the labs need, written with plain numpy / pandas /
matplotlib. Nothing here is magic -- feel free to read the code!

Key idea: a raster is just a 2-D array of numbers (rows x columns) plus the
information needed to place each cell on the map (the coordinates of the
top-left corner and the cell size). A *stack* of rasters is a 3-D array:
(layers x rows x columns).

Typical use
-----------
>>> import sdmlab as sdm
>>> env = sdm.load_env()                   # the course's environmental stack
>>> env.names[:3]                          # layer names
>>> pts = env.sample_random(500, seed=1)   # random land cells -> DataFrame
>>> sdm.plot_map(env["elevation"], env)    # draw one layer
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

__all__ = [
    "EnvStack",
    "load_env",
    "data_dir",
    "output_dir",
    "scale",
    "extract",
    "plot_map",
    "write_ascii_grid",
    "confusion_summary",
    "auc_ci",
]


# ---------------------------------------------------------------------------
# Finding files
# ---------------------------------------------------------------------------
def data_dir() -> Path:
    """Return the course `data/` folder (a sibling of this `python/` folder)."""
    here = Path(__file__).resolve().parent
    for folder in [here, *here.parents]:
        if (folder / "data" / "envStack.tif").exists():
            return folder / "data"
    raise FileNotFoundError(
        "Could not find data/envStack.tif. Keep the `python/` and `data/` "
        "folders side by side, as they are in the starter kit."
    )


def output_dir(*parts: str) -> Path:
    """Return (and create) a folder under `output/` for files a lab writes."""
    path = data_dir().parent / "output" / Path(*parts) if parts else data_dir().parent / "output"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# The environmental raster stack
# ---------------------------------------------------------------------------
class EnvStack:
    """A stack of co-registered rasters on a regular longitude/latitude grid.

    Attributes
    ----------
    values : ndarray, shape (n_layers, n_rows, n_cols)
        The data. Cells with no data (e.g. ocean) are NaN.
    names : list of str
        One name per layer.
    xmin, ymax : float
        Coordinates of the top-left corner of the grid.
    res : float
        Cell size (degrees).
    """

    def __init__(self, values, names, xmin, ymax, res, crs="EPSG:4326"):
        self.values = np.asarray(values, dtype=float)
        self.names = list(names)
        self.xmin, self.ymax, self.res, self.crs = float(xmin), float(ymax), float(res), crs

    # -- construction -------------------------------------------------------
    @classmethod
    def load(cls, path=None) -> "EnvStack":
        """Read a multi-layer GeoTIFF (default: data/envStack.tif)."""
        import rasterio  # imported here so the rest of the module works without it

        path = Path(path) if path else data_dir() / "envStack.tif"
        with rasterio.open(path) as src:
            values = src.read(masked=True).filled(np.nan).astype(float)
            names = [d or f"layer{i + 1}" for i, d in enumerate(src.descriptions)]
            return cls(values, names, src.bounds.left, src.bounds.top, src.res[0], str(src.crs))

    # -- basic properties ---------------------------------------------------
    @property
    def shape(self):
        """(n_rows, n_cols) of each layer."""
        return self.values.shape[1:]

    @property
    def extent(self):
        """(xmin, xmax, ymin, ymax) -- handy for matplotlib's imshow."""
        nrow, ncol = self.shape
        return (self.xmin, self.xmin + ncol * self.res, self.ymax - nrow * self.res, self.ymax)

    def __len__(self):
        return len(self.names)

    def __repr__(self):
        nrow, ncol = self.shape
        xmin, xmax, ymin, ymax = self.extent
        lines = [
            "EnvStack",
            f"  size       : {nrow} rows x {ncol} cols x {len(self)} layers",
            f"  resolution : {self.res:.6g} degrees",
            f"  extent     : {xmin:.4f}, {xmax:.4f}, {ymin:.4f}, {ymax:.4f}  (xmin, xmax, ymin, ymax)",
            f"  crs        : {self.crs}",
            "  layers     : " + ", ".join(self.names),
        ]
        return "\n".join(lines)

    def __getitem__(self, key):
        """env["elevation"] -> 2-D array;  env[["a", "b"]] -> smaller EnvStack."""
        if isinstance(key, (list, tuple)):
            idx = [self._index(k) for k in key]
            return EnvStack(self.values[idx], [self.names[i] for i in idx],
                            self.xmin, self.ymax, self.res, self.crs)
        return self.values[self._index(key)]

    def _index(self, key):
        if isinstance(key, (int, np.integer)):
            return int(key)
        try:
            return self.names.index(key)
        except ValueError:
            raise KeyError(f"No layer named {key!r}. Layers are: {self.names}") from None

    def copy(self) -> "EnvStack":
        return EnvStack(self.values.copy(), self.names, self.xmin, self.ymax, self.res, self.crs)

    # -- transformations ----------------------------------------------------
    def scale(self) -> "EnvStack":
        """Standardize every layer to mean 0, sd 1 (like R's `scale()`)."""
        out = self.copy()
        out.values = np.stack([scale(layer) for layer in self.values])
        return out

    def mask(self, keep) -> "EnvStack":
        """Set cells to NaN wherever the 2-D boolean array `keep` is False."""
        out = self.copy()
        out.values[:, ~np.asarray(keep, dtype=bool)] = np.nan
        return out

    # -- coordinates --------------------------------------------------------
    def rowcol(self, x, y):
        """Convert longitude/latitude to (row, col) indices of the grid."""
        row = np.floor((self.ymax - np.asarray(y, dtype=float)) / self.res).astype(int)
        col = np.floor((np.asarray(x, dtype=float) - self.xmin) / self.res).astype(int)
        return row, col

    def xy(self, row, col):
        """Convert (row, col) indices to the longitude/latitude of cell centres."""
        x = self.xmin + (np.asarray(col) + 0.5) * self.res
        y = self.ymax - (np.asarray(row) + 0.5) * self.res
        return x, y

    # -- getting data out ---------------------------------------------------
    def complete_cells(self, layer=None):
        """Flat indices of cells with data in every layer (or just in `layer`)."""
        if layer is None:
            ok = ~np.isnan(self.values).any(axis=0)
        else:
            ok = ~np.isnan(self[layer])
        return np.flatnonzero(ok)

    def sample_random(self, n, seed=None, layer=None) -> pd.DataFrame:
        """Sample `n` random cells (without replacement), like terra::spatSample.

        Only cells with data in every layer are eligible. If `layer` is given,
        cells only need data in that one layer, and the other columns may
        contain NaN (missing values).

        Returns a DataFrame with columns x, y (cell-centre coordinates) and
        one column per layer.
        """
        rng = np.random.default_rng(seed)
        cells = rng.choice(self.complete_cells(layer), size=n, replace=False)
        return self._cells_to_frame(cells)

    def to_frame(self, dropna=True) -> pd.DataFrame:
        """Every cell as one row of a DataFrame (index = flat cell number).

        This is how we predict a whole map: predict at every row, then put the
        predictions back on the grid with `to_map()`.
        """
        cells = self.complete_cells() if dropna else np.arange(np.prod(self.shape))
        return self._cells_to_frame(cells, keep_index=True)

    def _cells_to_frame(self, cells, keep_index=False):
        row, col = np.unravel_index(cells, self.shape)
        x, y = self.xy(row, col)
        df = pd.DataFrame({"x": x, "y": y})
        for name, layer in zip(self.names, self.values):
            df[name] = layer[row, col]
        if keep_index:
            df.index = pd.Index(cells, name="cell")
        return df

    def extract(self, x, y) -> pd.DataFrame:
        """Values of every layer at the points (x, y), like terra::extract."""
        row, col = self.rowcol(x, y)
        return pd.DataFrame({name: layer[row, col] for name, layer in zip(self.names, self.values)})

    def to_map(self, values, index=None) -> np.ndarray:
        """Put one value per cell back onto the grid, giving a 2-D array.

        `values` is usually a pandas Series whose index holds cell numbers (as
        returned by `to_frame()`); otherwise pass the cell numbers as `index`.
        Cells without a value are NaN.
        """
        if index is None:
            if not isinstance(values, pd.Series):
                raise ValueError("Pass a pandas Series from to_frame(), or give `index=`.")
            index = values.index
        out = np.full(self.shape, np.nan)
        out.flat[np.asarray(index)] = np.asarray(values, dtype=float)
        return out

    # -- plotting -----------------------------------------------------------
    def plot(self, layers=None, ncols=4, cmap="viridis", panel_size=(3.6, 2.2)):
        """Plot several layers in a grid of small maps, like plot() in terra."""
        layers = self.names if layers is None else layers
        nrows = int(np.ceil(len(layers) / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(panel_size[0] * ncols, panel_size[1] * nrows),
                                 squeeze=False, constrained_layout=True)
        for ax, name in zip(axes.flat, layers):
            plot_map(self[name], self, ax=ax, title=name, cmap=cmap, title_size=8)
            ax.tick_params(labelsize=6)
        for ax in axes.flat[len(layers):]:
            ax.set_visible(False)
        return fig


def load_env(path=None) -> EnvStack:
    """Load the course environmental stack (data/envStack.tif)."""
    return EnvStack.load(path)


# ---------------------------------------------------------------------------
# Working with single maps (2-D arrays)
# ---------------------------------------------------------------------------
def scale(a):
    """Standardize an array to mean 0 and sd 1, ignoring NaN (like R's scale())."""
    a = np.asarray(a, dtype=float)
    return (a - np.nanmean(a)) / np.nanstd(a, ddof=1)


def extract(grid, env: EnvStack, x, y):
    """Values of a 2-D map `grid` (on the same grid as `env`) at points (x, y)."""
    row, col = env.rowcol(x, y)
    return np.asarray(grid)[row, col]


def plot_map(grid, env: EnvStack, ax=None, title=None, cmap="viridis", vmin=None, vmax=None,
             colorbar=True, title_size=None, **imshow_kwargs):
    """Draw a 2-D map on longitude/latitude axes. Returns the matplotlib Axes.

    Add points on top with, e.g.:  ax.scatter(pts["x"], pts["y"], s=4, c="red")
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(grid, extent=env.extent, origin="upper", cmap=cmap,
                   vmin=vmin, vmax=vmax, interpolation="nearest", **imshow_kwargs)
    ax.set_aspect("equal")
    if title:
        ax.set_title(title, fontsize=title_size)
    if colorbar:
        plt.colorbar(im, ax=ax, shrink=0.8)
    return ax


def write_ascii_grid(grid, env: EnvStack, path, nodata=-9999):
    """Write a 2-D map as an ESRI ASCII grid (.asc), the format the Maxent app reads."""
    nrow, ncol = env.shape
    xmin, _, ymin, _ = env.extent
    header = (f"ncols {ncol}\nnrows {nrow}\nxllcorner {xmin:.10f}\nyllcorner {ymin:.10f}\n"
              f"cellsize {env.res:.10f}\nNODATA_value {nodata}\n")
    data = np.where(np.isnan(grid), nodata, grid)
    with open(path, "w") as f:
        f.write(header)
        np.savetxt(f, data, fmt="%.6g")


# ---------------------------------------------------------------------------
# Evaluation helpers (Python stand-ins for caret::confusionMatrix and pROC::ci)
# ---------------------------------------------------------------------------
def confusion_summary(y_true, y_pred, positive=1, show=True) -> dict:
    """Confusion matrix plus the summary statistics reported by caret::confusionMatrix."""
    from scipy import stats

    y_true = np.asarray(y_true) == positive
    y_pred = np.asarray(y_pred) == positive
    tp = int(np.sum(y_pred & y_true))
    tn = int(np.sum(~y_pred & ~y_true))
    fp = int(np.sum(y_pred & ~y_true))
    fn = int(np.sum(~y_pred & y_true))
    n = tp + tn + fp + fn

    acc = (tp + tn) / n
    ci = stats.binomtest(tp + tn, n).proportion_ci(confidence_level=0.95, method="exact")
    prevalence = (tp + fn) / n
    nir = max(prevalence, 1 - prevalence)  # "no information rate": always guess the majority class
    p_nir = stats.binomtest(tp + tn, n, nir, alternative="greater").pvalue
    p_exp = ((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp)) / n**2  # chance agreement
    kappa = (acc - p_exp) / (1 - p_exp)
    sens = tp / (tp + fn) if tp + fn else np.nan
    spec = tn / (tn + fp) if tn + fp else np.nan

    out = {
        "Accuracy": acc, "95% CI": (ci.low, ci.high), "No Information Rate": nir,
        "P-Value [Acc > NIR]": p_nir, "Kappa": kappa,
        "Sensitivity": sens, "Specificity": spec,
        "Pos Pred Value": tp / (tp + fp) if tp + fp else np.nan,
        "Neg Pred Value": tn / (tn + fn) if tn + fn else np.nan,
        "Prevalence": prevalence, "Detection Rate": tp / n,
        "Detection Prevalence": (tp + fp) / n, "Balanced Accuracy": (sens + spec) / 2,
    }
    if show:
        print("Confusion matrix (rows = prediction, columns = truth)")
        print(pd.DataFrame([[tn, fn], [fp, tp]], index=["pred 0", "pred 1"], columns=["true 0", "true 1"]))
        print()
        for k, v in out.items():
            print(f"{k:>22} : " + (f"({v[0]:.4f}, {v[1]:.4f})" if isinstance(v, tuple) else f"{v:.4f}"))
    return out


def auc_ci(y_true, scores, level=0.95):
    """AUC with a DeLong confidence interval (the default method of pROC::ci).

    Returns (lower, auc, upper).
    """
    from scipy import stats

    y_true = np.asarray(y_true).astype(bool)
    scores = np.asarray(scores, dtype=float)
    pos, neg = scores[y_true], scores[~y_true]
    m, n = len(pos), len(neg)
    # psi = 1 if a presence outranks an absence, 0.5 for ties, 0 otherwise
    psi = (pos[:, None] > neg[None, :]) + 0.5 * (pos[:, None] == neg[None, :])
    auc = psi.mean()
    v10 = psi.mean(axis=1)  # one value per presence
    v01 = psi.mean(axis=0)  # one value per absence
    se = np.sqrt(np.var(v10, ddof=1) / m + np.var(v01, ddof=1) / n)
    z = stats.norm.ppf(0.5 + level / 2)
    return max(0.0, auc - z * se), auc, min(1.0, auc + z * se)

"""Replot the packaged NEW_D1 processed system and reference maps."""
from pathlib import Path
import argparse
import json
import sys
sys.dont_write_bytecode = True
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from audit_panel_alignment import require_matplotlib_panel_alignment

SAMPLES = ("red", "green", "yellow", "blue")
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                     "font.size": 7.5, "axes.titlesize": 7.5, "axes.labelsize": 7.5,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.linewidth": .65,
                     "pdf.fonttype": 42, "svg.fonttype": "none",
                     "axes.spines.top": False, "axes.spines.right": False})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    ap.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "figures")
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    limits = json.loads((args.data_dir / "color_limits.json").read_text(encoding="utf-8"))
    fig = plt.figure(figsize=(183 / 25.4, 204 / 25.4))
    grid = fig.add_gridspec(4, 8, width_ratios=[1, .055, .46, 1, .055, .46, 1, .055],
                           left=.075, right=.935, bottom=.075, top=.895,
                           hspace=.64, wspace=.12)
    axes, rendered = [], []
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad(".7")
    diverge = plt.get_cmap("coolwarm").copy()
    diverge.set_bad(".7")
    titles = ("System\nBRDF", "Reference\nBRDF", "System\n− reference")
    for row, sample in enumerate(SAMPLES):
        with np.load(args.data_dir / (sample + "_550.npz"), allow_pickle=False) as z:
            t, p = z["theta_deg"], z["phi_deg"]
            a, g, mask = z["reconstruction"], z["reference"], z["comparison_mask"]
            delta = a - g
            assert np.array_equal(delta, z["difference"], equal_nan=True), "Difference mismatch"
            assert a.shape == g.shape == mask.shape == (t.size, p.size)
            assert np.all(np.diff(t) > 0) and np.all(np.diff(p) > 0), "Nonmonotone grid"
            dt, dp = np.diff(t), np.diff(p)
            assert np.allclose(dt, dt[0]) and np.allclose(dp, dp[0]), "Nonuniform pixel spacing"
            # Pixel-centre extent inherited from the final repaired display, no rotation.
            extent = [p[0] - dp[0] / 2, p[-1] + dp[-1] / 2,
                      t[-1] + dt[0] / 2, t[0] - dt[0] / 2]
            c = limits[sample]
            paired_images = []
            for col, (arr, label) in enumerate(zip((a, g, delta), titles)):
                ax = fig.add_subplot(grid[row, (0, 3, 6)[col]])
                axes.append(ax)
                low, high = ((c["bsdf_min"], c["bsdf_max"]) if col < 2
                             else (c["difference_min"], c["difference_max"]))
                im = ax.imshow(np.where(mask, arr, np.nan), extent=extent, origin="upper",
                               aspect="auto", interpolation="nearest",
                               vmin=low, vmax=high, cmap=cmap if col < 2 else diverge)
                paired_images.append(im)
                ax.set_xlim(0, 359)
                ax.set_ylim(70, 10)
                ax.set_facecolor(".7")
                ax.set_xticks([0, 90, 180, 270])
                ax.set_yticks([10, 30, 50, 70])
                ax.set_xlabel("φ (°)")
                if col == 0:
                    ax.set_ylabel(sample.capitalize() + "\nθ (°)")
                else:
                    ax.tick_params(axis="y", labelleft=False)
                if row == 0:
                    ax.set_title(label, pad=6)
                rendered.append({"sample": sample, "panel": label, "shape": list(arr.shape),
                                 "comparison_cells": int(mask.sum()), "vmin": low, "vmax": high,
                                 "xlim": [0, 359], "ylim": [70, 10], "extent": extent,
                                 "interpolation": "nearest", "origin": "upper"})
            for grid_col, image, ticks in ((1, paired_images[0], 4), (4, paired_images[1], 4),
                                           (7, paired_images[2], 3)):
                cax = fig.add_subplot(grid[row, grid_col])
                cbar = fig.colorbar(image, cax=cax, extend="both")
                cbar.locator = MaxNLocator(nbins=ticks)
                cbar.update_ticks()
                cbar.ax.tick_params(labelsize=6, length=2, pad=1)
                cbar.ax.set_ylabel("BRDF (sr$^{-1}$)" if grid_col < 7 else "ΔBRDF (sr$^{-1}$)",
                                  fontsize=7.5, labelpad=3)
    fig.suptitle("550 nm, normal incidence: system BRDF, reference and signed difference",
                 fontsize=8, y=.972)
    fig.text(.5, .943, "NEW_D1 processed data",
             ha="center", fontsize=7.5)
    stem = args.output_dir / "four550_reconstruction_GT_difference"
    require_matplotlib_panel_alignment(fig, axes=axes, json_out=str(stem) + ".alignment.json",
                                       strict=True)
    fig.savefig(str(stem) + ".png", dpi=300)
    fig.savefig(str(stem) + ".pdf")
    fig.savefig(str(stem) + ".svg")
    plt.close(fig)
    (args.output_dir / "rendered_panels.json").write_text(
        json.dumps(rendered, indent=2), encoding="utf-8")
    print("Exported PNG/PDF/SVG, all 12 panels; no numeric modification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Check published package checksums and direct array/mask identities."""
from pathlib import Path
import hashlib
import numpy as np


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = root / "CHECKSUMS.sha256"
    count = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        file = root / relative
        actual = hashlib.sha256(file.read_bytes()).hexdigest()
        assert actual == expected, "Checksum mismatch: " + relative
        count += 1
    for sample in ("red", "green", "yellow", "blue"):
        with np.load(root / "data" / (sample + "_550.npz"), allow_pickle=False) as z:
            a, g = z["reconstruction"], z["reference"]
            assert a.dtype == g.dtype == np.dtype("float64")
            assert a.shape == (len(z["theta_deg"]), len(z["phi_deg"]))
            assert np.array_equal(z["difference"], a - g, equal_nan=True)
            assert np.array_equal(z["comparison_mask"],
                                  z["source_display_mask"] & np.isfinite(a) & np.isfinite(g))
        print(sample + ": direct difference and comparison mask match")
    print(str(count) + " file checksums verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_analysis.py"
SPEC = importlib.util.spec_from_file_location("build_analysis", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BuildAnalysisTest(unittest.TestCase):
    def test_isotonic_fit_is_increasing(self) -> None:
        fitted = MODULE.isotonic_increasing(np.array([3.0, 2.0, 4.0, 1.0, 5.0]))
        self.assertTrue(np.all(np.diff(fitted) >= 0))
        self.assertAlmostEqual(float(fitted.mean()), 3.0)

    def test_activation_temperature_interpolates_half_rise(self) -> None:
        climatology = pd.DataFrame(
            {"temperature_c": [0.0, 10.0, 20.0], "interest_index": [10, 30, 90]}
        )
        self.assertAlmostEqual(MODULE.activation_temperature(climatology), 13.3333, 3)


if __name__ == "__main__":
    unittest.main()

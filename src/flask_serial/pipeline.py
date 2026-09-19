"""Modular CSI processing pipeline.

Stages are functions of signature ``(data, ...) -> data`` grouped into a
reorderable DSL. Input is a time-window matrix shaped
``(n_frames, n_subcarriers)`` of complex CSI I/Q samples; the terminal stage
produces a per-timestep motion score.

Amplitude extraction intentionally does **not** use ``CSIKit.get_CSI`` /
``get_metadata``: those crash on single-antenna streams (``TypeError: only
0-dimensional arrays can be converted to Python scalars``). We read
``frame.csi_matrix`` directly and squeeze, matching the ESP32 single-RX layout.

``hampel_filter`` is implemented locally rather than relying on
``CSIKit.util.filters.hampel``, whose rolling window includes the very sample
being tested (``csi[index-k:index+k]``) so an outlier never falls outside its
own median/std and is never removed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Tuple

import numpy as np
from scipy.signal import savgol_filter as _scipy_savgol

from CSIKit.util import filters as _csikit_filters

Array = np.ndarray


# --------------------------------------------------------------------------- #
# Individual stages: every function below maps an array to an array.
# --------------------------------------------------------------------------- #
def get_amplitude(data: "Array") -> Array:
    """Stage 1: convert complex I/Q to real magnitude (single-RX safe)."""
    return np.abs(np.squeeze(data))


def agc_compensation(data: Array, rssi: float = -65, noise_floor: float = -90) -> Array:
    """Stage 2: normalise across automatic-gain steps.

    A hardware gain step multiplies every subcarrier of a frame by the same
    constant. Dividing each frame by its own mean energy cancels that constant,
    so frames become directly comparable regardless of the receiver's AGC.
    """
    data = data.astype(np.float64, copy=False)
    frame_power = np.sqrt(np.mean(data ** 2, axis=1, keepdims=True)) + 1e-12
    return data / frame_power


def hampel_filter(data: Array, k: int = 3, nsigma: int = 3) -> Array:
    """Stage 3: remove burst/outlier spikes before any smoothing (axis=0).

    For each timestep the median/MAD are computed over the sliding window *not
    including* the point itself, so isolated spikes are reliably replaced.
    """
    data = data.astype(np.float64, copy=False)
    out = data.copy()
    for col in range(data.shape[1]):
        series = data[:, col]
        n = len(series)
        for i in range(n):
            lo = max(0, i - k)
            hi = min(n, i + k + 1)
            win = np.concatenate((series[lo:i], series[i + 1:hi]))
            if win.size == 0:
                continue
            median = np.median(win)
            mad = np.median(np.abs(win - median)) or 1e-12
            if abs(series[i] - median) > nsigma * 1.4826 * mad:
                out[i, col] = median
    return out


def butterworth_filter(data: Array, cutoff: float, fs: float, order: int = 4) -> Array:
    """Stage 4 (option A): Butterworth low-pass smoothing (axis 0)."""
    cols = np.apply_along_axis(
        lambda x: _csikit_filters.lowpass(x, cutoff=cutoff, fs=fs, order=order),
        axis=0, arr=data,
    )
    return cols


def savgol_filter(data: Array, window_length: int = 15, polyorder: int = 3) -> Array:
    """Stage 4 (option B): Savitzky-Golay zero-phase smoothing (axis 0)."""
    return _scipy_savgol(data, window_length=window_length, polyorder=polyorder, axis=0)


def subcarrier_selection(data: Array, keep: int = 2) -> Array:
    """Stage 5: keep the `keep` most temporally-variant subcarriers."""
    variances = np.var(data, axis=0)
    top = np.argsort(variances)[-int(keep):]
    return data[:, top]


def temporal_variance(data: Array, frame_size: int = 5) -> Array:
    """Stage 6: sliding-window variance of amplitude (motion metric)."""
    n = data.shape[0]
    frame_size = int(min(frame_size, n))
    out = np.full(data.shape, np.nan)
    for col in range(data.shape[1]):
        for i in range(n - frame_size + 1):
            out[i, col] = np.var(data[i:i + frame_size, col])
    return out


# --------------------------------------------------------------------------- #
#  Pipeline orchestration: a reorderable list of named stages.
#  Stages may be configured at build time with ``functools.partial`` so the
#  same DSL list can be re-ordered without touching any code.
# --------------------------------------------------------------------------- #
Stage = Tuple[str, Callable[..., Array]]


@dataclass
class Pipeline:
    stages: List[Stage] = field(default_factory=list)

    @property
    def stage_names(self) -> List[str]:
        return [name for name, _ in self.stages]

    def run(self, data: Array) -> Array:
        for _name, fn in self.stages:
            data = fn(data)
        return data
"""Contract tests for the modular CSI processing pipeline.

Stages are pure functions ``(array, state) -> array`` grouped by name into a
reorderable DSL. The pipeline consumes a time-window matrix shaped
``(n_frames, n_subcarriers)`` of complex CSI I/Q samples and produces a motion
score per time step.

Deliberately avoided: ``CSIKit.get_CSI``/``get_metadata`` which crash on
single-antenna streams (TypeError: only 0-dimensional arrays can be converted
to Python scalars in csitools.get_CSI). Amplitude extraction is done with
``np.abs(np.squeeze(frame.csi_matrix))`` instead.
"""
import numpy as np
import pytest

from flask_serial.pipeline import (
    Pipeline,
    agc_compensation,
    get_amplitude,
    hampel_filter,
    savgol_filter,
    subcarrier_selection,
    temporal_variance,
)


def _synthetic_window(n_frames=50, n_subcarriers=64, static=False):
    t = np.arange(n_frames) / 10.0
    amplitude = np.ones((n_frames, n_subcarriers))
    subcarrier = np.arange(n_subcarriers)
    for k in range(n_subcarriers):
        amplitude[:, k] += 0.5 * np.sin(2 * np.pi * 0.8 * t + subcarrier[k] * 0.1)
    if not static:
        # Moving body -> stronger, low-frequency modulation
        amplitude += 2.0 * np.sin(2 * np.pi * 0.2 * t)[:, None]
    phase = np.linspace(0, 0.3 * np.pi, n_subcarriers)[None, :] + 0.1 * t[:, None]
    return amplitude.astype(np.complex128) * np.exp(1j * phase)


def test_single_antenna_extraction_uses_csi_matrix_not_get_csi():
    """Amplitude from a (n_sub, 1) matrix must work (get_CSI crash regression)."""
    complex_matrix = np.array(
        [1., 2.] * 64, dtype=np.float32
    ).view(np.complex64).reshape(64, 1)

    amplitudes = get_amplitude(complex_matrix)

    assert amplitudes.shape == (64,)
    assert np.allclose(amplitudes, np.abs(complex_matrix[:, 0]))


def test_get_amplitude_squeezes_single_rx_keeps_frame_axis():
    window = _synthetic_window()  # (50, 64)
    out = get_amplitude(window)
    assert out.shape == (50, 64)
    assert np.isrealobj(out)


def test_hampel_removes_isolated_spike():
    clean = np.full((100, 1), 1.0)
    noisy = clean.copy()
    noisy[50, 0] = 100.0

    cleaned = hampel_filter(noisy, k=3, nsigma=3)

    assert cleaned.shape == noisy.shape
    assert cleaned[50, 0] == pytest.approx(1.0, abs=1e-6)
    assert np.max(np.abs(cleaned - clean)) < 1e-6


def test_savgol_smooths_without_phase_shift():
    t = np.linspace(0, 2 * np.pi, 200)
    sig = np.sin(t)[:, None]

    smoothed = savgol_filter(sig, window_length=15, polyorder=3)

    assert smoothed.shape == sig.shape
    # Savitzky-Golay is zero-phase: output lag ~0
    assert np.abs(smoothed[150, 0] - sig[150, 0]) < 0.05


def test_agc_compensation_normalizes_frame_energy():
    amp = np.abs(_synthetic_window())
    amp[:, :] = 1.0
    amp[:10, :] = 3.0  # simulated hardware gain step: same factor, all subcarriers

    corrected = agc_compensation(amp, rssi=-65, noise_floor=-90)

    assert corrected.shape == amp.shape
    assert np.all(np.isfinite(corrected))
    # Per-frame energy equalised: the gain step is removed from energy.
    energies = np.sqrt(np.mean(corrected ** 2, axis=1))
    assert np.allclose(energies, 1.0, atol=1e-6)


def test_subcarrier_selection_keeps_top_variance_indices():
    amp = np.zeros((100, 16))
    amp[:, 0] = np.sin(np.linspace(0, 4, 100))
    amp[:, 5] = 3.0 * np.sin(np.linspace(0, 8, 100))

    selected = subcarrier_selection(amp, keep=2)

    assert selected.shape == (100, 2)
    # top-2 variance are subcarriers {0, 5}; columns preserve original values
    assert np.allclose(selected[:, 0], amp[:, 0])
    assert np.allclose(selected[:, 1], amp[:, 5])


def test_temporal_variance_high_for_moving_low_for_static():
    moving = temporal_variance(np.abs(_synthetic_window(static=False)), frame_size=5)
    static = temporal_variance(np.abs(_synthetic_window(static=True)), frame_size=5)

    assert moving.shape[0] == 50
    assert static.shape[0] == 50
    assert float(np.nanmean(moving)) > float(np.nanmean(static))


def test_pipeline_orders_stages_by_registration():
    stages = [
        ("amp", get_amplitude),
        ("agc", agc_compensation),
        ("hampel", hampel_filter),
        ("smooth", savgol_filter),
        ("select", subcarrier_selection),
        ("var", temporal_variance),
    ]
    pipeline = Pipeline(stages)

    window = _synthetic_window()
    result = pipeline.run(window)

    assert result.shape == (50, 2)
    assert pipeline.stage_names == [
        "amp", "agc", "hampel", "smooth", "select", "var",
    ]


def test_pipeline_is_reorderable_without_code_change():
    stages = [
        ("amp", get_amplitude),
        ("var", temporal_variance),
        ("select", subcarrier_selection),
    ]
    pipeline = Pipeline(stages)
    window = _synthetic_window()
    result = pipeline.run(window)
    assert result.shape == (50, 2)
    assert pipeline.stage_names == ["amp", "var", "select"]

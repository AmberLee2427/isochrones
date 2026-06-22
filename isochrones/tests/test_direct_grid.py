import itertools

import numpy as np
import pandas as pd
import pytest

from isochrones.mist.isochrone import MIST_EvolutionTrack


class DummyGrid(object):
    def __init__(self, df):
        self.df = df


class DummyIso(object):
    def __init__(self, df):
        self.model_grid = DummyGrid(df)


class DummyBCGrid(object):
    def interp(self, pars, bands):
        Teff = np.atleast_1d(pars[0])
        return np.zeros((len(Teff), len(bands)))


def _direct_grid_df():
    mass0 = 0.888754
    rows = []
    index = []
    for age, feh in itertools.product([10.0], [-1.0, -0.75]):
        masses = [0.8, 0.878] if feh == -1.0 else [0.8, mass0, 1.0]
        for eep, initial_mass in enumerate(masses):
            rows.append(
                dict(
                    eep=eep,
                    age=age,
                    feh=feh,
                    mass=initial_mass,
                    initial_mass=initial_mass,
                    radius=1.0 + initial_mass,
                    density=1.0,
                    logTeff=3.7,
                    Teff=5000 + 100 * (initial_mass - mass0) + 10 * (age - 10.0) + 100 * (feh + 0.89),
                    logg=4.4 + 0.1 * (initial_mass - mass0),
                    logL=0.0,
                    Mbol=4.74 - (initial_mass - mass0),
                    phase=2,
                )
            )
            index.append((age, feh, eep))
    df = pd.DataFrame(rows)
    df.index = pd.MultiIndex.from_tuples(index)
    return df


def _mixed_phase_direct_grid_df():
    rows = []
    index = []
    for eep, (initial_mass, phase) in enumerate([(0.8, 0), (1.0, 1)]):
        rows.append(
            dict(
                eep=eep,
                age=10.0,
                feh=0.0,
                mass=initial_mass,
                initial_mass=initial_mass,
                radius=1.0 + initial_mass,
                density=1.0,
                logTeff=3.7,
                Teff=5000 + 100 * initial_mass,
                logg=4.4 + 0.1 * initial_mass,
                logL=0.0,
                Mbol=4.74 - initial_mass,
                phase=phase,
            )
        )
        index.append((10.0, 0.0, eep))
    df = pd.DataFrame(rows)
    df.index = pd.MultiIndex.from_tuples(index)
    return df


def _no_phase_direct_grid_df():
    df = _direct_grid_df()
    return df.drop(columns=["phase"])


def test_generate_default_does_not_direct_grid_fallback(monkeypatch):
    track = MIST_EvolutionTrack(bands=["IRAC_3.6"], version="1.2")

    monkeypatch.setattr(track, "get_eep", lambda *args, **kwargs: np.nan)
    monkeypatch.setattr(track, "interp_value", lambda *args, **kwargs: np.array([np.nan]))
    monkeypatch.setattr(
        track,
        "generate_direct_grid",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("direct grid fallback was used")),
    )

    df = track.generate(0.888754, 10.0, -0.89, props=["Teff"], bands=[])

    assert np.isnan(df["Teff"].iloc[0])


def test_generate_direct_grid_known_eep_nan_case_stays_strict(monkeypatch):
    track = MIST_EvolutionTrack(bands=["IRAC_3.6"], version="1.2")
    track._iso = DummyIso(_direct_grid_df())
    track._bc_grid = DummyBCGrid()

    monkeypatch.setattr(
        track,
        "get_eep",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("get_eep should not be used")),
    )

    df = track.generate(
        0.888754,
        10.0,
        -0.89,
        props=["Teff", "logg", "feh", "Mbol"],
        bands=["IRAC_3.6"],
        interp_method="direct_grid",
        distance=1059.3788781121696,
        AV=0,
    )

    assert np.isnan(df["Teff"].iloc[0])
    assert np.isnan(df["IRAC_3.6_mag"].iloc[0])


def test_generate_direct_grid_nearest_known_eep_nan_case(monkeypatch):
    track = MIST_EvolutionTrack(bands=["IRAC_3.6"], version="1.2")
    track._iso = DummyIso(_direct_grid_df())
    track._bc_grid = DummyBCGrid()

    monkeypatch.setattr(
        track,
        "get_eep",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("get_eep should not be used")),
    )

    df = track.generate(
        0.888754,
        10.0,
        -0.89,
        props=["Teff", "logg", "feh", "Mbol"],
        bands=["IRAC_3.6"],
        interp_method="direct_grid_nearest",
        distance=1059.3788781121696,
        AV=0,
    )

    assert np.isfinite(df["Teff"].iloc[0])
    assert np.isfinite(df["IRAC_3.6_mag"].iloc[0])
    assert np.isclose(df["requested_age"].iloc[0], 10.0)
    assert np.isclose(df["initial_feh"].iloc[0], -0.89)


def test_generate_direct_grid_mixed_phase_returns_nan(monkeypatch):
    track = MIST_EvolutionTrack(bands=["IRAC_3.6"], version="1.2")
    track._iso = DummyIso(_mixed_phase_direct_grid_df())
    track._bc_grid = DummyBCGrid()

    monkeypatch.setattr(
        track,
        "get_eep",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("get_eep should not be used")),
    )

    df = track.generate(
        0.9,
        10.0,
        0.0,
        props=["Teff", "logg", "feh", "Mbol"],
        bands=["IRAC_3.6"],
        interp_method="direct_grid",
    )

    assert np.isnan(df["Teff"].iloc[0])
    assert np.isnan(df["IRAC_3.6_mag"].iloc[0])


def test_generate_direct_grid_without_phase_raises(monkeypatch):
    track = MIST_EvolutionTrack(bands=["IRAC_3.6"], version="1.2")
    track._iso = DummyIso(_no_phase_direct_grid_df())
    track._bc_grid = DummyBCGrid()

    monkeypatch.setattr(
        track,
        "get_eep",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("get_eep should not be used")),
    )

    with pytest.raises(ValueError, match="requires a phase column"):
        track.generate(
            0.888754,
            10.0,
            -0.89,
            props=["Teff", "logg", "feh", "Mbol"],
            bands=["IRAC_3.6"],
            interp_method="direct_grid",
        )


def test_generate_direct_grid_nearest_mixed_phase_returns_finite(monkeypatch):
    track = MIST_EvolutionTrack(bands=["IRAC_3.6"], version="1.2")
    track._iso = DummyIso(_mixed_phase_direct_grid_df())
    track._bc_grid = DummyBCGrid()

    monkeypatch.setattr(
        track,
        "get_eep",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("get_eep should not be used")),
    )

    df = track.generate(
        0.9,
        10.0,
        0.0,
        props=["Teff", "logg", "feh", "Mbol"],
        bands=["IRAC_3.6"],
        interp_method="direct_grid_nearest",
    )

    assert np.isfinite(df["Teff"].iloc[0])
    assert np.isfinite(df["IRAC_3.6_mag"].iloc[0])

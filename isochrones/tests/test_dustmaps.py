"""Tests for the DustMap wrapper and DustMapAVPrior.

The tests here do not actually download dust map data -- they test the
interface, error handling, and prior mechanics without requiring the
external dustmaps package to be configured.
"""

import numpy as np
import pytest

from isochrones.dustmaps import DustMap, get_AV_from_dustmap, _SUPPORTED_MAPS
from isochrones.priors import DustMapAVPrior, AVPrior


# --- DustMap interface ---

def test_supported_map_names():
    for name in ["bayestar2019", "bayestar2017", "bayestar2015", "sfd", "planck"]:
        assert name in _SUPPORTED_MAPS


def test_unknown_map_raises():
    with pytest.raises(ValueError, match="Unknown dust map"):
        DustMap(map_name="notamap")


def test_default_map_name():
    dm = DustMap()
    assert dm.map_name == "bayestar2019"


def test_is_3d():
    assert DustMap("bayestar2019").is_3d
    assert DustMap("bayestar2017").is_3d
    assert not DustMap("sfd").is_3d
    assert not DustMap("planck").is_3d


def test_lazy_initialization():
    dm = DustMap()
    # dustmap should not be loaded yet
    assert dm._dustmap is None


def test_2d_map_warns_on_distance(monkeypatch):
    """2D maps should warn rather than silently ignore the distance arg."""
    import warnings

    # Mock the dustmap so we don't need the actual data
    class FakeSFDQuery:
        def __call__(self, coords):
            return 0.1

    dm = DustMap("sfd")
    dm._dustmap = FakeSFDQuery()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        dm.get_AV(ra=83.8, dec=-5.4, distance=500)
        assert any("2D map" in str(warning.message) for warning in w)


def test_get_AV_samples_raises_for_2d():
    dm = DustMap("sfd")
    with pytest.raises(ValueError, match="2D map"):
        dm.get_AV_samples(83.8, -5.4)


# --- DustMapAVPrior ---

class FakeDustMap:
    """Returns a fixed A_V for any coordinates."""
    def get_AV(self, ra, dec, distance=None):
        return 0.8  # mag


def test_dustmap_av_prior_ceiling(monkeypatch):
    """DustMapAVPrior should set upper bound from dust map + padding."""
    # DustMapAVPrior uses `from . import dustmaps as _dustmaps_mod` then
    # calls _dustmaps_mod.DustMap, so we patch at the module attribute level.
    import isochrones.dustmaps as dm_mod
    monkeypatch.setattr(dm_mod, "DustMap", lambda map_name=None: FakeDustMap())

    prior = DustMapAVPrior(ra=83.8, dec=-5.4)
    lo, hi = prior.bounds
    assert lo == 0
    # 0.8 * 1.5 = 1.2
    assert np.isclose(hi, 1.2)


def test_dustmap_av_prior_floor(monkeypatch):
    """Even if the dust map returns near-zero, keep a minimum floor."""
    import isochrones.dustmaps as dm_mod

    class NearZeroDustMap:
        def get_AV(self, ra, dec, distance=None):
            return 0.01

    monkeypatch.setattr(dm_mod, "DustMap", lambda map_name=None: NearZeroDustMap())

    prior = DustMapAVPrior(ra=83.8, dec=-5.4)
    lo, hi = prior.bounds
    assert hi >= 0.5  # floor enforced


def test_dustmap_av_prior_is_flat(monkeypatch):
    """DustMapAVPrior should have uniform PDF within bounds."""
    import isochrones.dustmaps as dm_mod
    monkeypatch.setattr(dm_mod, "DustMap", lambda map_name=None: FakeDustMap())

    prior = DustMapAVPrior(ra=83.8, dec=-5.4)
    lo, hi = prior.bounds
    # flat prior: all values in (lo, hi) should have equal pdf
    xs = np.linspace(lo + 0.01, hi - 0.01, 10)
    pdfs = [prior.pdf(x) for x in xs]
    assert np.allclose(pdfs, pdfs[0])


def test_dustmap_av_prior_subclasses_avprior():
    """DustMapAVPrior must be usable wherever AVPrior is used."""
    assert issubclass(DustMapAVPrior, AVPrior)


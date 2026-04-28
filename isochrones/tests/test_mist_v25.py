"""Tests for MIST v2.5 support.

Mirrors test_basic.py but exercises v2.5-specific features:
  - Extended metallicity grid (17 fehs vs. 15)
  - Version-aware URL dispatch
  - New filter systems (Roman, Euclid, Gaia EDR3)
  - Alpha-enhanced grid selection
  - WD EEP range infrastructure

These tests are intentionally fast -- they check plumbing and structure
rather than full grid downloads.
"""

import numpy as np
import pytest

from isochrones.mist.models import MIST_VERSIONS, MISTIsochroneGrid, MISTEvolutionTrackGrid
from isochrones.mist.bc import MISTBolometricCorrectionGrid
from isochrones.mist.eep import max_eep
from isochrones.mist.isochrone import MIST_Isochrone, MIST_EvolutionTrack


def _make_iso_grid(version, **kwargs):
    g = MISTIsochroneGrid.__new__(MISTIsochroneGrid)
    g.kwargs = dict(version=version, vvcrit=0.4, kind="full_isos")
    g.kwargs.update(kwargs)
    g._df = None
    g._df_orig = None
    g._interp = None
    g._interp_orig = None
    g._limits = {}
    return g


def _make_track_grid(version, afe=0.0, **kwargs):
    g = MISTEvolutionTrackGrid.__new__(MISTEvolutionTrackGrid)
    g.kwargs = dict(version=version, vvcrit=0.4, afe=afe)
    g.kwargs.update(kwargs)
    g._df = None
    g._df_orig = None
    g._interp = None
    g._interp_orig = None
    g._limits = {}
    g._fehs = None
    g._masses = None
    g._approx_eep_interp = None
    g._eep_interps = None
    g._primary_eeps_arr = None
    return g


# --- Version registry ---

def test_versions_exist():
    assert "1.2" in MIST_VERSIONS
    assert "2.5" in MIST_VERSIONS


def test_v25_has_more_fehs():
    g12 = _make_iso_grid("1.2")
    g25 = _make_iso_grid("2.5")
    assert len(g25.fehs) == 17
    assert len(g12.fehs) == 15
    # v2.5 adds -2.75 and -2.25
    assert -2.75 in g25.fehs
    assert -2.25 in g25.fehs
    assert -2.75 not in g12.fehs


def test_bounds_are_version_specific():
    g12 = _make_iso_grid("1.2")
    g25 = _make_iso_grid("2.5")
    bounds12 = dict(g12.bounds)
    bounds25 = dict(g25.bounds)
    # v2.5 extends the age ceiling slightly
    assert bounds25["age"][1] >= bounds12["age"][1]


# --- URL dispatch ---

def test_v12_iso_url():
    g = _make_iso_grid("1.2")
    url = g.get_tarball_url()
    assert "waps.cfa.harvard.edu" in url
    assert "MIST_v1.2_vvcrit0.4_full_isos.txz" in url


def test_v25_iso_url():
    g = _make_iso_grid("2.5")
    url = g.get_tarball_url()
    assert "mist.science" in url
    assert "isos/UBVRIplus.txz" in url


def test_v12_track_url():
    g = _make_track_grid("1.2")
    url = g.get_tarball_url(-0.5)
    assert "waps.cfa.harvard.edu" in url
    assert "MIST_v1.2" in url


def test_v25_track_url():
    g = _make_track_grid("2.5", afe=0.0)
    url = g.get_tarball_url(-0.5)
    assert "mist.science" in url
    assert "eeps/" in url
    assert "afe_p0" in url


def test_v25_track_url_alpha():
    g = _make_track_grid("2.5", afe=0.4)
    url = g.get_tarball_url(-0.5)
    assert "afe_p4" in url


def test_v25_track_url_negative_alpha():
    g = _make_track_grid("2.5", afe=-0.2)
    url = g.get_tarball_url(-0.5)
    assert "afe_m2" in url


# --- kwarg_tag cache isolation ---

def test_iso_kwarg_tag_v12():
    g = _make_iso_grid("1.2")
    assert "_v1.2_vvcrit0.4_full_isos" in g.kwarg_tag


def test_iso_kwarg_tag_v25():
    g = _make_iso_grid("2.5")
    assert "_v2.5_vvcrit0.4" in g.kwarg_tag
    # v2.5 drops the kind suffix
    assert "full_isos" not in g.kwarg_tag


def test_track_kwarg_tag_v25_includes_afe():
    g = _make_track_grid("2.5", afe=0.4)
    assert "afe_p4" in g.kwarg_tag

    g0 = _make_track_grid("2.5", afe=0.0)
    assert "afe_p0" in g0.kwarg_tag
    assert g0.kwarg_tag != g.kwarg_tag


# --- EEP dispatch ---

def test_max_eep_dispatch():
    g12 = _make_iso_grid("1.2")
    g25 = _make_iso_grid("2.5")
    # Both versions use max_eep (v1.2 analytical); v2.5 track ceiling is data-derived
    assert g12.max_eep(1.0, 0.0) == max_eep(1.0, 0.0)
    assert g25.max_eep(1.0, 0.0) == max_eep(1.0, 0.0)


# --- Bolometric correction grid ---

def test_bc_gaia_v12_gives_dr2rev():
    bc = MISTBolometricCorrectionGrid(bands=["G", "BP", "RP"], version="1.2")
    assert bc.band_map["G"] == "Gaia_G_DR2Rev"
    assert bc.band_map["BP"] == "Gaia_BP_DR2Rev"
    assert bc.band_map["RP"] == "Gaia_RP_DR2Rev"


def test_bc_gaia_v25_gives_edr3():
    bc = MISTBolometricCorrectionGrid(bands=["G", "BP", "RP"], version="2.5")
    assert bc.band_map["G"] == "Gaia_G_EDR3"
    assert bc.band_map["BP"] == "Gaia_BP_EDR3"
    assert bc.band_map["RP"] == "Gaia_RP_EDR3"


def test_bc_url_v12():
    bc = MISTBolometricCorrectionGrid(bands=["G"], version="1.2")
    url = bc.get_tarball_url("UBVRIplus")
    assert "waps.cfa.harvard.edu" in url


def test_bc_url_v25():
    bc = MISTBolometricCorrectionGrid(bands=["G"], version="2.5")
    url = bc.get_tarball_url("UBVRIplus")
    assert "mist.science" in url
    assert "BC_tables/v2" in url


# --- New filter systems ---

def test_roman_in_phot_bands():
    assert "Roman" in MISTBolometricCorrectionGrid.phot_bands
    assert "Roman_F062" in MISTBolometricCorrectionGrid.phot_bands["Roman"]
    assert "Roman_F184" in MISTBolometricCorrectionGrid.phot_bands["Roman"]


def test_euclid_in_phot_bands():
    assert "Euclid" in MISTBolometricCorrectionGrid.phot_bands
    assert "Euclid_VIS" in MISTBolometricCorrectionGrid.phot_bands["Euclid"]
    assert "Euclid_H" in MISTBolometricCorrectionGrid.phot_bands["Euclid"]


def test_roman_band_resolution():
    phot, band = MISTBolometricCorrectionGrid.get_band("Roman_F062")
    assert phot == "Roman"
    assert band == "Roman_F062"

    phot, band = MISTBolometricCorrectionGrid.get_band("Roman_F146")
    assert phot == "Roman"
    assert band == "Roman_F146"


def test_euclid_band_resolution():
    phot, band = MISTBolometricCorrectionGrid.get_band("Euclid_VIS")
    assert phot == "Euclid"
    assert band == "Euclid_VIS"

    phot, band = MISTBolometricCorrectionGrid.get_band("Euclid_H")
    assert phot == "Euclid"
    assert band == "Euclid_H"


def test_gaia_edr3_band_in_phot_bands():
    assert "Gaia_G_EDR3" in MISTBolometricCorrectionGrid.phot_bands["UBVRIplus"]
    assert "Gaia_BP_EDR3" in MISTBolometricCorrectionGrid.phot_bands["UBVRIplus"]
    assert "Gaia_RP_EDR3" in MISTBolometricCorrectionGrid.phot_bands["UBVRIplus"]


def test_unknown_band_raises():
    with pytest.raises(ValueError, match="cannot resolve band"):
        MISTBolometricCorrectionGrid.get_band("NotABand_X99")


# --- Backward compatibility ---

def test_v12_defaults_unchanged():
    """Default kwargs must not change -- existing user code must keep working."""
    assert MISTIsochroneGrid.default_kwargs["version"] == "1.2"
    assert MISTIsochroneGrid.default_kwargs["vvcrit"] == 0.4
    assert MISTIsochroneGrid.default_kwargs["kind"] == "full_isos"


def test_v12_fehs_unchanged():
    g = _make_iso_grid("1.2")
    expected = np.array((-4.00, -3.50, -3.00, -2.50, -2.00, -1.75, -1.50,
                         -1.25, -1.00, -0.75, -0.50, -0.25, 0.00, 0.25, 0.50))
    assert np.allclose(g.fehs, expected)

import re
import warnings

from .config import on_rtd

if not on_rtd:
    from astropy.coordinates import SkyCoord
    from six.moves import urllib


def get_AV_infinity(ra, dec, frame="icrs"):
    """Gets A_V extinction at infinity toward (ra, dec) by scraping NED.

    .. deprecated::
        Use :class:`isochrones.dustmaps.DustMap` instead, which supports
        3D distance-dependent extinction via the modern ``dustmaps`` package.

    :param ra,dec:
        Desired coordinates, in degrees.
    :param frame: (optional)
        Frame of input coordinates (e.g., ``'icrs', 'galactic'``)
    """
    try:
        import dustmaps as _dm  # noqa: F401
        _alt = " Use isochrones.dustmaps.DustMap instead (pip install isochrones[dustmaps])."
    except ImportError:
        _alt = ""
    warnings.warn(
        "get_AV_infinity queries NED and is fragile." + _alt,
        DeprecationWarning,
        stacklevel=2,
    )
    coords = SkyCoord(ra, dec, unit="deg", frame=frame).transform_to("icrs")

    rah, ram, ras = coords.ra.hms
    decd, decm, decs = coords.dec.dms
    if decd > 0:
        decsign = "%2B"
    else:
        decsign = "%2D"
    url = (
        "http://ned.ipac.caltech.edu/cgi-bin/nph-calc?in_csys=Equatorial&in_equinox=J2000.0&obs_epoch=2010&lon="
        + "%i" % rah
        + "%3A"
        + "%i" % ram
        + "%3A"
        + "%05.2f" % ras
        + "&lat=%s" % decsign
        + "%i" % abs(decd)
        + "%3A"
        + "%i" % abs(decm)
        + "%3A"
        + "%05.2f" % abs(decs)
        + "&pa=0.0&out_csys=Equatorial&out_equinox=J2000.0"
    )

    AV = None
    for line in urllib.request.urlopen(url).readlines():
        m = re.search(b"^Landolt V \(0.54\)\s+(\d+\.\d+)", line)
        if m:
            AV = float(m.group(1))
            break

    if AV is None:
        raise RuntimeError("AV query fails!  URL is {}".format(url))

    return AV

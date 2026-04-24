import warnings

import numpy as np

from .logger import getLogger


_SUPPORTED_MAPS = {
    "bayestar2019": ("dustmaps.bayestar", "BayestarQuery"),
    "bayestar2017": ("dustmaps.bayestar", "BayestarQuery"),
    "bayestar2015": ("dustmaps.bayestar", "BayestarQuery"),
    "sfd": ("dustmaps.sfd", "SFDQuery"),
    "planck": ("dustmaps.planck", "PlanckQuery"),
}

# R_V = 3.1; conversion from E(B-V) to A_V
_RV = 3.1


class DustMap(object):
    """Wraps the dustmaps package for A_V queries along lines of sight.

    Bayestar is 3D (distance-dependent); SFD and Planck are 2D (integrated
    to infinity).  dustmaps must be installed and the requested map data
    downloaded before first use; see https://dustmaps.readthedocs.io/.
    """

    default_map = "bayestar2019"

    def __init__(self, map_name=None):
        self.map_name = map_name or self.default_map
        if self.map_name not in _SUPPORTED_MAPS:
            raise ValueError(
                "Unknown dust map {!r}. Supported: {}".format(
                    self.map_name, list(_SUPPORTED_MAPS)
                )
            )
        self._dustmap = None

    @property
    def is_3d(self):
        return self.map_name.startswith("bayestar")

    @property
    def dustmap(self):
        if self._dustmap is None:
            module_name, cls_name = _SUPPORTED_MAPS[self.map_name]
            try:
                import importlib
                mod = importlib.import_module(module_name)
            except ImportError:
                raise ImportError(
                    "The dustmaps package is required. "
                    "Install it with: pip install isochrones[dustmaps]"
                )
            cls = getattr(mod, cls_name)
            if self.is_3d:
                # version kwarg selects Bayestar year (2015/2017/2019)
                year = int(self.map_name.replace("bayestar", "") or "2019")
                self._dustmap = cls(version="bayestar{}".format(year))
            else:
                self._dustmap = cls()
            getLogger().info("Loaded {} dust map".format(self.map_name))
        return self._dustmap

    def get_AV(self, ra, dec, distance=None, frame="icrs"):
        """A_V toward (ra, dec) in magnitudes; optionally at a specific distance in pc.

        For 3D maps (Bayestar) distance gives the integrated A_V to that distance.
        For 2D maps (SFD, Planck) distance is ignored with a warning.
        """
        from astropy.coordinates import SkyCoord
        import astropy.units as u

        coords = SkyCoord(ra, dec, unit="deg", frame=frame)

        if self.is_3d:
            if distance is not None:
                coords3d = SkyCoord(
                    ra, dec, distance=distance * u.pc, unit=("deg", "deg"), frame=frame
                )
                ebv = self.dustmap(coords3d)
            else:
                # Integrate to infinity; query at max distance in map (~63 kpc)
                coords3d = SkyCoord(
                    ra, dec, distance=63e3 * u.pc, unit=("deg", "deg"), frame=frame
                )
                ebv = self.dustmap(coords3d)
        else:
            if distance is not None:
                warnings.warn(
                    "{} is a 2D map; distance argument ignored.".format(self.map_name)
                )
            ebv = self.dustmap(coords)

        if ebv is None or np.isnan(ebv):
            getLogger().warning(
                "Dust map returned NaN for ({}, {}); returning 0.".format(ra, dec)
            )
            return 0.0

        return float(ebv) * _RV

    def get_AV_samples(self, ra, dec, n=100, max_distance=None, frame="icrs"):
        """AV vs. distance, sampled at n points; returns (distances_pc, AV_values).

        Only meaningful for 3D maps (Bayestar).
        """
        if not self.is_3d:
            raise ValueError(
                "{} is a 2D map; cannot sample AV vs. distance.".format(self.map_name)
            )
        if max_distance is None:
            max_distance = 20e3  # pc; well beyond most stellar targets

        distances = np.linspace(100, max_distance, n)
        AV_values = np.array([self.get_AV(ra, dec, distance=d, frame=frame) for d in distances])
        return distances, AV_values


def get_AV_from_dustmap(ra, dec, distance=None, map_name=None, frame="icrs"):
    """Convenience wrapper around DustMap.get_AV."""
    dm = DustMap(map_name=map_name)
    return dm.get_AV(ra, dec, distance=distance, frame=frame)

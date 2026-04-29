import os
import re

from ..bc import BolometricCorrectionGrid
from .models import MIST_VERSIONS


class MISTBolometricCorrectionGrid(BolometricCorrectionGrid):
    name = "mist"

    phot_bands = dict(
        UBVRIplus=[
            "Bessell_U",
            "Bessell_B",
            "Bessell_V",
            "Bessell_R",
            "Bessell_I",
            "2MASS_J",
            "2MASS_H",
            "2MASS_Ks",
            "Kepler_Kp",
            "Kepler_D51",
            "Hipparcos_Hp",
            "Tycho_B",
            "Tycho_V",
            # DR2Rev passbands kept for backward compat with v1.2 users
            "Gaia_G_DR2Rev",
            "Gaia_BP_DR2Rev",
            "Gaia_RP_DR2Rev",
            "Gaia_G_MAW",
            "Gaia_BP_MAWf",
            "Gaia_BP_MAWb",
            "Gaia_RP_MAW",
            # EDR3 passbands; available in MIST v2.5 BC tables
            "Gaia_G_EDR3",
            "Gaia_BP_EDR3",
            "Gaia_RP_EDR3",
            "TESS",
            "Gemini_NIRI_BrG",
            "WIYN_NESSI_NB832",
        ],
        WISE=["WISE_W1", "WISE_W2", "WISE_W3", "WISE_W4"],
        CFHT=["CFHT_u", "CFHT_g", "CFHT_r", "CFHT_i_new", "CFHT_i_old", "CFHT_z"],
        DECam=["DECam_u", "DECam_g", "DECam_r", "DECam_i", "DECam_z", "DECam_Y"],
        GALEX=["GALEX_FUV", "GALEX_NUV"],
        JWST=[
            "F070W",
            "F090W",
            "F115W",
            "F140M",
            "F150W2",
            "F150W",
            "F162M",
            "F164N",
            "F182M",
            "F187N",
            "F200W",
            "F210M",
            "F212N",
            "F250M",
            "F277W",
            "F300M",
            "F322W2",
            "F323N",
            "F335M",
            "F356W",
            "F360M",
            "F405N",
            "F410M",
            "F430M",
            "F444W",
            "F460M",
            "F466N",
            "F470N",
            "F480M",
        ],
        LSST=["LSST_u", "LSST_g", "LSST_r", "LSST_i", "LSST_z", "LSST_y"],
        PanSTARRS=["PS_g", "PS_r", "PS_i", "PS_z", "PS_y", "PS_w", "PS_open"],
        SkyMapper=["SkyMapper_u", "SkyMapper_v", "SkyMapper_g", "SkyMapper_r", "SkyMapper_i", "SkyMapper_z"],
        SPITZER=["IRAC_3.6", "IRAC_4.5", "IRAC_5.8", "IRAC_8.0"],
        UKIDSS=["UKIDSS_Z", "UKIDSS_Y", "UKIDSS_J", "UKIDSS_H", "UKIDSS_K"],
        SDSSugriz=["SDSS_u", "SDSS_g", "SDSS_r", "SDSS_i", "SDSS_z"],
        HST_ACSWF=["ACS_WFC_F435W", "ACS_WFC_F475W", "ACS_WFC_F502N", 
            "ACS_WFC_F550M", "ACS_WFC_F555W", "ACS_WFC_F606W", "ACS_WFC_F625W",
            "ACS_WFC_F658N", "ACS_WFC_F660N", "ACS_WFC_F775W", "ACS_WFC_F814W", 
            "ACS_WFC_F850LP", "ACS_WFC_F892N"],
        HST_ACSHR=["ACS_HRC_F220W", "ACS_HRC_F250W", "ACS_HRC_F330W", "ACS_HRC_F344N",
            "ACS_HRC_F435W", "ACS_HRC_F475W", "ACS_HRC_F502N", "ACS_HRC_F550M", "ACS_HRC_F555W", 
            "ACS_HRC_F606W", "ACS_HRC_F625W", "ACS_HRC_F658N", "ACS_HRC_F660N", "ACS_HRC_F775W", 
            "ACS_HRC_F814W", "ACS_HRC_F850LP", "ACS_HRC_F892N"],
        HST_WFC3=[
            "WFC3_UVIS_F200LP",
            "WFC3_UVIS_F218W",
            "WFC3_UVIS_F225W",
            "WFC3_UVIS_F275W",
            "WFC3_UVIS_F280N",
            "WFC3_UVIS_F300X",
            "WFC3_UVIS_F336W",
            "WFC3_UVIS_F343N",
            "WFC3_UVIS_F350LP",
            "WFC3_UVIS_F373N",
            "WFC3_UVIS_F390M",
            "WFC3_UVIS_F390W",
            "WFC3_UVIS_F395N",
            "WFC3_UVIS_F410M",
            "WFC3_UVIS_F438W",
            "WFC3_UVIS_F467M",
            "WFC3_UVIS_F469N",
            "WFC3_UVIS_F475W",
            "WFC3_UVIS_F475X",
            "WFC3_UVIS_F487N",
            "WFC3_UVIS_F502N",
            "WFC3_UVIS_F547M",
            "WFC3_UVIS_F555W",
            "WFC3_UVIS_F600LP",
            "WFC3_UVIS_F606W",
            "WFC3_UVIS_F621M",
            "WFC3_UVIS_F625W",
            "WFC3_UVIS_F631N",
            "WFC3_UVIS_F645N",
            "WFC3_UVIS_F656N",
            "WFC3_UVIS_F657N",
            "WFC3_UVIS_F658N",
            "WFC3_UVIS_F665N",
            "WFC3_UVIS_F673N",
            "WFC3_UVIS_F680N",
            "WFC3_UVIS_F689M",
            "WFC3_UVIS_F763M",
            "WFC3_UVIS_F775W",
            "WFC3_UVIS_F814W",
            "WFC3_UVIS_F845M",
            "WFC3_UVIS_F850LP",
            "WFC3_UVIS_F953N",
            "WFC3_IR_F098M",
            "WFC3_IR_F105W",
            "WFC3_IR_F110W",
            "WFC3_IR_F125W",
            "WFC3vIR_F126N",
            "WFC3_IR_F127M",
            "WFC3_IR_F128N",
            "WFC3_IR_F130N",
            "WFC3_IR_F132N",
            "WFC3_IR_F139M",
            "WFC3_IR_F140W",
            "WFC3_IR_F153M",
            "WFC3_IR_F160W",
            "WFC3_IR_F164N",
            "WFC3_IR_F167N"
        ],
        HST_WFPC2=[
            "WFPC2_F218W",
            "WFPC2_F255W",
            "WFPC2_F300W",
            "WFPC2_F336W",
            "WFPC2_F439W",
            "WFPC2_F450W",
            "WFPC2_F555W",
            "WFPC2_F606W",
            "WFPC2_F622W",
            "WFPC2_F675W",
            "WFPC2_F791W",
            "WFPC2_F814W",
            "WFPC2_F850LP",
        ],
        # Roman Space Telescope WFI filters (available in MIST v2.5 BC tables)
        Roman=[
            "Roman_F062",
            "Roman_F087",
            "Roman_F106",
            "Roman_F129",
            "Roman_F146",
            "Roman_F158",
            "Roman_F184",
            "Roman_F213",
            "Roman_Grism",
            "Roman_Prism",
        ],
        # Euclid VIS + NISP photometric bands (available in MIST v2.5 BC tables)
        Euclid=[
            "Euclid_VIS",
            "Euclid_Y",
            "Euclid_J",
            "Euclid_H",
        ],
        # HSC (Subaru Hyper Suprime-Cam)
        HSC=["HSC_g", "HSC_r", "HSC_i", "HSC_z", "HSC_y", "HSC_nb816", "HSC_nb921"],
        # S-PLUS
        SPLUS=[
            "SPLUS_uJAVA", "SPLUS_F378", "SPLUS_F395", "SPLUS_F410", "SPLUS_F430",
            "SPLUS_g", "SPLUS_F515", "SPLUS_r", "SPLUS_F660", "SPLUS_i",
            "SPLUS_F861", "SPLUS_z",
        ],
        # VISTA (ESO VIRCAM)
        VISTA=["VISTA_Z", "VISTA_Y", "VISTA_J", "VISTA_H", "VISTA_Ks"],
        # NIRISS (JWST Near Infrared Imager and Slitless Spectrograph)
        NIRISS=[
            "NIRISS_F090W", "NIRISS_F115W", "NIRISS_F140M", "NIRISS_F150W",
            "NIRISS_F158M", "NIRISS_F200W", "NIRISS_F277W", "NIRISS_F356W",
            "NIRISS_F380M", "NIRISS_F430M", "NIRISS_F444W", "NIRISS_F480M",
        ],
    )

    default_bands = ("J", "H", "K", "G", "BP", "RP", "W1", "W2", "W3", "TESS", "Kepler")

    def __init__(self, bands=None, version="1.2", afe=None):
        if version >= "2.5" and afe is None:
            raise ValueError("MIST v2.5 bolometric corrections require an explicit afe value.")
        self.version = version
        self.afe = afe
        super().__init__(bands=bands)

    @property
    def datadir(self):
        from ..config import ISOCHRONES
        # v2.5 BC tables are incompatible with v1.2; keep separate directories.
        if self.version >= "2.5":
            return os.path.join(ISOCHRONES, "BC", "mist_v2")
        return os.path.join(ISOCHRONES, "BC", self.name)

    def get_tarball_url(self, phot):
        cfg = MIST_VERSIONS[self.version]
        return cfg["bc_url"].format(phot=phot)

    def parse_table(self, filename):
        if self.version >= "2.5":
            import pandas as pd
            # v2.5 header: lgTef logg Fe_H a_Fe Av Rv <band> ...
            with open(filename) as fin:
                for line in fin:
                    if line.startswith("# lgTef"):
                        names = line[1:].split()
                        break
            df = pd.read_csv(filename, names=names, sep=r"\s+", comment="#")
            df = df.rename(columns={"lgTef": "Teff", "Fe_H": "[Fe/H]", "a_Fe": "afe"})
            df["Teff"] = 10 ** df["Teff"]
            df = df.set_index(["Teff", "logg", "[Fe/H]", "afe", "Av", "Rv"])
            return df
        return super().parse_table(filename)

    def get_df(self, *args, **kwargs):
        if self.version >= "2.5":
            import glob
            import pandas as pd
            afe = self.afe
            df_all = pd.DataFrame()
            for phot in self.phot_systems:
                hdf_filename = self.get_hdf_filename(phot=phot)
                if not os.path.exists(hdf_filename):
                    filenames = glob.glob(os.path.join(self.datadir, "*.{}".format(phot)))
                    if not filenames:
                        self.extract_tarball(phot=phot)
                        filenames = glob.glob(os.path.join(self.datadir, "*.{}".format(phot)))
                    df = pd.concat([self.parse_table(f) for f in filenames]).sort_index()
                    df.to_hdf(path_or_buf=hdf_filename, key="df")
                df = pd.read_hdf(hdf_filename)
                df_all = pd.concat([df_all, df], axis=1)
            df_all = df_all.rename(columns={v: k for k, v in self.band_map.items()})
            for col in list(df_all.columns):
                if col not in self.bands:
                    del df_all[col]
            return df_all.xs(3.1, level="Rv").xs(afe, level="afe")
        df = super().get_df(*args, **kwargs)
        return df.xs(3.1, level="Rv")

    @classmethod
    def get_band(cls, b, **kwargs):
        """Defines what a "shortcut" band name refers to.  Returns phot_system, band

        Gaia shortcut resolution is version-aware: v1.2 gives DR2Rev passbands,
        v2.5+ gives EDR3 passbands (revised photometric system).
        """
        phot = None
        version = kwargs.get("version", "1.2")
        spitzer_aliases = {
            "IRAC_3.6": "IRAC_36",
            "IRAC_4.5": "IRAC_45",
            "IRAC_5.8": "IRAC_58",
            "IRAC_8.0": "IRAC_80",
        }

        # Default to SDSS for these
        if b in ["u", "g", "r", "i", "z"]:
            phot = "SDSSugriz"
            band = "SDSS_{}".format(b)
        elif b in ["U", "B", "V", "R", "I"]:
            phot = "UBVRIplus"
            band = "Bessell_{}".format(b)
        elif b in ["J", "H", "Ks"]:
            phot = "UBVRIplus"
            band = "2MASS_{}".format(b)
        elif b == "K":
            phot = "UBVRIplus"
            band = "2MASS_Ks"
        elif b in ["kep", "Kepler", "Kp"]:
            phot = "UBVRIplus"
            band = "Kepler_Kp"
        elif b == "TESS":
            phot = "UBVRIplus"
            band = "TESS"
        elif b in ["W1", "W2", "W3", "W4"]:
            phot = "WISE"
            band = "WISE_{}".format(b)
        elif b in ("G", "BP", "RP"):
            phot = "UBVRIplus"
            # EDR3 passbands for v2.5+; DR2Rev for v1.x
            if version >= "2.0":
                band = "Gaia_{}_EDR3".format(b)
            else:
                band = "Gaia_{}_DR2Rev".format(b)
        elif b == "Bp":
            phot = "UBVRIplus"
            band = "Gaia_BP_EDR3" if version >= "2.0" else "Gaia_BP_DR2Rev"
        elif b == "Rp":
            phot = "UBVRIplus"
            band = "Gaia_RP_EDR3" if version >= "2.0" else "Gaia_RP_DR2Rev"
        else:
            m = re.match("([a-zA-Z]+)_([a-zA-Z0-9_]+)", b)
            if m:
                if m.group(1) in cls.phot_bands.keys():
                    phot = m.group(1)
                    if phot == "PanSTARRS":
                        band = "PS_{}".format(m.group(2))
                    else:
                        band = m.group(0)
                elif m.group(1) in ["UK", "UKIRT"]:
                    phot = "UKIDSS"
                    band = "UKIDSS_{}".format(m.group(2))

        if phot is None:
            for system, bands in cls.phot_bands.items():
                if b in bands:
                    phot = system
                    band = spitzer_aliases.get(b, b)
                    break
            if phot is None:
                raise ValueError("MIST grids cannot resolve band {}!".format(b))
        return phot, band

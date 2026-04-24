def default_max_eep(mass):
    """For MIST v1.2
    """
    if mass < 0.6:
        return 454
    elif mass == 0.6:
        return 605
    elif mass == 0.65:
        return 808
    elif mass < 6.0:
        return 1710
    else:
        return 808


def max_eep(mass, feh):
    """For MIST v1.2
    """
    eep = None
    if feh == -4.0:
        if mass < 0.6:
            eep = 454
        elif mass <= 0.94:
            eep = 631
        elif mass < 3.8:
            eep = 808
        elif mass <= 4.4:
            eep = 1409
        elif mass >= 18:
            eep = 631
    elif feh == -3.5:
        if mass == 0.65:
            eep = 631
        elif 0.65 < mass < 1.78:
            eep = 808
        elif mass == 1.78:
            eep = 1409
        elif 1.78 < mass <= 3.4:
            eep = 808
        elif mass >= 19:
            eep = 707
    elif feh == -3.0:
        if 0.7 <= mass <= 2.48:
            eep = 808
        elif 2.5 <= mass <= 4.4:
            eep = 1409
    elif feh == -2.5:
        if 0.7 <= mass <= 2.32:
            eep = 808
        elif 2.32 < mass <= 5.8:
            eep = 1409
    elif feh == 0.5:
        if 0.7 <= mass <= 0.75:
            eep = 808

    if eep is None:
        return default_max_eep(mass)
    else:
        return eep


def max_eep_v25(mass, feh):
    """For MIST v2.5

    WD cooling extends the EEP sequence past the WDCS entry point (1710).
    Stars that produce WDs (roughly 0.5-8 Msun) may have EEPs beyond 1710
    depending on how far along the cooling sequence the grid runs.

    For now returns the same ceilings as v1.2; update once v2.5 data files
    are inspected to confirm the actual per-star EEP limits.
    """
    return max_eep(mass, feh)

"""
Shared configuration for comparison scripts.
Edit only this file when base directories or network rules change.
"""

from dataclasses import dataclass


@dataclass
class CompareConfig:
    # Default base paths
    test_base: str = "/lfs/h2/emc/stmp/dagmar.merkova/CRON/v129/com/obsproc/v1.2.9"
    baseline_base: str = "/lfs/h2/emc/stmp/dagmar.merkova/CRON/v127/com/obsproc/v1.3.0"

    # Optional alternate paths you may want to switch to later
    # test_base: str = "/lfs/h1/ops/para/com/obsproc/v1.3"
    # baseline_base: str = "/lfs/h1/ops/prod/com/obsproc/v1.2"

    default_hh: str = "00"
    default_tm: str = "00"


CONFIG = CompareConfig()


# Rules per network
# has_atmos:
#   True  -> path looks like base/netw.YYYYMMDD/HH/atmos
#   False -> path looks like base/netw.YYYYMMDD
#
# prepbufr_has_tm:
#   True  -> filename ...prepbufr.tmTM
#   False -> filename ...prepbufr
#
# force_hh:
#   if not None, overrides HH
NETWORK_RULES = {
    "gdas": {
        "has_atmos": True,
        "prepbufr_has_tm": False,
        "force_hh": "00",
        "note": "GDAS uses /HH/atmos and prepbufr without tm suffix.",
    },
    "gfs": {
        "has_atmos": True,
        "prepbufr_has_tm": False,
        "force_hh": "00",
        "note": "GFS uses /HH/atmos and prepbufr without tm suffix.",
    },
    "cdas": {
        "has_atmos": False,
        "prepbufr_has_tm": False,
        "force_hh": None,
        "note": "CDAS may require manual PTMP adjustment if testing local files.",
    },
    "rap_p": {
        "has_atmos": False,
        "prepbufr_has_tm": True,
        "force_hh": None,
        "note": "RAP prepbufr usually uses tm suffix.",
    },
}


DEFAULT_RULES = {
    "has_atmos": False,
    "prepbufr_has_tm": True,
    "force_hh": None,
    "note": "Default network rule.",
}

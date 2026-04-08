"""
Shared configuration for comparison scripts.
Edit only this file when base directories or network rules change.
"""

from dataclasses import dataclass


@dataclass
class CompareConfig:
    # Default base paths
    #test_base: str = "/lfs/h2/emc/stmp/ashley.stanfield/CRON/kshtobash/com/obsproc/v1.3.0"
    #test_base: str = "/lfs/h2/emc/stmp/dagmar.merkova/CRON/v128ksh/com/obsproc/v1.3.0"
    test_base: str = "/lfs/h2/emc/stmp/iliana.genkova/CRON/REL/com/obsproc/v5.0"
    #test_base: str = "/lfs/h2/emc/stmp/dagmar.merkova/CRON/v127/com/obsproc/v1.3.0"
    #test_base: str = "/lfs/h2/emc/stmp/dagmar.merkova/CRON/v129/com/obsproc/v5.0"
    #test_base: str = "/lfs/h2/emc/stmp/dagmar.merkova/CRON/v127.nap/com/obsproc/v1.3.0"
    #baseline_base: str = "/lfs/h2/emc/stmp/dagmar.merkova/CRON/v127/com/obsproc/v1.3.0"

    # Optional alternate path
    # test_base: str = "/lfs/h1/ops/para/com/obsproc/v1.3"
    #baseline_base: str = "/lfs/h2/emc/stmp/dagmar.merkova/CRON/v127/com/obsproc/v1.3.0"
    baseline_base: str = "/lfs/h1/ops/prod/com/obsproc/v1.2"

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
        "force_hh": None,
        "note": "GDAS uses /HH/atmos and prepbufr without tm suffix.",
    },
    "gfs": {
        "has_atmos": True,
        "prepbufr_has_tm": False,
        "force_hh": None,
        "note": "GFS uses /HH/atmos and prepbufr without tm suffix.",
    },
    "cdas": {
        "has_atmos": False,
        "prepbufr_has_tm": True,
        "force_hh": None,
        "test_base": "/lfs/h2/emc/ptmp/dagmar.merkova/CRON/v129/com/obsproc/v5.0",
        "note": "CDAS may require manual PTMP adjustment if testing local files.",
    },
    "rap": {
        "has_atmos": False,
        "prepbufr_has_tm": True,
        "force_hh": None,
        "note": "RAP prepbufr uses tm suffix.",
    },
    "rap_e": {
        "has_atmos": False,
        "prepbufr_has_tm": True,
        "force_hh": None,
        "note": "RAP prepbufr uses tm suffix.",
    },
    "rap_p": {
        "has_atmos": False,
        "prepbufr_has_tm": True,
        "force_hh": None,
        "note": "RAP prepbufr uses tm suffix.",
    },
    "nam": {
        "has_atmos": False,
        "prepbufr_has_tm": True,
        "force_hh": None,
        "note": "NAM prepbufr uses tm suffix.",
    },
}


DEFAULT_RULES = {
    "has_atmos": False,
    "prepbufr_has_tm": True,
    "force_hh": None,
    "note": "Default network rule.",
}

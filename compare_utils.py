"""
Shared utility functions for directory / prepbufr comparison scripts.
"""

import os
from datetime import datetime
from compare_config import CONFIG, NETWORK_RULES, DEFAULT_RULES


def today_yyyymmdd():
    return datetime.today().strftime("%Y%m%d")


def get_network_rules(netw):
    return NETWORK_RULES.get(netw, DEFAULT_RULES)


def resolve_hh(netw, hh):
    rules = get_network_rules(netw)
    if rules.get("force_hh") is not None:
        return rules["force_hh"]
    return hh if hh is not None else CONFIG.default_hh


def resolve_tm(tm):
    return tm if tm is not None else CONFIG.default_tm


def build_cycle_dir(base, netw, date, hh=None):
    """
    Build cycle directory for a network/date/hh using network rules.
    """
    rules = get_network_rules(netw)
    hh = resolve_hh(netw, hh)

    if rules.get("has_atmos", False):
        return f"{base}/{netw}.{date}/{hh}/atmos"
    return f"{base}/{netw}.{date}"


def build_prepbufr_path(base, netw, date, hh=None, tm=None):
    """
    Build full prepbufr file path using network rules.
    """
    rules = get_network_rules(netw)
    hh = resolve_hh(netw, hh)
    tm = resolve_tm(tm)
    cycle_dir = build_cycle_dir(base, netw, date, hh)

    if rules.get("prepbufr_has_tm", True):
        return f"{cycle_dir}/{netw}.t{hh}z.prepbufr.tm{tm}"
    return f"{cycle_dir}/{netw}.t{hh}z.prepbufr"


def get_compare_targets(mode, netw, date1, date2=None):
    """
    Decide which bases/dates go on left/right side.

    mode='exp'
        left  = CONFIG.test_base/date1
        right = CONFIG.baseline_base/date2 or date1

    mode='date'
        left  = CONFIG.test_base/date1
        right = CONFIG.test_base/date2
    """
    rules = NETWORK_RULES.get(netw, DEFAULT_RULES)

    test_base = rules.get("test_base", CONFIG.test_base)
    baseline_base = rules.get("baseline_base", CONFIG.baseline_base)
    
    if mode == "exp":
        left_base = CONFIG.test_base
        right_base = CONFIG.baseline_base
        right_date = date2 if date2 else date1
    elif mode == "date":
        if not date2:
            raise ValueError("mode='date' requires --date2")
        left_base = CONFIG.test_base
        right_base = CONFIG.test_base
        right_date = date2
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return left_base, right_base, date1, right_date


def format_mode_label(mode):
    return "exp" if mode == "exp" else "date"


def safe_exists(path):
    return os.path.exists(path)


def get_file_time(file_path):
    if os.path.exists(file_path):
        mod_time = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
    return "File not found"

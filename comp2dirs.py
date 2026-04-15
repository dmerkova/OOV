#!/usr/bin/env python3
"""
Description:
Compare file inventory between two directory trees.

Supports two modes:
1) exp  = test_base vs baseline_base
2) date = test_base(date1) vs test_base(date2)

Compares file presence and file sizes for:
- bufr_d
- listing
- nr
- prepbufr
- twin-like files
- unblok (only cdas has them) 

Output:
  compare_dir_<netw>_<date1>_vs_<date2>_<HH or all>_<mode>.csv

Usage examples:
  python comp2dirs.py <netw>
  python comp2dirs.py <netw> --date1 20260313 --hh 00
  python comp2dirs.py <netw> --date1 20260313 --mode exp --hh 00
  python comp2dirs.py <netw> --date1 20260312 --date2 20260313 --mode date --hh 00
"""

import os
import sys
import argparse
import pandas as pd
from tabulate import tabulate

from compare_utils import (
    today_yyyymmdd,
    get_compare_targets,
    build_cycle_dir,
    resolve_hh,
    resolve_tm,
    format_mode_label,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Compare two obsproc directory trees.")
    parser.add_argument("network", help="Network name, e.g. gdas, gfs, cdas, rap_p")
    parser.add_argument("--date1", default=today_yyyymmdd(), help="Left date YYYYMMDD (default: today)")
    parser.add_argument("--date2", default=None, help="Right date YYYYMMDD")
    parser.add_argument("--hh", default=None, help="Cycle HH (if omitted, compare all files unless forced by network rule)")
    parser.add_argument("--tm", default=None, help="Time marker (tm00, tm01, tm02, ...)  - if omitted, compare all files unless forced by network rule)")
    parser.add_argument(
        "--mode",
        choices=["exp", "date"],
        default="exp",
        help="exp=test vs baseline, date=same base different days"
    )
    return parser.parse_args()


def get_files_and_sizes(directory, netw, hh_filter=None, tm_filter=None):
    """
    Recursively list all files with sizes.
    If hh_filter is given, keep only files matching netw.tHHz* OR upa_*.
    """
    if not os.path.exists(directory):
        print(f"Warning: Directory does not exist: {directory}")
        return {}

    file_dict = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if hh_filter:
                if not (
                    file.startswith(f"{netw}.t{hh_filter}z")
                    or file.startswith("upa_")
                ):
                    continue

            if tm_filter:
                if f".tm{tm_filter}." not in file:
                    continue

            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, directory)
            file_dict[relative_path] = os.path.getsize(full_path)

    return file_dict

def count_files(directory, netw, HH_filter=None, tm_filter=None):
    """Count occurrences of .listing, .nr, .bufr_d, prepbufr, twin, unblock, and total files."""

    if not os.path.exists(directory):
        return {"listing": 0, "nr": 0, "bufr_d": 0, "prepbufr": 0, "twin": 0, "total": 0}

    file_counts = {
        "listing": 0,
        "nr": 0,
        "bufr_d": 0,
        "prepbufr": 0,
        "twin": 0,
        "unblok": 0,
        "total": 0
    }

    files = os.listdir(directory)

    for f in files:

        # Apply HH filter if requested
        if HH_filter:
            if not (f.startswith(f"{netw}.t{HH_filter}z") or f.startswith("upa_")):
                continue

        if tm_filter:
            if f".tm{tm_filter}." not in f:
                continue

        file_counts["total"] += 1

        if f.endswith(".listing"):
            file_counts["listing"] += 1
        elif f.endswith(".nr"):
            file_counts["nr"] += 1
        elif ".bufr_d" in f:
            file_counts["bufr_d"] += 1
        elif "prepbufr" in f:
            file_counts["prepbufr"] += 1
        elif f.startswith("upa_"):
            file_counts["twin"] += 1
        elif f.endswith("unblok"):
            file_counts["unblok"] += 1

    return file_counts


def compare_directories(left_dir, right_dir, netw, hh_filter=None, tm_filter=None):
    """
    Compare file names and sizes between two directories.
    """
    if not os.path.exists(left_dir):
        print(f"Error: left directory does not exist: {left_dir}")
        sys.exit(1)

    if not os.path.exists(right_dir):
        print(f"Error: right directory does not exist: {right_dir}")
        sys.exit(1)

    left_files = get_files_and_sizes(left_dir, netw, hh_filter, tm_filter)
    right_files = get_files_and_sizes(right_dir, netw, hh_filter, tm_filter)
    
# Add debug prints at key points
    table_data = []
    all_files = left_files.keys() | right_files.keys()

    for file in all_files:
        size1 = left_files.get(file, "N/A")
        size2 = right_files.get(file, "N/A")

        if size1 == "N/A":
            status = "Only in right"
            size_diff = "N/A"
            rel_size_diff = "N/A"
        elif size2 == "N/A":
            status = "Only in left"
            size_diff = "N/A"
            rel_size_diff = "N/A"
        elif size1 == size2:
            status = "Identical"
            size_diff = 0
            rel_size_diff = "0.00%"
        else:
            status = "Size differs"
            size_diff = abs(size1 - size2)
            rel_size_diff = f"{(size_diff / size1) * 100:.2f}%" if size1 != 0 else "100%"

        table_data.append([file, size1, size2, size_diff, rel_size_diff, status])

    columns = [
        "File",
        "Size in left (bytes)",
        "Size in right (bytes)",
        "Size Difference (bytes)",
        "Relative Size Difference (%)",
        "Status",
    ]

    if not table_data:
        print("No matching files found for requested selection.")
        return pd.DataFrame(columns=columns)

    table_data.sort(key=lambda x: x[0])

    df = pd.DataFrame(table_data, columns=columns)

    print("\nDetailed file comparison:")
    print(tabulate(
        table_data,
        headers=columns,
        tablefmt="pretty",
        colalign=("left", "right", "right", "right", "right", "left")
    ))

    return df


def main():
    args = parse_args()

    netw = args.network
    date1 = args.date1
    date2 = args.date2
    mode = args.mode
    hh = resolve_hh(netw, args.hh)
    tm = resolve_tm(args.tm)

    left_base, right_base, left_date, right_date = get_compare_targets(mode, netw, date1, date2)

    # If user omitted HH and network does not force it, compare all files.
    # For gdas/gfs: HH is in directory path (/HH/atmos/), NOT in filename
    # For others: HH is in filename (nam.t00z*, rap.t00z*), so need filename filter
    if args.hh is not None:
        # User explicitly specified HH
        hh_filter = hh if netw not in ["gdas", "gfs"] else None
    elif netw in ["gdas", "gfs"]:
        # HH already in directory structure, don't filter filenames
        hh_filter = None
    else:
        # Other networks: filter by filename
        hh_filter = hh if hh is not None else None

    # TM filter should only be applied when user explicitly provides --tm.
    # Default TM is for naming/metadata, not for filtering directory comparisons.
    if args.tm is not None:
        tm_filter = tm if netw not in ["gdas", "gfs"] else None
    else:
        tm_filter = None


    left_dir = build_cycle_dir(left_base, netw, left_date, hh)
    right_dir = build_cycle_dir(right_base, netw, right_date, hh)

    # gdas/gfs keep HH in directory path, so hh_filter is intentionally None.
    # Use cycle HH for reporting/output naming in that case.
    display_hh = hh if netw in ["gdas", "gfs"] else (hh_filter if hh_filter else "ALL")
    hh_part = str(display_hh).lower() if display_hh != "ALL" else "all"
    tm_part = f"_tm{tm_filter}" if tm_filter else ""
    mode_label = format_mode_label(mode)
    output_csv = f"compare_dir_{netw}_{left_date}_vs_{right_date}_{hh_part}{tm_part}_{mode_label}.csv"

    print("\nComparing directories:")
    print(f"left_dir : {left_dir}")
    print(f"right_dir: {right_dir}")
    print(f"mode     : {mode_label}")
    print(f"network  : {netw}")
    print(f"date1    : {left_date}")
    print(f"date2    : {right_date}")
    print(f"hh       : {display_hh}")
    print(f"tm       : {tm_filter if tm_filter else 'ALL'}")


    df_compare = compare_directories(left_dir, right_dir, netw, hh_filter,tm_filter)

    left_counts = count_files(left_dir, netw, hh_filter, tm_filter)
    right_counts = count_files(right_dir, netw, hh_filter, tm_filter)

    print("\nFile Type Counts per Directory:")
    counts_rows = [
        ["Listing Files", left_counts["listing"], right_counts["listing"]],
        ["NR Files", left_counts["nr"], right_counts["nr"]],
        ["BUFR_D Files", left_counts["bufr_d"], right_counts["bufr_d"]],
        ["Prepbufr Files", left_counts["prepbufr"], right_counts["prepbufr"]],
        ["Twin Files", left_counts["twin"], right_counts["twin"]],
        ["Unblok Files", left_counts["unblok"], right_counts["unblok"]],
        ["TOTAL Files", left_counts["total"], right_counts["total"]],
    ]
    print(tabulate(
        counts_rows,
        headers=["File Type", "Count in left", "Count in right"],
        tablefmt="pretty",
        colalign=("left", "right", "right")
    ))

    print("\nComparing directories:")
    print(f"left_dir : {left_dir}")
    print(f"right_dir: {right_dir}")
    print(f"mode     : {mode_label}")
    print(f"network  : {netw}")
    print(f"date1    : {left_date}")
    print(f"date2    : {right_date}")
    print(f"hh       : {display_hh}")

    df_compare.to_csv(output_csv, index=False)
    

    with open(output_csv, "a") as f:
        f.write("\n")
        f.write("Directory Info\n")
        f.write(f"left_dir,{left_dir}\n")
        f.write(f"right_dir,{right_dir}\n")
        f.write(f"mode,{mode_label}\n")
        f.write(f"network,{netw}\n")
        f.write(f"date1,{left_date}\n")
        f.write(f"date2,{right_date}\n")
        f.write(f"hh,{display_hh}\n")
        f.write("\n")

    df_counts = pd.DataFrame(
        counts_rows,
        columns=["File Type", "Count in left", "Count in right"]
    )
    df_counts.to_csv(output_csv, mode="a", index=False)

    print(f"\nSaved: {output_csv}")


if __name__ == "__main__":
    main()

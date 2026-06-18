#!/usr/bin/env python3
"""
Description:
Compare file inventory between two directory trees.

Supports two modes:
1) exp  = path2 vs path1
2) date = path2(date1) vs path2(date2)

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
    python comp2dirs.py <netw> --path1 /path/to/base1 --path2 /path/to/base2 --date1 20260313 --hh 00
"""

import os
import sys
import argparse
from datetime import datetime
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
    parser.add_argument("--path1", default=None, help="Override config path1 base directory")
    parser.add_argument("--path2", default=None, help="Override config path2 base directory")
    parser.add_argument("--hh", default=None, help="Cycle HH (if omitted, compare all files unless forced by network rule)")
    parser.add_argument("--tm", default=None, help="Time marker (tm00, tm01, tm02, ...)  - if omitted, compare all files unless forced by network rule)")
    parser.add_argument(
        "--mode",
        choices=["exp", "date"],
        default="exp",
        help="exp=path2 vs path1, date=same path2 different days"
    )
    return parser.parse_args()


def get_files_and_sizes(directory, netw, hh_filter=None, tm_filter=None):
    if not os.path.exists(directory):
        print(f"Warning: Directory does not exist: {directory}")
        return {}

    file_dict = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if hh_filter:
                if not (file.startswith(f"{netw}.t{hh_filter}z") or file.startswith("upa_")):
                    continue
            if tm_filter and f".tm{tm_filter}." not in file:
                continue
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, directory)
            file_dict[relative_path] = {"size": os.path.getsize(full_path), "mtime": datetime.fromtimestamp(os.path.getmtime(full_path))}
    return file_dict


def count_files(directory, netw, HH_filter=None, tm_filter=None):
    if not os.path.exists(directory):
        return {"listing": 0, "nr": 0, "bufr_d": 0, "prepbufr": 0, "twin": 0, "total": 0}

    file_counts = {"listing": 0, "nr": 0, "bufr_d": 0, "prepbufr": 0, "twin": 0, "unblok": 0, "total": 0}
    files = []
    for root, _, filelist in os.walk(directory):
        files.extend(filelist)
    for f in files:
        if HH_filter and not (f.startswith(f"{netw}.t{HH_filter}z") or f.startswith("upa_")):
            continue
        if tm_filter and f".tm{tm_filter}." not in f:
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


def _format_mtime(value):
    return "N/A" if value == "N/A" else value.strftime("%Y-%m-%d %H:%M:%S")


def _time_diff_str(left_time, right_time):
    if left_time == "N/A" or right_time == "N/A":
        return "N/A"
    diff = right_time - left_time
    total_seconds = int(diff.total_seconds())
    sign = "" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"


def compare_directories(left_dir, right_dir, netw, hh_filter=None, tm_filter=None):
    if not os.path.exists(left_dir):
        print(f"Error: left directory does not exist: {left_dir}")
        sys.exit(1)
    if not os.path.exists(right_dir):
        print(f"Error: right directory does not exist: {right_dir}")
        sys.exit(1)

    left_files = get_files_and_sizes(left_dir, netw, hh_filter, tm_filter)
    right_files = get_files_and_sizes(right_dir, netw, hh_filter, tm_filter)

    table_data = []
    all_files = left_files.keys() | right_files.keys()
    for file in all_files:
        left = left_files.get(file, None)
        right = right_files.get(file, None)
        size1 = left["size"] if left else "N/A"
        size2 = right["size"] if right else "N/A"
        time1 = _format_mtime(left["mtime"]) if left else "N/A"
        time2 = _format_mtime(right["mtime"]) if right else "N/A"

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

        time_diff = _time_diff_str(left["mtime"] if left else "N/A", right["mtime"] if right else "N/A")
        if status.startswith("Only in "):
            status = f"\033[31m{status}\033[0m"

        table_data.append([file, size1, size2, size_diff, rel_size_diff, status, time1, time2, time_diff])

    columns = ["File", "Size L (bytes)", "Size R (bytes)", "Size Diff (bytes)", "Diff(%)", "Status", "Time L", "Time R", "Time Diff"]
    if not table_data:
        print("No matching files found for requested selection.")
        return pd.DataFrame(columns=columns)

    table_data.sort(key=lambda x: x[0])
    df = pd.DataFrame(table_data, columns=columns)

    print("\nDetailed file comparison:")
    print(tabulate(table_data, headers=columns, tablefmt="pretty", colalign=("left", "right", "right", "right", "right", "left", "left", "left", "left")))
    return df


def main():
    args = parse_args()
    if bool(args.path1) ^ bool(args.path2):
        print("Error: --path1 and --path2 must be provided together.")
        sys.exit(2)

    netw = args.network
    date1 = args.date1
    date2 = args.date2
    mode = args.mode
    hh = resolve_hh(netw, args.hh)
    tm = resolve_tm(args.tm)

    if args.path1 and args.path2:
        left_date = date1
        right_date = date2 if date2 else date1
        if mode == "exp":
            left_base = os.path.abspath(args.path2)
            right_base = os.path.abspath(args.path1)
        else:
            if not date2:
                print("Error: mode='date' requires --date2")
                sys.exit(2)
            left_base = os.path.abspath(args.path2)
            right_base = os.path.abspath(args.path2)
        left_dir = build_cycle_dir(left_base, netw, left_date, hh)
        right_dir = build_cycle_dir(right_base, netw, right_date, hh)
        mode_label = format_mode_label(mode)
    else:
        left_base, right_base, left_date, right_date = get_compare_targets(mode, netw, date1, date2)
        left_dir = build_cycle_dir(left_base, netw, left_date, hh)
        right_dir = build_cycle_dir(right_base, netw, right_date, hh)
        mode_label = format_mode_label(mode)

    if args.hh is not None:
        hh_filter = hh if netw not in ["gdas", "gfs"] else None
    elif netw in ["gdas", "gfs"]:
        hh_filter = None
    else:
        hh_filter = hh if hh is not None else None

    if args.tm is not None:
        tm_filter = tm if netw not in ["gdas", "gfs"] else None
    else:
        tm_filter = None

    display_hh = hh if netw in ["gdas", "gfs"] else (hh_filter if hh_filter else "ALL")
    tm_relevant = netw not in ["gdas", "gfs"]
    hh_part = str(display_hh).lower() if display_hh != "ALL" else "all"
    tm_part = f"_tm{tm_filter}" if tm_filter else ""
    output_csv = f"compare_dir_{netw}_{left_date}_vs_{right_date}_{hh_part}{tm_part}_{mode_label}.csv"

    print("\nComparing directories:")
    print(f"left_dir : {left_dir}")
    print(f"right_dir: {right_dir}")
    print(f"mode     : {mode_label}")
    print(f"network  : {netw}")
    print(f"date1    : {left_date}")
    print(f"date2    : {right_date}")
    print(f"hh       : {display_hh}")
    if tm_relevant:
        print(f"tm       : {tm_filter if tm_filter else 'ALL'}")

    df_compare = compare_directories(left_dir, right_dir, netw, hh_filter, tm_filter)
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
    print(tabulate(counts_rows, headers=["File Type", "Count in left", "Count in right"], tablefmt="pretty", colalign=("left", "right", "right")))

    df_compare.to_csv(output_csv, index=False)
    with open(output_csv, "a") as f:
        f.write("\nDirectory Info\n")
        f.write(f"left_dir,{left_dir}\n")
        f.write(f"right_dir,{right_dir}\n")
        f.write(f"mode,{mode_label}\n")
        f.write(f"network,{netw}\n")
        f.write(f"date1,{left_date}\n")
        f.write(f"date2,{right_date}\n")
        f.write(f"hh,{display_hh}\n")
        if tm_relevant:
            f.write(f"tm,{tm_filter if tm_filter else 'ALL'}\n")
        f.write("\n")
    pd.DataFrame(counts_rows, columns=["File Type", "Count in left", "Count in right"]).to_csv(output_csv, mode="a", index=False)
    print(f"\nSaved: {output_csv}")


if __name__ == "__main__":
    main()

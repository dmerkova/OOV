#!/usr/bin/env python3
"""
Description:
Compare prepbufr content using binv output.

Supports two modes:
1) exp  = test_base vs baseline_base
2) date = test_base(date1) vs test_base(date2)

It computes:
- raw binv outputs for left and right
- differences by common field NAME only
- prints ATTENTION if a NAME is missing on one side

Output:
  compare_prepb_<netw>_<date1>_vs_<date2>_<HH>_<TM>_<mode>.csv

Usage examples:
  python comp2prepbs.py gdas
  python comp2prepbs.py gdas --date1 20260313 --hh 00
  python comp2prepbs.py rap_p --date1 20260313 --hh 06 --tm 00
  python comp2prepbs.py gdas --date1 20260312 --date2 20260313 --mode date --hh 00
"""

import os
import sys
import argparse
import subprocess
import pandas as pd

from compare_utils import (
    today_yyyymmdd,
    get_compare_targets,
    build_prepbufr_path,
    resolve_hh,
    resolve_tm,
    get_file_time,
    format_mode_label,
)

BINV_CMD = "/apps/ops/prod/libs/intel/19.1.3.304/bufr/11.7.0/bin/binv"


def parse_args():
    parser = argparse.ArgumentParser(description="Compare prepbufr files using binv.")
    parser.add_argument("network", help="Network name, e.g. gdas, gfs, cdas, rap_p")
    parser.add_argument("--date1", default=today_yyyymmdd(), help="Left date YYYYMMDD (default: today)")
    parser.add_argument("--date2", default=None, help="Right date YYYYMMDD")
    parser.add_argument("--hh", default=None, help="Cycle HH")
    parser.add_argument("--tm", default=None, help="TM value, if relevant for network")
    parser.add_argument(
        "--mode",
        choices=["exp", "date"],
        default="exp",
        help="exp=test vs baseline, date=same base different days"
    )
    return parser.parse_args()


def run_binv(input_file, output_file):
    """Run binv and save stdout to output_file."""
    try:
        with open(output_file, "w") as fout:
            subprocess.run(
                [BINV_CMD, input_file],
                stdout=fout,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
    except subprocess.CalledProcessError as e:
        print(f"Error running binv on {input_file}")
        print(e.stderr)
        sys.exit(1)


def load_binv_output(filename):
    """Load binv output after skipping first 3 lines."""
    df = pd.read_csv(
        filename,
        skiprows=3,
        sep=r"\s+",
        names=["name", "type", "subset", "bytes", "val"],
        engine="python"
    )

    for col in ["type", "subset", "bytes", "val"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def save_section(df, filename, title=None, separator=","):
    """Append a titled DataFrame section to a CSV-like file."""
    with open(filename, "a") as f:
        if title:
            f.write(f"{title}\n")
        df.to_csv(f, index=False, sep=separator)
        f.write("\n")
def build_diff_table(left_df, right_df):
    """
    Simple old-style difference table.
    Assumes left/right rows are in the same order.
    Prints ATTENTION if names do not match.
    Returns table with left, right, and differences.
    """

    if len(left_df) != len(right_df):
        print("ATTENTION: LEFT and RIGHT have different number of rows")

    if not left_df["name"].equals(right_df["name"]):
        print("ATTENTION: NAME columns do not match row by row")
        print("\nLEFT names:")
        print(left_df["name"].to_string(index=False))
        print("\nRIGHT names:")
        print(right_df["name"].to_string(index=False))

    result = pd.DataFrame()
    result["name"] = left_df["name"]

    result["type_left"] = left_df["type"]
    result["type_right"] = right_df["type"]
    result["type_diff"] = left_df["type"] - right_df["type"]

    result["subset_left"] = left_df["subset"]
    result["subset_right"] = right_df["subset"]
    result["subset_diff"] = left_df["subset"] - right_df["subset"]

    result["bytes_left"] = left_df["bytes"]
    result["bytes_right"] = right_df["bytes"]
    result["bytes_diff"] = left_df["bytes"] - right_df["bytes"]

    result["val_left"] = left_df["val"]
    result["val_right"] = right_df["val"]
    result["val_diff"] = left_df["val"] - right_df["val"]

    result["bytes_relative_diff_pct"] = (
        (left_df["bytes"] - right_df["bytes"])
        / right_df["bytes"].replace(0, pd.NA) * 100.0
    )

    return result




def main():
    args = parse_args()

    netw = args.network
    date1 = args.date1
    date2 = args.date2
    mode = args.mode
    hh = resolve_hh(netw, args.hh)
    tm = resolve_tm(args.tm)

    left_base, right_base, left_date, right_date = get_compare_targets(mode, netw, date1, date2)

    left_file = build_prepbufr_path(left_base, netw, left_date, hh, tm)
    right_file = build_prepbufr_path(right_base, netw, right_date, hh, tm)

    mode_label = format_mode_label(mode)
    output_csv = f"compare_prepb_{netw}_{left_date}_vs_{right_date}_{hh}_{tm}_{mode_label}.csv"
    tmp_left = f"binv_left_{netw}_{left_date}_{hh}_{tm}.tmp"
    tmp_right = f"binv_right_{netw}_{right_date}_{hh}_{tm}.tmp"

    print("\nPrepbufr comparison setup:")
    print(f"left_file : {left_file}")
    print(f"right_file: {right_file}")
    print(f"mode      : {mode_label}")
    print(f"network   : {netw}")
    print(f"date1     : {left_date}")
    print(f"date2     : {right_date}")
    print(f"hh        : {hh}")
    print(f"tm        : {tm}")

    if not os.path.exists(left_file) or not os.path.exists(right_file):
        print("Error: One or both prepbufr files are missing.")
        if not os.path.exists(left_file):
            print(f"Missing left file : {left_file}")
        if not os.path.exists(right_file):
            print(f"Missing right file: {right_file}")
        sys.exit(1)

    print("\nPrepbufr file times:")
    print(f"{left_file}  -> {get_file_time(left_file)}")
    print(f"{right_file} -> {get_file_time(right_file)}")

    run_binv(left_file, tmp_left)
    run_binv(right_file, tmp_right)

    left_df = load_binv_output(tmp_left)
    right_df = load_binv_output(tmp_right)

    diff_df = build_diff_table(left_df, right_df)

    print("\n=== LEFT BINV OUTPUT ===")
    print(left_df.to_string(index=False))

    print("\n=== RIGHT BINV OUTPUT ===")
    print(right_df.to_string(index=False))

    print("\n=== DIFFERENCES ===")
    cols = ["name", "type_diff", "subset_diff", "bytes_diff", "val_diff", "bytes_rel_diff_%"]
    diff_df = diff_df.rename(columns={"bytes_relative_diff_pct": "bytes_rel_diff_%" })
    diff_df["bytes_rel_diff_%"] = diff_df["bytes_rel_diff_%"].round(2)
    diff_df["val_diff"] = diff_df["val_diff"].round(2)
    print(diff_df[cols].to_string(index=False))

    if os.path.exists(output_csv):
        os.remove(output_csv)

    with open(output_csv, "w") as f:
        f.write("Metadata\n")
        f.write(f"network,{netw}\n")
        f.write(f"mode,{mode_label}\n")
        f.write(f"date1,{left_date}\n")
        f.write(f"date2,{right_date}\n")
        f.write(f"hh,{hh}\n")
        f.write(f"tm,{tm}\n")
        f.write(f"left_file,{left_file}\n")
        f.write(f"right_file,{right_file}\n")
        f.write(f"left_file_time,{get_file_time(left_file)}\n")
        f.write(f"right_file_time,{get_file_time(right_file)}\n\n")

    save_section(left_df, output_csv, title="LEFT_BINV_OUTPUT")
    save_section(right_df, output_csv, title="RIGHT_BINV_OUTPUT")
    save_section(diff_df, output_csv, title="DIFFERENCES")

    print(f"\nSaved: {output_csv}")

    for tmp in [tmp_left, tmp_right]:
        if os.path.exists(tmp):
            os.remove(tmp)


if __name__ == "__main__":
    main()

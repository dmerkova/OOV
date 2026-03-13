#!/usr/bin/env python3
"""
Description:
Compare prepbufr content using binv output.

Supports two modes:
1) exp  = test_base vs baseline_base
2) date = test_base(date1) vs test_base(date2)

It computes:
- raw binv outputs for left and right
- numeric differences: left - right
- relative difference for bytes: ((left-right)/right)*100

Output:
  compare_prepb_<netw>_<date1>_vs_<date2>_<HH>_<TM>_<mode>.csv

Usage examples:
  python comp2prepb.py gdas
  python comp2prepb.py gdas --date1 20260313 --hh 00
  python comp2prepb.py rap_p --date1 20260313 --hh 06 --tm 00
  python comp2prepb.py gdas --date1 20260312 --date2 20260313 --mode date --hh 00
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
    """
    Run binv and save stdout to output_file.
    """
    try:
        with open(output_file, "w") as fout:
            subprocess.run([BINV_CMD, input_file], stdout=fout, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running binv on {input_file}")
        print(e.stderr)
        sys.exit(1)


def load_binv_output(filename):
    """
    Load binv output after skipping first 3 lines.
    """
    return pd.read_csv(
        filename,
        skiprows=3,
        sep=r"\s+",
        names=["name", "type", "subset", "bytes", "val"],
        engine="python"
    )


def save_section(df, filename, title=None, separator=","):
    """
    Append a titled DataFrame section to a CSV-like file.
    """
    with open(filename, "a") as f:
        if title:
            f.write(f"{title}\n")
        df.to_csv(f, index=False, sep=separator)
        f.write("\n")


def main():
    args = parse_args()

    netw = args.network
    date1 = args.date1
    date2 = args.date2
    mode = args.mode
    hh = resolve_hh(netw, args.hh)
    tm = resolve_tm(args.tm)

    left_base, right_base, left_date, right_date = get_compare_targets(mode, date1, date2)

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

    # Merge on identifying columns so rows align safely
    merged = pd.merge(
        left_df,
        right_df,
        on=["name", "type", "subset"],
        how="outer",
        suffixes=("_left", "_right")
    )

    # Convert numeric columns safely
    for col in ["bytes_left", "val_left", "bytes_right", "val_right"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    merged["bytes_diff"] = merged["bytes_left"] - merged["bytes_right"]
    merged["val_diff"] = merged["val_left"] - merged["val_right"]
    merged["bytes_relative_diff_pct"] = (
        (merged["bytes_left"] - merged["bytes_right"]) / merged["bytes_right"] * 100.0
    )

    diff_df = merged[[
        "name", "type", "subset",
        "bytes_left", "bytes_right", "bytes_diff", "bytes_relative_diff_pct",
        "val_left", "val_right", "val_diff"
    ]]

    # Clean old output if exists
    if os.path.exists(output_csv):
        os.remove(output_csv)

    # Save metadata
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

    # Remove temp files
    for tmp in [tmp_left, tmp_right]:
        if os.path.exists(tmp):
            os.remove(tmp)


if __name__ == "__main__":
    main()

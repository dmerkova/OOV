# OOV

Observation Output Verification tools to compare 2 different versions of obsproc runs.

## Update (2026-03-13)

### New files

- `compare_config.py`: setting base path and network-specific rules
- `compare_utils.py`: utilities shared by both scripts
- `comp2dirs.py`: compare 2 directories
- `comp2prepbs.py`: compare 2 PREPBUFR files

### Modes

- `mode=exp`: compare 2 different experiments
- `mode=date`: compare 2 different dates

### Usage

Load Python first:

```bash
module load python
```

Run examples:

```bash
python comp2dirs.py gfs --date1 20260313 --hh 00 --mode exp
python comp2dirs.py gdas --date1 20260312 --date2 20260313 --hh 00 --mode date
python comp2prepbs.py rap_p --date1 20260313 --hh 06 --tm 00 --mode exp
```

Note: special treatment for CDAS due to the fact that test is saved on `ptmp` instead of `stmp` due to time restrictions.

### Old versions kept as-is

- `com2dir.py`
- `cop2prepb.py`

## Setup

Install required packages (if not already installed):

- `tabulate`
- `matplotlib`
- `pandas`

```bash
pip install <package>
```

Load modules:

```bash
module load python
```

Supported networks:

- `gdas`
- `gfs`
- `cdas`
- `nam`
- `rap`
- `rap_e`
- `rap_p`
- `urma`
- `rtma`

Before running comparison scripts, set the paths for `BASE_COMROOT` and `BASE_SMTP`.

## Available comparison scripts

1. Compare two directories, print differences and relative differences on screen, and save data into a CSV file. Also lists differences and counts of `bufr_d`, `*nr`, and status files.

```bash
python comp2dir.sh <network> <yyyymmdd> [HH]
```

2. Compare two PREPBUFR files, calculate differences, and print directories and production time on screen and into a CSV file.

```bash
python comp2prepb.sh <network> <yyyymmdd> [HH]
```


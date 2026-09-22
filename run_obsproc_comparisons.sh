#!/usr/bin/env bash

module load python
set -euo pipefail

# Usage:
#   ./run_obsproc_comparisons.sh [HH] [YYYYMMDD]
#
# Examples:
#   ./run_obsproc_comparisons.sh
#   ./run_obsproc_comparisons.sh 06
#   ./run_obsproc_comparisons.sh 12 20260922

hh="${1:-00}"
run_date="${2:-$(date -u +%Y%m%d)}"
hour_flag="${HOUR_FLAG:---hh}"
mv compare_*.csv archive/.

if [[ ! "$hh" =~ ^(00|06|12|18)$ ]]; then
    echo "ERROR: hour must be 00, 06, 12, or 18." >&2
    exit 2
fi

if [[ ! "$run_date" =~ ^[0-9]{8}$ ]]; then
    echo "ERROR: date must have YYYYMMDD format." >&2
    exit 2
fi

cdas_date=$(date -u -d "${run_date} -1 day" +%Y%m%d)

module load python

echo "Running directory comparisons for cycle ${hh}Z"
for model in gfs gdas nam rap; do
    python comp2dirs.py --date1 "$run_date" "$hour_flag" "$hh" "$model"
done
python comp2dirs.py --date1 "$cdas_date" "$hour_flag" "$hh" cdas

echo "Running PREPBUFR comparisons for cycle ${hh}Z"
for model in gfs gdas nam rap; do
    python comp2prepbs.py --date1 "$run_date" "$hour_flag" "$hh" "$model"
done
python comp2prepbs.py --date1 "$cdas_date" "$hour_flag" "$hh" cdas

echo "All comparisons completed successfully."

tar -cvf comp.${run_date}.${hh}.tar compare_*.csv 

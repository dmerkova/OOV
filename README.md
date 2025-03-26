# OOV
Observation Output Verification

Tools to compare 2 different versions

Install required packages (if not already installed):

You will need the following packages: tabulate, matplotlib, and pandas.
pip install <package>

Supported eetworks: gdas, gfs, cdas, nam, rap, rap_e, rap_p, urma, rtma 

Before running comparison scripts, set the paths for: 
BASE_COMROOT
BASE_SMTP

Available Comparison Scripts

1. Compare Two Directories:
Lists differences and counts of bufr_d, *nr, and status files.

python comp2dir.sh <network> <yyyymmdd>

2. Compare Two PREPBUFR Files:

python comp2prepb.sh <network> <yyyymmdd>


# OOV
Observation Output Verification tools to compare 2 different versions of obsproc runs. 

Install required packages (if not already installed):

You will need the following packages: tabulate, matplotlib, and pandas.

`pip install <package>`

Load modules 

`module load python`


Supported networks: *gdas, gfs, cdas, nam, rap, rap_e, rap_p, urma, rtma*


Before running comparison scripts, set the paths for **BASE_COMROOT** and **BASE_SMTP**.



### Available Comparison Scripts

1. Compare Two Directories:
Lists differences and counts of bufr_d, *nr, and status files.

`python comp2dir.sh <network> <yyyymmdd>`

2. Compare Two PREPBUFR Files, calsulate differences and print directories and production time.

`python comp2prepb.sh <network> <yyyymmdd>`


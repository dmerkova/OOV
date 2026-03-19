# UPDATE 3/13/2026
NEW files:
 compare_config.py  # setting base path, network specific rules 
 compare_utils.py   # utils shared for both scripts
 comp2dirs.py       # comparing 2 directories 
 comp2prepbs.py     # comparing 2 prepbufr files

mode=exp  # comparing 2 different experiments
mode=date # comparing 2 different dates


USAGE: (need to load python module: module load python ) 
python comp2dirs.py gfs --date1 20260313 --hh 00 --mode exp
python comp2dirs.py gdas --date1 20260312 --date2 20260313 --hh 00 --mode date
python comp2prepbs.py rap_p --date1 20260313 --hh 06 --tm 00 --mode exp
# NOTE:  special treatment for CDAS due to fact that test is saved 
# on ptmp instead of stmp due time restrictions

# ############################ 
# keeping old versions as is 
# ############################ 
   com2dir.py
   cop2prepb.py 


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

1. Compare two directories, print differences and relative differences on the screen and saves data into cvs file.
Lists differences and counts of bufr_d, *nr, and status files on screen.

`python comp2dir.sh <network> <yyyymmdd> [HH]`

2. Compare two PREPBUFR Files, calculate differences and print directories and production time on screen and also into the *csv file.

`python comp2prepb.sh <network> <yyyymmdd> [HH]`  


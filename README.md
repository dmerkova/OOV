# OOV
Observation Output Verification

Tools to compare 2 different versions

USAGE: 

module load python

in case you do not have some packages installed, use pip command (you need tabulate, matplotlib, panda) 
pip install <package>

Networks: gdas, gfs, cdas, nam, rap, rap_e, rap_p, urma, rtma 

Before you run comparison script, set path 
BASE_COMROOT
BASE_SMTP

Compare 2 directories, list differences , count bufr_d, *nr, status files
python comp2dir.sh <network> <yyymmdd>

Compare 2 prepbufr files
python comp2prepb.sh <network> <yyymmdd>

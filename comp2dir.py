"""
Description: 
takes the binries and compares  bufr_d, listings, nr, prepbufer files and twin
OUTPUT FILE  --  compare_dir_<netw>_<date>_<HH>..csv --- for import to tables!
UPDATED: February 20, 2025 (DM)
USAGE:
module load python
python comp2dir.py <network> [yyyymmdd] [HH]
--- default values             today     00
if you do not use HH it will compare full directories
!!!!!!!!!! NEED TO CHECK DIRECTORIES and change it  inside of the script !!!!!!!!!!!!!!!!!!!!!!
BASE_COMROOT
BASE_STMP
"""

import os
import sys
import subprocess
import pandas as pd
from tabulate import tabulate
from datetime import datetime


#### !! NEED TO DEFINE common base paths ##############################
#BASE_STMP = "/lfs/h1/ops/para/com/obsproc/v1.2"
BASE_STMP = "/lfs/h2/emc/stmp/dagmar.merkova/CRON/R13/com/obsproc/v1.3"
BASE_COMROOT = "/lfs/h1/ops/prod/com/obsproc/v1.2"
#BASE_COMROOT = "/lfs/h2/emc/prod/com/obsproc/v1.3"
#######################################################################

# Ensure the script receives correct arguments
if len(sys.argv) < 2 or len(sys.argv) > 4:
    print("Usage: python compare_dirs.py <network> [yyyymmdd] [HH]")
    print("Default values for date is TODAY and HH=00")
    sys.exit(1)

today_date = datetime.today().strftime("%Y%m%d")

# Get arguments
netw = sys.argv[1]
datum = sys.argv[2] if len(sys.argv) >= 3 else today_date # Default is today date
HH = sys.argv[3] if len(sys.argv) == 4 else None  # Optional HH argument

# Construct output filenames dynamically based on provided arguments
HH_part = f"_{HH}" if HH else "_all"

output_log = f"compare_log_{netw}_{datum}{HH_part}.txt"
output_csv = f"compare_dir_{netw}_{datum}{HH_part}.csv"

# Set default HH for gdas/gfs if not provided
if netw in ['gdas', 'gfs'] and HH is None:
    HH = "00"


# Initialize paths with the common structure
mySTMP = f"{BASE_STMP}/{netw}.{datum}"
myCOMROOT = f"{BASE_COMROOT}/{netw}.{datum}"

# If HH is provided, modify directory structure
if HH:
    if netw in ['gdas', 'gfs']:  # Additional HH/atmos level for gdas/gfs
        mySTMP = f"{BASE_STMP}/{netw}.{datum}/{HH}/atmos"
        myCOMROOT = f"{BASE_COMROOT}/{netw}.{datum}/{HH}/atmos"
    else:  # Other networks just use HH as a filter
        mySTMP = f"{BASE_STMP}/{netw}.{datum}"
        myCOMROOT = f"{BASE_COMROOT}/{netw}.{datum}"

# Modify paths based on the network type
if netw == 'cdas':
    print('****  IF CDAS AND CHECKING MY TEST NEED TO UNCOMMENT FOLLOWING LINE *******')
    print('because the use of PTMP')
    #mySTMP = '/lfs/h2/emc/ptmp/dagmar.merkova/CRON/R13/com/obsproc/v1.3/'+netw+'.'+datum+'/'+HH+'/atmos'

print(f"Comparing directories:\nmySTMP: {mySTMP}\nmyCOMROOT: {myCOMROOT}\n")

# Function to retrieve file names and sizes from a directory, using HH as a filter
def get_files_and_sizes(directory, HH_filter=None):
    """List all files in the given directory and subdirectories with their sizes, filtering by HH."""
    if not os.path.exists(directory):
        print(f"Warning: Directory {directory} does not exist. Returning empty file list.")
        return {}

    file_dict = {}
    for root, _, files in os.walk(directory):
        for file in files:
            # Apply HH filter as a mask for 't??z.' files
            if HH_filter:
                if not (file.startswith(f"{netw}.t{HH_filter}z") and len(file) > len(f"{netw}.t{HH_filter}z")):
                    continue  # Skip files that do not match the expected netw.t??z pattern
            
            relative_path = os.path.relpath(os.path.join(root, file), directory)
            file_size = os.path.getsize(os.path.join(root, file))
            file_dict[relative_path] = file_size

    return file_dict  # Always return a dictionary

# Function to count occurrences of specific file types in a directory
def count_files(directory, netw, HH_filter=None):
    """Count occurrences of .listing, .nr, .bufr_d, and prepbufr files, applying HH filtering."""
    if not os.path.exists(directory):
        return {"listing": 0, "nr": 0, "bufr_d": 0, "prepbufr": 0, "twin": 0}
    file_counts = {"listing": 0, "nr": 0, "bufr_d": 0, "prepbufr": 0, "twin": 0}
    # Get all files in the directory
    files = [f for f in os.listdir(directory) if f.startswith(f"{netw}.t")]
    # Apply HH filter if provided
    if HH_filter:
        files = [f for f in files if f.startswith(f"{netw}.t{HH_filter}z")]
    # Use Bash to find files containing "status" and "twin" files

    # Count file types
    for f in files:
        if f.endswith(".listing"):
            file_counts["listing"] += 1
        elif f.endswith(".nr"):
            file_counts["nr"] += 1
        elif ".bufr_d" in f:
            file_counts["bufr_d"] += 1
        elif "prepbufr" in f:
            file_counts["prepbufr"] += 1
        elif f.startswith("upa_"):   # Check if file appears in the grep result
            file_counts["twin"] += 1
    return file_counts

# Function to compare two directories
def compare_directories(dir1, dir2, HH_filter=None):
    """Compare file names and sizes between two directories."""
    if not os.path.exists(dir1) or not os.path.exists(dir2):
        print(f"Error: One or both directories do not exist. Cannot proceed.")
        sys.exit(1)

    files_in_dir1 = get_files_and_sizes(dir1,HH_filter)
    files_in_dir2 = get_files_and_sizes(dir2,HH_filter)

    table_data = []
    for file in files_in_dir1.keys() | files_in_dir2.keys():
        size1 = files_in_dir1.get(file, 'N/A')
        size2 = files_in_dir2.get(file, 'N/A')

        if size1 == 'N/A':
            status = "Only in dir2"
            size_diff = 'N/A'
            rel_size_diff = 'N/A'
        elif size2 == 'N/A':
            status = "Only in dir1"
            size_diff = 'N/A'
            rel_size_diff = 'N/A'
        elif size1 == size2:
            status = "Identical"
            size_diff = 0
            rel_size_diff = "0.00%"
        else:
            status = "Size differs"
            size_diff = abs(size1 - size2)
            rel_size_diff = f"{(size_diff / size1) * 100:.2f}%" if size1 != 0 else "100%"

        table_data.append([file, size1, size2, size_diff, rel_size_diff, status])

    if not table_data:
        print(" No matching files found for the given HH. No comparison data to display.")
        return


    # Sort results alphabetically by filename
    table_data.sort(key=lambda x: x[0])

    # Print the comparison results
    df = pd.DataFrame(table_data, columns=["File", "Size in mySTMP (bytes)", "Size in myCOMROOT (bytes)", 
                                           "Size Difference (bytes)", "Relative Size Difference (%)", "Status"])
    df.to_csv(output_csv, index=False)
    
    print(tabulate(table_data, 
                        tablefmt="pretty", 
                        colalign=("left", "right", "right", "right", "right", "left")))


# Run the directory comparison
compare_directories(mySTMP, myCOMROOT,HH)

# Count file occurrences in each directory
stmp_counts = count_files(mySTMP,netw,HH)
comroot_counts = count_files(myCOMROOT,netw,HH)

# Print the count of specific files in each directory
print("\nFile Type Counts per Directory:")
print(tabulate([
    ["Listing Files", stmp_counts["listing"], comroot_counts["listing"]],
    ["NR Files", stmp_counts["nr"], comroot_counts["nr"]],
    ["BUFR_D Files", stmp_counts["bufr_d"], comroot_counts["bufr_d"]],
    ["Prepbufr Files", stmp_counts["prepbufr"], comroot_counts["prepbufr"]],
    ["Twin Files", stmp_counts["twin"], comroot_counts["twin"]],
], headers=["File Type", "Count in mySTMP", "Count in myCOMROOT"], tablefmt="pretty", colalign=("left", "right", "right")))

print(f"Comparing directories:\nmySTMP: {mySTMP}\nmyCOMROOT: {myCOMROOT}\n")

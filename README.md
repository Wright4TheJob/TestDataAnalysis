# TestDataAnalysis
A script for analyzing tensile and compression test data.

This python script reads a set of sequentially numbered files containing test data.

# Usage
The program is written for python 3 and tested in python 3.7.

The script contains several parameters that will require review before successful operation. Most importantly, the directory of the test files to be read and the filename will require modification. Files are expected to be numbered sequentially using integers with an equal number of leading zeros.

If the three files to analyze are located on the desktop and titled File-01.txt, File-02.txt, and File-03.txt, the base name is set to "File-", the suffix is set to ".txt", and the index_digits parameter set to 2. After providing the folder variable the path the desktop in your operating system, everything should execute properly.

To run the script, invoke the command
```
$ python3 TestDataAnalysis.py
```
from the repository directory. Results for peak load/stress and modulus will be printed to the terminal. For large quantities of files, these results should be directed into a text file using the command
```
$ python3 TestDataAnalysis.py > results.txt
```

# Input Files
Files are assumed to be exported from the MTI software, but the script is configurable for your data structure. An example of the file expected to be read is shown below.
```
6/11/2018 11:47:32 AM   Width, Thick, Diam. Units Code
1.0000, 1.0000, 1.0000, 0,
199659.6719,
Load, Disp, Stress, Time, Temp, Axial, Transverse, Chans 1-20
 40.4636, 0.00000, 40.464, 0.01422,  0.00, 0.00000, 0.00000, -40.463593,
 40.9143, 0.00000, 40.914, 0.01424,  0.00, 0.00000, 0.00000, -40.914330,
 40.2910, 0.00000, 40.291, 0.01428,  0.00, 0.00000, 0.00000, -40.290955,
 41.1863, 0.00000, 41.186, 0.01433,  0.00, 0.00000, 0.00000, -41.186275,
 40.8369, 0.00000, 40.837, 0.01435,  0.00, 0.00000, 0.00000, -40.836891,
```
Header lines are ignored and delimiter type is easily modified for tab-separated or other file types.

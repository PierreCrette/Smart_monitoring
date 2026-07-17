# Smart_monitoring
Graph SMART disk values over time to identify rises prior failure.

Rationale: 
https://www.howtogeek.com/i-always-check-these-smart-values-before-trusting-an-old-hdd-with-my-data/#threads

Source code for parsing smartmontools/attrprint*.csv files: https://git.wut.ee/arti/smartmontoolstopsql/src/branch/master/attrprintimport.py


USAGE:

One must look at indicator trend. A sudden rise may predict a failure.

SMART 5 counts reallocated sectors.

SMART 187 counts reads that the error correction could not fix, and this is the one where zero tolerance is the right approach.

SMART 188 counts commands that took too long or got aborted entirely.

SMART 197, this one counts pending sectors, meaning spots on the platter the drive is struggling to read and has queued for reallocation.

SMART 198 same as 197 for some drives.



Requirements:

smartmontools must be installed and run daily or weekly (cron or other) to feed /var/lib/smartmontools/attrlog*.csv

Download smartgraph.py, chmod +x and run.

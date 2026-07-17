#!/usr/bin/env python3

def doc():
  print('SMART Monitoring over time')
  print('Copyright (C) 2026  Pierre Crette ')
  print('Rationale: https://www.howtogeek.com/i-always-check-these-smart-values-before-trusting-an-old-hdd-with-my-data/#threads')
  print('Parsing code for smartmontools/attrprint*.csv files: https://git.wut.ee/arti/smartmontoolstopsql/src/branch/master/attrprintimport.py')
  print('')
  print('Requirements:')
  print('smartmontools must be installed and run daily or weekly (cron or other) to feed /var/lib/smartmontools/attrlog*.csv')
  print('')
  print('This program is free software: you can redistribute it and/or modify')
  print('it under the terms of the GNU General Public License as published by')
  print('the Free Software Foundation, either version 3 of the License, or')
  print('(at your option) any later version.')
  print('')
  print('This program is distributed in the hope that it will be useful,')
  print('but WITHOUT ANY WARRANTY; without even the implied warranty of')
  print('MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the')
  print('GNU General Public License for more details.')
  print('')
  print('You should have received a copy of the GNU General Public License')
  print('along with this program.  If not, see <http://www.gnu.org/licenses/>.')
  print()
  print()
  print('USAGE:')
  print('One must look at indicator trend. A sudden rise may predict a failure.')
  print('SMART 5 counts reallocated sectors')
  print('SMART 187 counts reads that the error correction could not fix, and this is the one where zero tolerance is the right approach.')
  print('SMART 188 counts commands that took too long or got aborted entirely')
  print('SMART 197, this one counts pending sectors, meaning spots on the platter the drive is struggling to read and has queued for reallocation')
  print('SMART 198 same as 197 for some drives')
  print('________________________________________________________________________________________________________________________________________')
  print('')
  print('')

import os
import re
import sys
import glob
from datetime import datetime
from pytz import timezone, AmbiguousTimeError, NonExistentTimeError

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt


def parse_attrprint_file(filename, start_seek=0):
  global drive_name, ser0, ser1, ser2, ser3, ser4, ser5

  tz_dst = timezone("Europe/Paris")
  utc = timezone("UTC")
  # This is a date when smartmontools switched from UTC time to local time
  # That change was done in commit b75b99551368da1a8623cd76b3c67bdd3aaceddc
  smartmontools_update_date = datetime(2021, 9, 16, 18, 00, 00)
  dst = None  # Is daylight saving time in effect?
  prev_time = None

  fd = open(filename)
  file_size = fd.seek(0, os.SEEK_END)
  fd.seek(start_seek)

  # print(f'filesize({drive_name})={file_size}')

  while fd.tell() != file_size: #and len(ser0) < 10:
    line = fd.readline()
    line_parts = [p for p in line.strip().split(";") if p.strip()]
    
    plain_dt = datetime.strptime(line_parts.pop(0), "%Y-%m-%d %H:%M:%S")
    # Debian 10 to 11 upgrade added timezone and dst support to smartmontools timestamps
    if plain_dt > smartmontools_update_date:
        tz = tz_dst
    else:
        tz = utc
    try:
        dt = tz.localize(plain_dt, is_dst=None)

        # We are currently in normal time
        cur_dst = bool(dt.dst())
        if dst != cur_dst:
            dst = cur_dst
    except (AmbiguousTimeError, NonExistentTimeError):
        # We are in Ambiguous time where localtime cant be translated to UTC
        # Hack around it by tracking previous DST and time values
        dt = tz.localize(plain_dt, is_dst=dst)
        if prev_time and prev_time > dt:
            dt = tz.localize(plain_dt, is_dst=not dst)
    prev_time = dt
    cur_dst = bool(dt.dst())
    dtu = dt.astimezone(utc)
    #print(plain_dt, dt, dtu, dst, cur_dst, sep='; ')
    if dst is None:
        dst = cur_dst
    ser0.append(dtu)
    # ser0.append(plain_dt)

    while line_parts:
      id = int(line_parts.pop(0))
      norm = int(line_parts.pop(0))
      raw = int(line_parts.pop(0))
      # yield str(dtu), id, norm, raw, fd.tell()
      if   id == 5:   ser1.append(norm)
      elif id == 187: ser2.append(norm)
      elif id == 188: ser3.append(norm)
      elif id == 197: ser4.append(norm)
      elif id == 198: ser5.append(norm)
      # smartmeasures.append([str(dtu), id, norm, raw, fd.tell()])

    # Pretty progress indicator
    if fd.tell() % 1000 == 0:
        print(f"{int(((fd.tell() - start_seek) / (file_size - start_seek))*100):>5}%", end='\r')
  print()
  # df = pd.DataFrame(
  #   {
  #     "dtu": ser0,
  #     "id5": ser1,
  #     "id187": ser2,
  #     "id188": ser3,
  #     "id197": ser4,
  #     "id198": ser5,
  #   })
  print()  
  return


def percentage(ser, gap=0):
  global ser0

  if len(ser) < 1:
    serout = [0 for v in ser0]
  else:
    maxval = max(ser)
    serout = [v / maxval + gap for v in ser] 
  return serout


def summarize(ser, label):
  if len(ser) < 1:
    print(f'{label} is not populated by this disk')
  else:
    print(f'{label} range from {min(ser)} to {max(ser)} with an average of {sum(ser) / len(ser)}')


def import_attrprint_file(filename):
  global drive_name, ser0, ser1, ser2, ser3, ser4, ser5

  drive_name = drive_name_re.search(filename).group(1)
  # print(drive_name)
  
  ser0 = []
  ser1 = []
  ser2 = []
  ser3 = []
  ser4 = []
  ser5 = []

  parse_attrprint_file(filename)

  print()
  print(f'{drive_name} analysed from {min(ser0)} to {max(ser0)}')
  summarize(ser1, 'id5')
  summarize(ser2, 'id187')
  summarize(ser3, 'id188')
  summarize(ser4, 'id197')
  summarize(ser5, 'id198')
  print()

  # Note that even in the OO-style, we use `.pyplot.figure` to create the Figure.
  fig, ax = plt.subplots(figsize=(5, 2.7), layout='constrained')
  ax.plot(ser0, percentage(ser1, 0), label='id5')
  ax.plot(ser0, percentage(ser2, 1), label='id187')
  ax.plot(ser0, percentage(ser3, 2), label='id188')
  ax.plot(ser0, percentage(ser4, 3), label='id197')
  ax.plot(ser0, percentage(ser5, 4), label='id198')
  # ax.set_xlabel('Time')  # Add an x-label to the Axes.
  # ax.set_ylabel('SMART')  # Add a y-label to the Axes.
  ax.set_title(drive_name)  # Add a title to the Axes.
  ax.legend()  # Add a legend.
  plt.show()




if __name__ == '__main__':
  doc()
  for file in glob.glob('/var/lib/smartmontools/attrlog*.csv'):
    # print(f'Parsing {file}')
    drive_name_re = re.compile(r'attrlog\.(.*).ata.csv')
    import_attrprint_file(file)

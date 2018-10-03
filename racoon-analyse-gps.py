#!/usr/bin/env python3
"""Analyse Racoon GPS logger data

    USAGE:
        python racoon-analyse-gps.py [<INFILE.(gpx|txt)>]

    Example Output generated from example.gpx (converted from example.kml) can
    be viewed in *example.gpx.html* and *example.gpx.html.png*

    HOW TO USE
    ==========
    1. Run the command above
       OR
       When run without arguments a file chooser dialog will appear.
    2. A browser with an OpenStreetMap should appear.

    The program shows the gps positions in two different colors:
    1. The red stronger markers are the positions
       recorded in the daytime (10:00 - 18:00)
    2. The blue more transparent markers are positions
       recorded in the night time (18:00 - 10:00)
    The markers are a little transparent so that spots with more recorded GPS
    postions appear in stronger colors.

    INSTALLATION
    ============
    - Easiest is to use `pipenv` to install all needed dependencies.
      Simple run `pipenv install` in the same directory where `Pipfile` and
      `Pipfile.lock` reside.

      NOTE!!!: If you use pipenv the run command changes to:

        `pipenv run python racoon-analyse-gps.py <INFILE.(gpx|txt)>`
         ~~~~~~~~~~

    - If you are not using Pipenv you have to make sure all dependencies are
      installed by yourself.

      These are probably installed with pip with:
      `pip install --user pandas gpxpy mplleaflet matplotlib`

      WINDOWS
      -------
      - Install python3 https://www.python.org/downloads/
      - Make sure to tick "Add python to PATH" during the installation
      - Open Terminal and run `pip3.exe install pandas gpxpy mplleaflet matplotlib`

    CHANGELOG
    =========
    0.2.0 Added simple 'GUI' to choose the gps file
    0.1.1 Added txt gps importer
    0.1.0 Inital with gpx file importer

    COPYRIGHT
    =========
    2018 Florian Voit <florian.voit@gmail.com>
    This is free and unencumbered software released into the public domain.
"""
__version__ = '0.1.1'
import datetime
import os
import sys
import tempfile
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import gpxpy  # Apache-2.0
import matplotlib.pyplot as plt  # BSD like matplotlib License
import mplleaflet  # BSD 3-Clause License
import pandas as pd  # BSD License
from dateutil.parser import parse  # Apache-2.0


def convert_comment_to_datetime(comment):
    tokens = comment.split()
    date = tokens[2]
    time = tokens[4]
    dt = parse(date + ' ' + time, dayfirst=True)
    return dt


def gpx_importer(in_filename):
    gpx_file = open(in_filename, 'r')
    gpx = gpxpy.parse(gpx_file)
    df = pd.DataFrame(columns=['lon', 'lat', 'alt', 'time'])
    for point in gpx.waypoints:
        df = df.append(
            {
                'lon': point.longitude,
                'lat': point.latitude,
                'alt': point.elevation,
                'time': convert_comment_to_datetime(
                 point.comment)
            }, ignore_index=True)
    return df


def txt_importer(in_filename):
    df = pd.read_csv(in_filename, header=None,
                     names=['date', 'time', 'lon', 'lat'],
                     usecols=[2, 4, 5, 6],
                     na_values=[0.0])
    df = df.dropna()
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
    df['time'] = pd.to_timedelta(df['time'])
    df['time'] = df['date'] + df['time']
    return df


def main(in_filename):
    if in_filename.endswith('.gpx'):
        df = gpx_importer(in_filename)
    elif in_filename.endswith('.txt'):
        df = txt_importer(in_filename)
    else:
        print('Error: No importer for filetype "{}"'.format(
            os.path.splitext(in_filename)))
        sys.exit(2)
    df['time'] = pd.DatetimeIndex(df['time'])
    df.set_index(keys='time', inplace=True)
    df_night = df.between_time(datetime.time(hour=18), datetime.time(hour=10))
    plt.plot(df_night['lon'], df_night['lat'], 'bs', alpha=0.1)
    df_day = df.between_time(datetime.time(hour=10), datetime.time(hour=18))
    plt.plot(df_day['lon'], df_day['lat'], 'rs', alpha=0.5)

    mapfile = os.path.join(
        tempfile.gettempdir(), Path(in_filename).name + '.html')
    mplleaflet.show(path=mapfile)


if __name__ == '__main__':
    print('racoon-analyse-gps {}'.format(__version__))
    if len(sys.argv) < 2:
        Tk().withdraw()
        filename = askopenfilename(initialdir=os.path.expanduser('~'),
                                   title="Select GPS file",
                                   filetypes=(
                                       ("gps files", "*.gpx"),
                                       ("gps files", "*.txt")))
    else:
        filename = sys.argv[1]

    main(in_filename=filename)

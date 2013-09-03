#!/usr/local/bin/python
"""
A simple script for generating multiple JSON/JavaScript from comma-separated (or
otherwise delimited) values. A specified column from the input file must be
set.  Each record sharing the same field value are put in the same file, so
one file is produced per unique value for this specified column.

Python 2.7 or higher is recommended see :
"Floating Point Arithmetic issues and Limitations" at
http://docs.python.org/2/tutorial/floatingpoint.html

by Shawn Allen <shawn at stamen dot com>
modified by Alexandre Dube <adube at mapgears dot com> for lighter json
"""
import csv, sys, os
try:
    import json
except ImportError:
    import simplejson as json
from StringIO import StringIO

# These are shorthands for delimiters that might be a pain to type or escape.
delimiter_map = {'tab': '\t',
                 'sc':  ';',
                 'bar': '|'}

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def csv2json(csv_file, delimiter=',', quotechar='"', callback=None, variable=None, **csv_opts):
    if delimiter_map.has_key(delimiter):
        delimiter = delimiter_map.get(delimiter)
    reader = csv.DictReader(csv_file, delimiter=delimiter, quotechar=quotechar or None, **csv_opts)

    limitations = {}

    # manually cast to integer or float according values for a lighter json
    # csv.DictReader has no mean to return unquoted integer and float values,
    # that's why it's manually done here. None really efficient upon script
    # execution, but json is much lighter that way
    for row in reader:
        for field in row:
            if is_number(row[field]):
                if is_int(row[field]):
                    row[field] = int(row[field])
                else:
                    row[field] = float(row[field])

        year = row['y']
        disease = row['d']
        limitation = row['l']
        diseaseName = row['n']
        
        limitation = limitation.replace(str(year), '{{{YEAR}}}', 1)
        key = diseaseName + '___' + limitation + '___' + str(disease)

        if not key in limitations:
            limitations[key] = {}
            limitations[key]['l'] = limitation
            limitations[key]['d'] = disease
            limitations[key]['n'] = diseaseName
            limitations[key]['y'] = []

        if not year in limitations[key]['y']:
            limitations[key]['y'].append(year)

    # create clean rows, with sorted values (and sorted by disease name)
    rows = []
    for key in sorted(limitations.keys(), reverse=False):
        limitations[key]['y'] = sorted(limitations[key]['y'])
        rows.append(limitations[key])

    out = StringIO()
    if callback:
        out.write('%s(' % callback);
    elif variable:
        out.write('var %s = ' % variable)
    json.dump(rows, out, indent=None, separators=(',', ':'))
    if callback:
        out.write(');');
    elif variable:
        out.write(';')
    return out.getvalue()


if __name__ == '__main__':
    import sys
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-F', '--field-separator', dest='fs', default=',',
                      help='The CSV file field separator, default: %default')
    parser.add_option('-q', '--field-quote', dest='fq', default='"',
                      help='The CSV file field quote character, default: %default')
    parser.add_option('-i', '--indent', dest='indent', default=None,
                      help='The string with which to indent the output GeoJSON, '
                           'defaults to none.')
    parser.add_option('-p', '--callback', dest='callback', default=None,
                      help='The JSON-P callback function name.')
    parser.add_option('-v', '--variable', dest='var', default=None,
                      help='If provided, the output becomes a JavaScript statement'
                      ' which assigns the JSON structure to a variable of the same'
                      ' name.')

    options, args = parser.parse_args()

    close = False
    if len(args) > 0 and args[0] != '-':
        csv_file = open(args.pop(0), 'r')
        close = True
    else:
        csv_file = sys.stdin
    print csv2json(csv_file, options.fs, options.fq, options.callback, options.var)
    if close:
        csv_file.close()

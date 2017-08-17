#!/usr/bin/env python

import requests
import csv, sys, re
import codecs
from bs4 import BeautifulSoup

# Globals
row_counter = 1
trip_counter = 1
name_dict = {}
columns = [['Name', 'ISNI', 'Name variants', 'Web page', 'Identity 1 name', 'Identity 1 ISNI',
            'Identity 2 name', 'Identity 2 ISNI', 'Identity 3 name', 'Identity 3 ISNI', 'Notes']]

# Methods
def write_csv(filename, content):
    with open(filename, 'wb') as output:
        output.write(codecs.BOM_UTF8)
        writer = csv.writer(output, quoting=csv.QUOTE_ALL,quotechar='"')
        writer.writerows(content)
    print filename, 'has been created!'

def process_webpage(notes):
    regexp = re.compile(r'(www\.|http:\/\/|.\..{3})')
    if regexp.search(notes):
      return notes

def process_isni(isni, name):
    global name_dict
    uri = "http://isni.org/isni/" + isni.replace(' ','') + '.xml'
    isni_xml = requests.get(uri)
    isni_xml_soup = BeautifulSoup(isni_xml.text, 'html.parser')
    isniuri = isni_xml_soup.isniuri.text
    # Add name/isni to dictionary for use in second trip
    if isniuri:
        name_dict[name] = str(isniuri)
        return str(isniuri)

def check_for_isni(names_list):
    global name_dict
    if names_list[0] in name_dict:
        columns[row_counter][5] += name_dict[names_list[0]]
    if names_list[1] in name_dict:
        columns[row_counter][7] += name_dict[names_list[1]]
    if len(names_list) > 2:
        if names_list[2] in name_dict:
            columns[row_counter][9] += name_dict[names_list[2]]
    return columns

def process_names(name):
    name = name.replace(', and ',', ').replace(' and ',', ')
    names_list = name.split(', ')
    # Output can't handle more than three names
    if len(names_list) > 3:
        print "Found 'Name' column with more than three names!"
        print names_list
    # Handle multiple names up to three
    if len(names_list) > 1 and len(names_list) < 4:
        # If this is the first trip, add names to columns
        if trip_counter == 1:
            columns[row_counter][4] += names_list[0]
            columns[row_counter][6] += names_list[1]
            if len(names_list) > 2:
                columns[row_counter][8] += names_list[2]
            return columns
        # If this is the second trip, check for ISNI
        else:
            check_for_isni(names_list)

def process_row(name, isni=None, notes=None):
    global columns, row_counter
    # If this is the first trip, add all the required rows
    if trip_counter == 1:
        new_row = ['' for _ in columns[0]]
        columns += [new_row]
        columns[row_counter][0] += name
        process_names(name) # Process names
        if isni:
            final_isni = process_isni(isni, name) # Process ISNI
            columns[row_counter][1] += final_isni
        if notes:
            columns[row_counter][10] += notes # Process notes
        webpage = process_webpage(notes) # Process webpage
        if webpage:
            columns[row_counter][3] += webpage
    # If this is the second trip, just process names
    else:
        process_names(name)
    row_counter += 1 # Move on to next row
    return columns

def read_rows(reader):
    for row in enumerate(reader):
        name = row[1][0].strip()
        isni = row[1][1].strip()
        notes = row[1][2].strip()
        if name:
            output = process_row(name, isni, notes)
    return output

def process_file(input_file):
    with open(input_file, 'rb') as name_csv:
        reader = csv.reader(name_csv)
        next(reader, None) # skip headers
        output = read_rows(reader)
    return output

def main():
    global trip_counter, row_counter
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        print "Cleaning up {}...".format(input_file)
        output = process_file(input_file)
        # Set trip/row counters and process file again
        trip_counter += 1
        row_counter = 1
        output = process_file(input_file)
        # Write output to CSV
        write_csv("output.csv", output)
    else:
        print "Please provide a CSV file."
        exit()

if __name__ == '__main__':
    main()

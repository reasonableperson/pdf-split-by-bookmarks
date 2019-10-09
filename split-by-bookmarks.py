#!/usr/bin/python3

from functools import reduce
import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys

# Parse arguments.
parser = argparse.ArgumentParser(description=
    'Split a large PDF into many small PDFs based on its bookmarks.')
parser.add_argument('input', metavar='FILE', type=str, help=
    'PDF file to use as input.')
parser.add_argument('-o, --output', default='out', dest='output', help=
    'Output directory.')
parser.add_argument('--skip', action='store_true', help=
    "Exclude 'duplicate' bookmarks; that is, bookmarks which start and end on" +
    "the same page, and therefore would simply produce a copy of a single page" +
    "which would be reproduced as page 1 of the file for the next bookmark.")
parser.add_argument('--force', action='store_true', help=
    'Delete anything that is already in the output directory.')
parser.add_argument('--json', action='store_true', help=
    'Dump a JSON file containing the bookmark metadata.')
args = parser.parse_args()

# Extract the metadata from the input file.
print('Extracting PDF metadata.', args.input)
task = subprocess.run(['pdftk', args.input, 'dump_data_utf8'], capture_output=True)
metadata = task.stdout.decode('utf-8').split('\n')

# Compile some regular expressions which will be repeatedly used when parsing
# the metadata file.
class Token:
    begin = re.compile(r'BookmarkBegin')
    level = re.compile(r'BookmarkLevel: (\d+)')
    page  = re.compile(r'BookmarkPageNumber: (\d+)')
    text  = re.compile(r'BookmarkTitle: (.*)')
    end   = re.compile(r'BookmarkEnd')

# Do some nasty procedural parsing, which is necessary to handle the edge case
# of bookmarks with newlines included in the text. pdftk doesn't delimit these.
bookmarks = []  # accumulate all the bookmarks here
bookmark = None # the current partially-parsed bookmark
still_parsing_title = False # used for handling multi-line fields
for line in metadata:
    if Token.begin.match(line): # create a new bookmark
        if bookmark is not None: bookmarks.append(bookmark)
        bookmark = {}
    elif Token.level.match(line): # store the BookmarkLevel
        still_parsing_title = False
        bookmark['level'] = Token.level.match(line).group(1)
    elif Token.page.match(line): # store the BookmarkPageNumber
        bookmark['page'] = Token.page.match(line).group(1)
    elif Token.text.match(line): # store the first line of the BookmarkTitle
        still_parsing_title = True
        bookmark['text'] = Token.text.match(line).group(1)
    else: # we have a line that doesn't begin with a bookmark token
        if still_parsing_title:
            # this bit should have been flipped when BookmarkLevel was hit,
            # which should always happen after a BookmarkTitle; since it is
            # still true, assume this is part of the title
            bookmark['text'] += line
        else:
            # otherwise, it's just some junk token 
            if bookmark is not None:
                bookmarks.append(bookmark)
                bookmark = None

# This shouldn't happen, but if the very last line of the metadata file is part
# of a final bookmark (it should be followed by other junk), then we need to
# keep track of that final bookmark.
if bookmark is not None: bookmarks.append(bookmark)

# If page 1 isn't bookmarked, add a bookmark so that the pages preceding the first
# bookmark can still be extracted.
if bookmarks[0]['page'] != 1:
    bookmarks.insert(0, {'level': '0', 'page': '1', 'text': '(start)'})

# Function for generating an appropriate filename for a bookmark, given the
# index number (starting at zero) and the bookmark text.
friendly_chars = re.compile(r'[ \w]')
max_length = 100
def make_filename(index, page, text):
    # remove unfriendly characters unsuitable for filenames
    text = "".join(filter(friendly_chars.match, text))
    # truncate bookmark text if necessary
    if len(text) > max_length:
        text = text[:max_length - 3] + '...'
    # add index and page numbers as a prefix
    return f'{i+1:03} - p {page} - {text}.pdf'

# Generate the filenames and end page for each bookmark selection.
for i, b in enumerate(bookmarks):
    b['file'] = make_filename(i, b['page'], b['text'])
    b['end_page'] = bookmarks[i+1]['page'] if i + 1 < len(bookmarks) else 'end'

# Optionally filter out 'duplicates'.
if args.skip:
    def skip_duplicates(acc, next_b):
        if acc is None: return [next_b]
        last_b = acc.pop()
        if last_b['page'] == next_b['page']: acc.append(next_b)
        else: acc.extend([last_b, next_b])
        return acc
    bookmarks = reduce(skip_duplicates, bookmarks, None)

# Set up output directory.
try: os.mkdir('out')
except OSError:
    if args.force:
        print("There's already an out/ directory; DELETING it.")
        shutil.rmtree('out')
        os.mkdir('out')
    else:
        print("There's already an out/ directory; exiting.")
        sys.exit(1)

def make_pdftk_args(bm, input_file, output_dir):
    page_range = f'{bm["page"]}-{bm["end_page"]}'
    output_file = os.path.join(args.output, f'{bm["file"]}')
    return ['pdftk', input_file, 'cat', page_range, 'output', output_file]

for i, b in enumerate(bookmarks):
    subprocess.run(make_pdftk_args(b, args.input, args.output), stdout=subprocess.PIPE)
    print(f'[{i+1}/{len(bookmarks)}] {b["file"]}')

#!/usr/bin/python3

from functools import reduce
import json
import os
import re
import shutil
import subprocess
import sys

# Read in the metadata file produced by PDFtk.
with open('metadata', 'r') as fd:
    metadata = fd.readlines()

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
def generate_filename(index, page, text):
    # remove unfriendly characters unsuitable for filenames
    text = "".join(filter(friendly_chars.match, text))
    # truncate bookmark text if necessary
    if len(text) > max_length:
        text = text[:max_length - 3] + '...'
    # add index and page numbers as a prefix
    return f'{i+1:03} - p {page} - {text}.pdf'

# Generate the filenames and end page for each bookmark selection.
for i, bm in enumerate(bookmarks):
    bm['file'] = generate_filename(i, bm['page'], bm['text'])
    bm['end_page'] = bookmarks[i+1]['page'] if i + 1 < len(bookmarks) else 'end'

# Optionally filter out 'duplicates'; that is, bookmarks which start and end on
# the same page, and therefore would simply produce a copy of a single page
# which would be reproduced as page 1 of the file for the next bookmark.
if '--no-dups' in sys.argv:
    def skip_duplicates(acc, next_bm):
        if acc is None: return [next_bm]
        last_bm = acc.pop()
        if last_bm['page'] == next_bm['page']: acc.append(next_bm)
        else: acc.extend([last_bm, next_bm])
        return acc
    bookmarks = reduce(skip_duplicates, bookmarks, None)

# Set up output directory.
try: os.mkdir('out')
except OSError:
    if '--force' in sys.argv:
        print("There's already an out/ directory; DELETING it.")
        shutil.rmtree('out')
        os.mkdir('out')
    else:
        print("There's already an out/ directory; exiting.")
        print("Add --force to just delete it.")

# Print pdftk commands.
input_file = 'in.pdf'
for i, bm in enumerate(bookmarks):
    page_range = f'{bm["page"]}-{bm["end_page"]}'
    output_file = f'out/{bm["file"]}'
    print(f'[{i+1}/{len(bookmarks)}] out/{bm["file"]}')
    subprocess.run(['pdftk', input_file, 'cat', page_range, 'output', output_file])

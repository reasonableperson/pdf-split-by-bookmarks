# pdf-split-by-bookmarks

This repository contains a script for performing the task of 'un-combining'
PDFs: it will convert a very large PDF with many bookmarks into a directory
full of smaller PDFs, one per bookmark.

## Usage

Install `pdftk` (`apt install pdftk` or `brew install pdftk`), then:

```
$ ./split-by-bookmarks.py -h
usage: split-by-bookmarks.py [-h] [-o OUTPUT] [--skip] [--force] [--json] FILE

Split a large PDF into many small PDFs based on its bookmarks.

positional arguments:
  FILE        PDF file to use as input.

optional arguments:
  -h, --help  show this help message and exit
  -o OUTPUT   Output directory.
  --skip      Exclude 'duplicate' bookmarks; that is, bookmarks which start
              and end on the same page, and therefore would simply produce a
              copy of a single pagewhich would be reproduced as page 1 of the
              file for the next bookmark.
  --force     Delete anything that is already in the output directory.
  --json      Dump a JSON file containing the bookmark metadata and exit.
```

## Description

I needed a tool to split PDFs by bookmarks, satisfying the following
requirements:

* The new files must be named and ordered according to the bookmarks, so the
  filename must have an ordinal prefix in order to preserve the order of the
  bookmarks.

* Bookmark titles can contain characters that aren't allowed in filenames, so
  they must be sanitised.

* It should be possible to provide your own template for the new filenames, but
  if this occurs then the edge case of non-unique filenames must be handled.

* The list of bookmarks should be flattened, and if there are multiple
  bookmarks on the same page, the user should be able to choose between
  creating multiple copies of that page, or skipping duplicates and only
  creating a file for the last bookmark on each page.

* The list of bookmarks should also be avaiable in a structured format like
  JSON. The list should include the full text of each bookmark, as well as the
  filename of the newly-created document, and the corresponding page numbers
  in the original document.

I considered using these tools to do it:

* [Sejda][1] has a 'split by bookmarks' feature, but the files it produces are
  named according to page number only, and there doesn't seem to be any way to
  get at the bookmark titles.

  [1]: https://github.com/torakiki/sejda

* [PyPDF2][2] seems unnecessarily low-level, although arguably it would be a
  good starting point if we want to implement other features later, like
  programmatically modifying bookmarks or hyperlinks.

  [2]: https://medium.com/@menglishu09/get-bookmarks-from-pdf-using-pypdf2-4166ae8eb6f6

* [cpdf][3] has the required functionality, but it is not free software, and
  the functionality [does not support very long bookmark text][4].

  [3]: https://github.com/coherentgraphics/cpdf-binaries
  [4]: https://github.com/coherentgraphics/cpdf-binaries/issues/43

* `pdftk` provides access to the required metadata, but the output format is
  horrible and it doesn't have a command-line interface to the required
  functionality. Nonetheless, it is a dependency that can be easily installed
  without licensing issues. Thus, it forms the basis of this script.

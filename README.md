# pdf-split-by-bookmarks

This repository contains a script for performing the task of 'un-combining'
PDFs: it will convert a very large PDF with many bookmarks into a directory
full of smaller bookmarks, one per bookmark.

* The new files must be named and ordered according to the bookmarks, so the
  filename must have an ordinal prefix in order to preserve the order of the
  bookmarks.

* Bookmark titles can contain characters that aren't allowed in filenames, so
  they must be sanitised.

* It should be possible to provide your own template for the new filenames, but
  if this occurs then the edge case of non-unique filenames must be handled.

* The list of bookmarks should be flattened, and if there are multiple
  bookmarks on the same page, the user should be able to choose between
  creating multiple copies of that page.

It is surprisingly difficult to meet all these requirements!

* [Sejda][1] has a 'split by bookmarks' feature, but the files it produces are
  named according to page number only, and there doesn't seem to be any way to
  get at the bookmark titles.

  [1]: https://github.com/torakiki/sejda

* [PyPDF2][2] seems unnecessarily low-level, although arguably it would be a
  good starting point if we want to implement other features later, like
  programmatically modifying bookmarks or hyperlinks.

  [2]: https://medium.com/@menglishu09/get-bookmarks-from-pdf-using-pypdf2-4166ae8eb6f6

* [cpdf][3] has the required functionality, but it is not free software, and
  the functionality breaks with very long bookmark text.

* [pdftk][4] provides access to the required metadata, but the output format is
  horrible and it doesn't have a command-line interface to the required
  functionality. Nonetheless, it is a dependency that can be easily installed
  with `apt-get` without creating licensing issues. This repository contains
  a shell wrapper around it.

# pyimagesort
Sort image & video files, remove duplicates

### Features

* Capable of processing jpg, png, mov, avi, mp4, wmv, m4v.
* Sorts files into destination directory, creating sub-directories for year and month.
* Files are named using the oldest timestamp found on the file, for example `/sorted/2017/08/20170801-193758-0.jpg`
* Uses filesystem and all available EXIF timestamps to attempt to determine the original (oldest) timestamp
* Duplicates images are detected using by fuzzy match, with rotation. 
* Images that have been resized, rotated, very slightly changed, or are almost identical, will be considered matching.
* Always keeps the highest resolution version of matching images.
* If 2 images match and have the same resolution, will keep the HDR version.
* Will preserve the EXIF from the oldest image, even if the oldest was lower resolution and not kept.
* Only deletes duplicate images if an exact match was detected. Otherwise images are backed up to a trash directory.
* Ignores directories starting with . (dot).
* Removes directories emptied as a result of sorting.

### Requirements

* Python 3.6+
* [exiftool](https://www.sno.phy.queensu.ca/~phil/exiftool/)

### Installation

* Unzip to any directory
* `pip install -r requirements.txt`

### Usage

`sort.py destination source [source ...]`

* `destination` is the full path to a directory to sort images into
* `source` are full path to directories containing images to process

### Notes

* A directory called `.imagesort/` will be created in your `destination` directory, use to store the image database.
* Duplicates images will be backed up to `.imagesort/trash`.  You may delete these as desired.
* Upon startup, the database is checked for consistency with the `destination` directory, and created or fixed based on images this directory contains.
* You should try to avoid modifying the `destination` directory once images have been sorted.
* You can adjust the fuzzy match threshold by changing SIMILAR_IMAGE_HASH_DIST in ImageSorter.py.
  * Range 0-1024, default 3
  * 0 = Exact match
  * 3 is conservative, you may want to go as high as 5 or 6. The higher you go the more false matches you'll get and risk losing images you may want to keep.
  

### Known Bugs, TODOs

* Automatic rotation to proper orientation
* Video files do not use fuzzy match

### Author

[Paul Cowan](paul@monospacesoftware.com) ([Monospace Software LLC](https://monospacesoftware.com/))

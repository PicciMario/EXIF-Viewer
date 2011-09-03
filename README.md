# PicciMario EXIF analyzer v. 0.1

mario.piccinelli@gmail.com
  
This command line tool is a wrapper of the text-only utility [exiv2](http://www.exiv2.org/). Analyzes a JPG picture and creates a forensically sound PDF report with informations about the file (as told by the filesystem) and about the image itself via its EXIF/IPTC/XMP tags. 

Special features:

* If GPS data are found in the EXIF tags, the report will contain a map of the location and an approximate reverse geocoding of the coordinates into their location name. Everything thanks to OpenStreetMap.org.

* If thumbnails are embedded in the original file, these will be extracted, analyzed and included in the report.

Usage:

  ./exif2reporter.py -f inputfile 
  
Other options:

  -o reportname (default: report.pdf)

# Requires:

* Tested on Python 2.6 on Linux and Mac Os X.

* Python Imaging Library (PIL). For Mac Os download from [here](http://www.pythonware.com/products/pil/). For Linux you should do something like:
  
  sudo apt-get install python-imaging python-imaging-tk

* ReportLab Toolkit (open source version). You can download it [here](http://www.reportlab.com/software/opensource/rl-toolkit/download/).

* The command line utility exiv2 must be present on your computer. You can download and install it from [here](http://www.exiv2.org/).
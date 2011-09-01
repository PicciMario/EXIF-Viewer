#!/usr/bin/env python

"""
EXIF reporter 
(part of ExifViewer project - https://github.com/PicciMario/EXIF-Viewer)
Copyright (c) 2011 PicciMario <mario.piccinelli@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Various dependencies
import sys, math, os, hashlib, time, urllib, getopt, subprocess, string

# Exif Data Class
# from the ExifViewer project too
from exifviewer import ExifData

# XML manager
# to manage data read from reverse geocoding
from xml.dom import minidom

# Python Imaging Library
# needed to handle images
import PIL, cStringIO
from PIL import ImageDraw
from PIL import Image as PILImage

# ReportLab project dependencies
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer, Image, PageBreak, Table, TableStyle, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# socket default timeout
import socket
socket.setdefaulttimeout(10)

# insert a space in a string after each numChars non-space characters
def wrapString(string, numChars=80):
	completed = False
	while (completed != True):
	
		consecutive = 0
		posInString = 0
		
		for c in string:
			posInString += 1
			if (c not in [' ', '\n']):
				consecutive += 1
				if (consecutive >= numChars):
					consecutive = 0
					string = string[0:posInString] + " " + string[posInString:-1]
					print(posInString)
					continue
					#return string
			else:
				consecutive = 0
			
		completed = True
	
	return string

def usage():
	print("")
	print("PicciMario EXIF reported v. 0.1")
	print("mario.piccinelli@gmail.com")
	print("")
	print("Analyzes a JPG picture and prints a PDF report with informations about")
	print("the file (as told by the filesystem) and about the image itself via its")
	print("EXIF tags. Special care has been thrown in intepreting the GPS data, if")
	print("present the report will contain a map of the location and an approximate")
	print("reverse geocoding of the coordinates into their location name.")
	print("")
	print("Usage:")
	print("exifreporter.py -f filename -o reportname")
	print("")
	print("If a report name is not provided, the tool will use the default: report.pdf.")

filename = ""
reportFileName = ""

try:
	opts, args = getopt.getopt(sys.argv[1:], "hf:o:")
except getopt.GetoptError:
	usage()
	sys.exit(0)

for o,a in opts:
	if o == "-h":
		usage()
		sys.exit(0)
	elif o == "-f":
		filename = a
	elif o == "-o":
		reportFileName = a

if (len(filename) == 0):
	usage()
	print("You need to provide a in input file name.\n")
	sys.exit(1)

if (len(reportFileName) == 0):
	defaultReportFileName = "report.pdf"
	print("Didn't provide an output file name. Using default: %s"%defaultReportFileName)
	reportFileName = defaultReportFileName

# check file existence
if (os.path.isfile(filename) == 0):
	usage()
	print("Provided input file does not exist.\n")
	sys.exit(1)	

# check existence of temp dirs (or create)
tempDirs = ['tmp', 'tmp/prw']

for tempDir in tempDirs:
	if (os.path.isdir(tempDir)):
		continue
	else:
		try:
			os.makedirs(tempDir)
		except:
			print("Unable to create temp dir: \"%s\". Check permissions."%tempDir)
			sys.exit(1)

# clear content of temp dirs
for tempDir in tempDirs:
	for file in os.listdir(tempDir):
		try:
			if os.path.isfile(os.path.join(tempDir, file)):
				os.unlink(os.path.join(tempDir, file))
		except Exception, e:
			print e


# launch EXIV2 to aquire tags
print("Lauch EXIV2 to aquire tags...")
command = [
	"exiv2",
	"-q",
	#"-u",
	"-Pxkyct",
	filename
]
try:
	p = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
except:
	print("\nUnable to run EXIF2. Is it installed and available?")
	print("If not, you have to download it from http://www.exiv2.org/\n")
	sys.exit(1)

# save output in exifs array
exifs = []
while True:
	o = p.stdout.readline()
	if o == '' and p.poll() != None: break
	
	try:
		(tag, key, varType, varNumber, descr) = string.split(o.strip("\n"), None, 4)
	except:
		try:
			(tag, key, varType, varNumber) = string.split(o.strip("\n"), None, 3)
			descr = ""
		except:
			print("Unable to decode key: \"%s\""%key)
			continue	
	
	try:
		key1, key2, key3 = string.split(key, ".")
	except:
		print("Unable to decode key: \"%s\""%key)
		continue

	try:
		exif = {
			"tag": int(tag, 16),
			"key": key,
			"key1": key1,
			"key2": key2,
			"key3": key3,
			"varType": varType,
			"varNumber": int(varNumber),
			"descr": descr
		}
	except:
		print("Unable to decode key: \"%s\""%key)
		continue	
	
	exifs.append(exif)
	
retval = p.wait()

# launch EXIV2 to aquire raw values
print("Lauch EXIV2 to aquire raw values...")
command = [
	"exiv2",
	"-q",
	#"-u",
	"-Pkv",
	filename
]
try:
	p = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
except:
	print("\nUnable to run EXIF2. Is it installed and available?")
	print("If not, you have to download it from http://www.exiv2.org/\n")
	sys.exit(1)

# save output in exifs array
exifRaws = []
while True:
	o = p.stdout.readline()
	if o == '' and p.poll() != None: break

	try:
		(key, raw) = string.split(o.strip("\n"), None, 2)
	except:
		key = o.strip("\n")
		raw = ""
	
	try:
		exifRaw = {
			"raw": raw,
			"key": key
		}
		exifRaws.append(exifRaw)
	except:
		print("Unable to decode raw key: \"%s\""%key)
		continue	
	
retval = p.wait()

# merge two dictionaries
print("Merging values...")
for exif in exifs:
	for exifRaw in exifRaws:
		if (exifRaw['key'] == exif['key']):
			exif['raw'] = exifRaw['raw']
			break

for exif in exifs:
	if ('raw' in exif.keys()):
		continue
	else:
		exif['raw'] = ""

# ------- PDF Styles ----------------------------------------------------

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

styles.add(
	ParagraphStyle(
		name='CodeNoIndent',
		fontName='Courier',
		fontSize=8,
		leading=12,
		firstLineIndent=0,
		leftIndent=0,
		spaceBefore=6
	)
)

styles.add(
	ParagraphStyle(
		name='Small',
		fontName='Times-Roman',
		fontSize=8,
		leading=12,
		spaceBefore=6
	)
)

styles.add(
	ParagraphStyle(
		name='SmallBold',
		fontName='Times-Bold',
		fontSize=8,
		leading=12,
		spaceBefore=6
	)
)

styles.add(
	ParagraphStyle(
		name='Caption',
		fontName='Times-Italic',
		fontSize=8,
		leading=12,
		spaceBefore=6,
		alignment=TA_CENTER
	)
)

tableStyleStandard = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 1),
	('BOTTOMPADDING', (0,0), (-1,-1), 2),
	('LEFTPADDING', (0,0), (-1,-1), 5),
	('RIGHTPADDING', (0,0), (-1,-1), 5),
])

tableStyleSmall = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 0),
	('BOTTOMPADDING', (0,0), (-1,-1), 0),
	('LEFTPADDING', (0,0), (-1,-1), 3),
	('RIGHTPADDING', (0,0), (-1,-1), 3),
])

tableStyle4col = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('BACKGROUND',(0,0),(0,-1),colors.lightgrey),
	('BACKGROUND',(2,0),(2,-1),colors.lightgrey),
	('TOPPADDING', (0,0), (-1,-1), 0),
	('BOTTOMPADDING', (0,0), (-1,-1), 0),
	('LEFTPADDING', (0,0), (-1,-1), 3),
	('RIGHTPADDING', (0,0), (-1,-1), 3),
])

tableStyleImg = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 3),
	('BOTTOMPADDING', (0,0), (-1,-1), 3),
	('LEFTPADDING', (0,0), (-1,-1), 3),
	('RIGHTPADDING', (0,0), (-1,-1), 3),
])

tableStyleGray = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('BACKGROUND',(0,0),(2,0),colors.lightgrey),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 3),
	('BOTTOMPADDING', (0,0), (-1,-1), 3),
	('LEFTPADDING', (0,0), (-1,-1), 3),
	('RIGHTPADDING', (0,0), (-1,-1), 3),
])

Story = []

# ------- Header Section ----------------------------------------------------

def fileMd5(original_filename):
	try:
		f = file(original_filename ,'rb')
		
		md5 = hashlib.md5()
		while True:
			data = f.read()
			if not data:
				break
			md5.update(data)
		md5String = md5.hexdigest()
		
		f.close()
		return md5String
	except:
		return ""

try:
	imageRef = PILImage.open(filename)
	imageFormat = imageRef.format
	imageMode = imageRef.mode
	imageSize = "%sx%s"%(imageRef.size[0], imageRef.size[1])
	imageWidth = imageRef.size[0]
	imageHeight = imageRef.size[1]
except:
	print("Unable to open image file.")
	print("Error: %s"%sys.exc_info()[1])
	sys.exit(1)

Story.append(Paragraph("Image analysis report", styles["Title"]))

thumbWidth = 3*inch
thumbHeight = imageHeight * (float(thumbWidth) / float(imageWidth))

im = Image(filename, thumbWidth, thumbHeight)

imgData = Table(
	[
		[
			Paragraph("File name:", styles["Small"]),
			Paragraph("%s"%filename, styles["Small"])
		],
		[
			Paragraph("File size:", styles["Small"]),
			Paragraph("%s kB"%(os.path.getsize(filename)/1024), styles["Small"])
		],
		[
			Paragraph("File MD5:", styles["Small"]),
			Paragraph("%s"%fileMd5(filename), styles["Small"])
		],
		[
			Paragraph("Image format", styles["Small"]), 
			Paragraph(imageFormat, styles["Small"])
		], 
		[
			Paragraph("Image mode", styles["Small"]), 
			Paragraph(imageMode, styles["Small"])
		],
		[
			Paragraph("Image size", styles["Small"]), 
			Paragraph("%s px"%imageSize, styles["Small"])
		],	

	],
	colWidths=[70, 234]
)
imgData.setStyle(tableStyleSmall)

t=Table([[im, imgData]], colWidths=[3*inch+6, 310])
t.setStyle(tableStyleImg)
Story.append(t)

Story.append(Spacer(10, 20))

# ------- FileSystem Section ---------------------------------------------

Story.append(Paragraph("FileSystem data", styles['Heading2']))

stats = os.stat(filename)

# otherTags stores data in 2 column format (tag, value)
otherTags = []

# attrs stores a list of attributes to append (if available) to otherTags
# [attribute tag - attribute descr - type]
# type:
#    0 - none (string)
#    1 - time
#    2 - binary

attrs = [
	['st_mode', 'Protection bits', 2],
	['st_ino', 'Inode number', 0],
	['st_dev', 'Device', 0],
	['st_nlink', 'Number of hard links', 0],
	['st_uid', 'UID of the owner', 0],
	['st_gid', 'GID of the owner', 0],
	['st_atime', 'Time of most recent access', 1],
	['st_mtime', 'Time of most recent content modification', 1],
	['st_ctime', 'Time of most recent metadata change (time of creation in Windows systems)', 1],
	['st_blocks', 'Number of blocks allocated', 0],
	['st_blksize', 'Filesystem block size', 0],
	['st_rdev', 'Type of device', 0],
	['st_flags', 'User defined flags for file', 0],
	['st_gen', 'File generation number', 0],
	['st_birthtime', 'Time of file creation', 1],
	['st_rsize', 'Rsize (mac os specific)', 0],
	['st_creator', 'Creator (mac os specific)', 0],
	['st_type', 'Type (mac os specific)', 0],
]

for attr in attrs:
	if (hasattr(stats, attr[0])):
		value = getattr(stats, attr[0])
		
		if (attr[2] == 1):
			value = time.ctime(value)
		elif (attr[2] == 2):
			value = bin(value)

		otherTags.append(
			[
				Paragraph(attr[1], styles["Small"]), 
				Paragraph("%s"%value, styles["Small"])
			]
		)

# osData stores data in 4 column format (tag1, value1, tag2, value2)
osData = []

# takes data from otherTags and append (two by two) to osData
while True:
	if (len(otherTags) >= 2):
		osData.append([otherTags[0][0], otherTags[0][1], otherTags[1][0], otherTags[1][1]])
		otherTags.pop(0)
		otherTags.pop(0)
	elif (len(otherTags) == 1):
		osData.append([otherTags[0][0], otherTags[0][1], "", ""])
		otherTags.pop(0)
	else:
		break

osDataTable = Table(osData, colWidths=[140, 125, 140, 125])
osDataTable.setStyle(tableStyle4col)
Story.append(osDataTable)

Story.append(Spacer(10, 10))

# ------- Previews Section ---------------------------------------------

# read previews list with exiv2
print("Lauch EXIV2 to acquire previews list...")
command = [
	"exiv2",
	"-p",
	"p",
	filename
]

try:
	p = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
except:
	print("\nUnable to run EXIF2. Is it installed and available?")
	print("If not, you have to download it from http://www.exiv2.org/\n")
	sys.exit(1)

previews = []
while True:
	o = p.stdout.readline()
	if o == '' and p.poll() != None: break
	previews.append(o)
retval = p.wait()

if (len(previews) > 0):
	Story.append(Paragraph("Preview thumbnails in image data", styles['Heading2']))
		
	# extract previews
	prwDir = "tmp/prw"
	
	print("Lauch EXIV2 to extract preview images...")
	command = [
		"exiv2",
		"-ep",
		"-l",
		prwDir,
		filename
	]
	
	try:
		p = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	except:
		print("\nUnable to run EXIF2. Is it installed and available?")
		print("If not, you have to download it from http://www.exiv2.org/\n")
		sys.exit(1)
	
	while True:
		o = p.stdout.readline()
		if o == '' and p.poll() != None: break		
	retval = p.wait()

	for imageFile in os.listdir(prwDir):
		imagePath = os.path.join(prwDir, imageFile)

		try:
			imageRef = PILImage.open(imagePath)
			imageFormat = imageRef.format
			imageMode = imageRef.mode
			imageSize = "%sx%s"%(imageRef.size[0], imageRef.size[1])
			imageWidth = imageRef.size[0]
			imageHeight = imageRef.size[1]
		except:
			print("Unable to open preview image file \"%s\"."%imagePath)
			print("Error: %s"%sys.exc_info()[1])
			continue

		thumbWidth = 1.5*inch
		thumbHeight = imageHeight * (float(thumbWidth) / float(imageWidth))
		
		im = Image(filename, thumbWidth, thumbHeight)
		
		imgData = Table(
			[
				[
					Paragraph("Preview data size:", styles["Small"]),
					Paragraph("%s kB"%(os.path.getsize(imagePath)/1024), styles["Small"])
				],
				[
					Paragraph("Preview format", styles["Small"]), 
					Paragraph(imageFormat, styles["Small"])
				], 
				[
					Paragraph("Preview mode", styles["Small"]), 
					Paragraph(imageMode, styles["Small"])
				],
				[
					Paragraph("Preview size", styles["Small"]), 
					Paragraph("%s px"%imageSize, styles["Small"])
				],	
		
			],
			colWidths=[70, 329]
		)
		imgData.setStyle(tableStyleSmall)
		
		previewData = Table([[im, imgData]], colWidths=[115, 405])
		previewData.setStyle(tableStyleImg)
		
		Story.append(previewData)

# ------- MAP Section ----------------------------------------------------

def ratString2Deg(data):
	try:
		deg, min, sec = string.split(data, " ")	 	
	 	deg1, deg2 = string.split(deg, "/")
	 	deg = float(deg1) / float(deg2) 	
	 	min1, min2 = string.split(min, "/")
	 	min = float(min1) / float(min2)
		sec1, sec2 = string.split(sec, "/")
	 	sec = float(sec1) / float(sec2)
		ret = deg + (min/60) + (sec/60/60)
		return ret
	
	except:
		return None

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

def gpsUrl(lat, lon, zoom):
	(x, y) = deg2num(lat, lon, zoom)
	imUrl = "http://a.tile.openstreetmap.org/%s/%s/%s.png"%(zoom, x, y)
	return imUrl

def gpsImg(filename, lat, lon, zoom):
	
	x, y = deg2num(lat, lon, zoom)	
	upperLeftLat, upperLeftLon = num2deg(x, y, zoom)
	upperRightLat, upperRightLon = num2deg(x+1, y, zoom)
	bottomLeftLat, bottomLeftLon = num2deg(x, y+1, zoom)
	
	#print("Upper Left: %s - %s"%(upperLeftLat, upperLeftLon))
	#print("Upper Right: %s - %s"%(upperRightLat, upperRightLon))
	#print("Bottom Left: %s - %s"%(bottomLeftLat, bottomLeftLon))
	
	deltaLat = upperLeftLat - bottomLeftLat
	deltaLon = upperRightLon - upperLeftLon
	
	#print("X,Y: %s %s"%(dotX, dotY))
	
	try:
		file = urllib.urlopen(gpsUrl(lat, lon, zoom))
		imRead = cStringIO.StringIO(file.read())
		im = PIL.Image.open(imRead)
		draw = ImageDraw.Draw(im)
		
		imgHeight, imgWidth = im.size 
		
		dotY = imgWidth - int(float((lat - bottomLeftLat) * imgHeight) / float(deltaLat))
		dotX = int(float((lon - upperLeftLon) * imgWidth) / float(deltaLon))
		
		rectWidth = 10
		draw.rectangle([dotX-rectWidth, dotY-rectWidth, dotX+rectWidth, dotY+rectWidth], outline=0)
		im.save(filename)
		
		return 0
	
	except:
		print("Unable to download image for GPS data from OpenStreetMap")
		return 1

def reverseGeocode(lat, lon, zoom):
	try:
		url = "http://nominatim.openstreetmap.org/reverse?format=xml&lat=%s&lon=%s&zoom=%s&addressdetails=1"%(lat, lon, zoom)
		dom = minidom.parse(urllib.urlopen(url))
		address = dom.getElementsByTagName('result')
		if (len(address) >= 1):
			return address[0].firstChild.toxml()
	except:
		print("Unable to fetch reverse geocode data")
		return None
	
	return None

# search for GPS data
gpsDataLat = None
gpsDataLon = None
gpsDataLatRef = 1
gpsDataLonRef = 1

for exif in exifs:
	if (exif['key2'] == "GPSInfo" and exif['key3'] == "GPSLatitude"):
		gpsDataLat = ratString2Deg(exif['raw'])
	elif (exif['key2'] == "GPSInfo" and exif['key3'] == "GPSLongitude"):
		gpsDataLon = ratString2Deg(exif['raw'])
	elif (exif['key2'] == "GPSInfo" and exif['key3'] == "GPSLatitudeRef"):
		if (exif['raw'] == 'S'):
			gpsDataLatRef = -1
	elif (exif['key2'] == "GPSInfo" and exif['key3'] == "GPSLongitudeRef"):
		if (exif['raw'] == 'W'):
			gpsDataLatRef = -1

if (gpsDataLat and gpsDataLon):

	print("Downloading GPS map data...")

	Story.append(Paragraph("EXIF Location data", styles['Heading2']))

	lat = gpsDataLat * gpsDataLatRef
	lon = gpsDataLon * gpsDataLonRef
	
	address = reverseGeocode(lat, lon, 14)
	if (address != None):
		Story.append(Paragraph("The photo seems to have been shot in: \"%s\""%address, styles['Normal']))
		Story.append(Spacer(1, 10))

	imgDim = 2.3*inch
	
	res1 = gpsImg("tmp/temp01.png", lat, lon, 7)
	res2 = gpsImg("tmp/temp02.png", lat, lon, 10)
	res3 = gpsImg("tmp/temp03.png", lat, lon, 13)
	
	if (res1 == 0 and res2 == 0 and res3 == 0):
	
		im1 = Image("tmp/temp01.png", imgDim, imgDim)
		im2 = Image("tmp/temp02.png", imgDim, imgDim)
		im3 = Image("tmp/temp03.png", imgDim, imgDim)
	
		t=Table([[im1, im2, im3]], colWidths=[imgDim + 10, imgDim + 10, imgDim + 10])
		t.setStyle(tableStyleImg)
		Story.append(t)
		
		Story.append(Paragraph("Tiles provided by OpenStreetMap.org (c) OpenStreetMap contributors, CC-BY-SA", styles['Caption']))
		
		Story.append(Spacer(10, 20))

# ------- EXIF Section ----------------------------------------------------

# set for first key
key1 = []
for element in exifs:
	key1.append(str(element['key1']))
key1unique = sorted(set(key1))

for key1 in key1unique:

	# section header
	Story.append(Paragraph(str(key1), styles['Heading2']))

	# select unique values per key2
	key2 = []
	for element in exifs:
		if (element['key1'] == key1): 
			key2.append(str(element['key2']))
		else:
			continue
	key2unique = sorted(set(key2))
	
	for key2 in key2unique:

		# section header
		Story.append(Paragraph(str(key2), styles['Heading3']))
		
		headerData = [
			[
				Paragraph("Key", styles["Small"]), 
				Paragraph("Name", styles["Small"]), 
				Paragraph("Content", styles["Small"])
			]
		]
		t=Table(headerData, colWidths=[30, 170, 330])
		t.setStyle(tableStyleGray)
		Story.append(t)
		Story.append(Spacer(1, 2))
		
		for exif in sorted(exifs, key=lambda k: k['tag']) :
			
			if (exif['key1'] != key1): continue
			if (exif['key2'] != key2): continue
			
			try:
				descrString = unicode(exif['descr'], "utf-8")
			except:
				descString = "Unable to decode string"
			
			firstRow = [
				Paragraph(str(exif['tag']), styles['Small']),
				Paragraph("%s"%exif['key3'], styles['SmallBold']), 
				Paragraph(wrapString(descrString, numChars = 80), styles['Small'])
			]
			
			rawDataString = ""
			if (len(exif['raw'].strip()) > 0):
				try:
					rawDataString = unicode("Raw data: %s"%str(exif['raw']), "utf-8")
				except:
					rawDataString = "Unable to decode string"
		
			secondRow = [
				"", 
				Paragraph("type: %s x %s"%(exif['varNumber'], exif['varType']), styles['Small']), 
				Paragraph(wrapString(rawDataString, numChars = 65), styles['CodeNoIndent'])
			]
		
			elementData = [firstRow, secondRow]
			
			t=Table(elementData, colWidths=[30, 170, 330])
			t.setStyle(tableStyleSmall)
			Story.append(t)
			
			Story.append(Spacer(1, 2))


# ------- DOC Generation ----------------------------------------------------

doc = SimpleDocTemplate(reportFileName, pagesize=letter,
                        rightMargin=40,leftMargin=40,
                        topMargin=40,bottomMargin=40)

doc.build(Story)
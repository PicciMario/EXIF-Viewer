#!/usr/bin/env python

'''
 EXIF data viewer

 (C)opyright 2011 Mario Piccinelli <mario.piccinelli@gmail.com>
 Released under MIT licence
 
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.
 
'''

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import sys, string, logging

class ExifData():
	
	# exif data saved in self.exifs as:
	# [tag number, tag description, value]
	
	def __init__(self):

		# ----------- Globals -------------------------------------------------------------------------------
		
		self.exifs = []
		self.filename = []

		# ----------- Logger --------------------------------------------------------------------------------

		# Logger
		self.log = logging.getLogger('Exif Reader')
		self.log.setLevel(logging.DEBUG)
		#create console handler and set level to debug
		ch = logging.StreamHandler()
		ch.setLevel(logging.DEBUG)
		#create formatter
		formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
		#add formatter to ch
		ch.setFormatter(formatter)
		#add ch to logger
		self.log.addHandler(ch)	
	
	def openFile(self, filename):
	
		# ----------- Open File Data ------------------------------------------------------------------------
		
		try:
			i = Image.open(filename)
			info = i._getexif()
			for tag, value in info.items():
				decoded = TAGS.get(tag, tag)
				self.exifs.append([tag, decoded, value])
			self.exifs = sorted(self.exifs, key=lambda ret: ret[0])
			self.filename = filename
			return 0
		except:
			self.log.error("Error while initializing EXIF data from input file.")
			self.log.debug("Error: %s"%sys.exc_info()[1])
			return 1

	def searchExifKey(self, key):
		for element in self.exifs:
			if (element[0] == key):
				return element
		return None

	def searchExifName(self, name):
		for element in self.exifs:
			if (element[1] == name):
				return element
		return None

	def _convert_to_degrees(self, value):
		d0 = value[0][0]
		d1 = value[0][1]
		d = float(d0) / float(d1)
		
		m0 = value[1][0]
		m1 = value[1][1]
		m = float(m0) / float(m1)
		
		s0 = value[2][0]
		s1 = value[2][1]
		s = float(s0) / float(s1)
		
		return d + (m / 60.0) + (s / 3600.0)

	def _rational_to_num(self, couple):
		if (len(couple) != 2):
			return None	
		return (float(couple[0]) / float(couple[1]))

	def getGpsData(self, gpsValue = None):
		
		if (gpsValue == None):
			gpsTag = self.searchExifKey(34853)
			if (gpsTag != None):
				gpsValue = gpsTag[2]
		
		if (gpsValue != None):
			gps_data = {}
			for t in gpsValue:
				sub_decoded = GPSTAGS.get(t, t)
				gps_data[sub_decoded] = gpsValue[t]
			return gps_data
		else:
			self.log.debug("Did not find GPS data in EXIF data.")
			return None
	
	def decodeGpsData(self, gpsData):
		
		if (gpsData == None):
			return None
		
		# write here the names of the fields analyzed
		# the others will be passed as-is
		usedFields = []
		
		def readField(fieldName):
			if (fieldName in gpsData):
				usedFields.append(fieldName)
				return gpsData[fieldName]
			else:
				return None
		
		lat = None
		lon = None
		imgDir = None
		imgDirRef = None
		timeStamp = None
		
		# GPS lat and lon --------------------------------------

		gpsLatitude = readField('GPSLatitude')
		gpsLongitude = readField('GPSLongitude')
		
		if gpsLatitude:
			lat = self._convert_to_degrees(gpsLatitude)
			gpsLatitudeRef = readField('GPSLatitudeRef')
			if gpsLatitudeRef == "S":                     
				lat = 0 - lat

		if gpsLongitude:
			lon = self._convert_to_degrees(gpsLongitude)
			gpsLongitudeRef = readField('GPSLongitudeRef')
			if gpsLongitudeRef == "W":
				lon = 0 - lon


		# GPS img direction --------------------------------------
		
		gpsImgDirection = readField('GPSImgDirection')	
		gpsImgDirectionRef = readField('GPSImgDirectionRef')	
	
		if gpsImgDirection:
			imgDir = self._rational_to_num(gpsImgDirection)
				
		if gpsImgDirectionRef:
			imgDirRef =  gpsImgDirectionRef
		
		# GPS timestamp ------------------------------------------
		
		gpsTimeStamp = readField('GPSTimeStamp')
		
		if gpsTimeStamp:
			hour = self._rational_to_num(gpsTimeStamp[0])
			minutes = self._rational_to_num(gpsTimeStamp[1])
			sec = self._rational_to_num(gpsTimeStamp[2])
			timeStamp = "%i:%i:%.2f"%(hour, minutes, sec)
		
		# return dictionary --------------------------------------

		ret = {}
		ret['lat'] = lat
		ret['lon'] = lon
		ret['imgDir'] = imgDir
		ret['imgDirRef'] = imgDirRef
		ret['timeStamp'] = timeStamp
		
		ret['other'] = []
		
		# append unused fields 
		for item in gpsData.keys():
			if (item not in usedFields):
				ret['other'].append([item, gpsData[item]])
			
		return ret

	def dumpHex(self, src, length=8, limit=10000):
		FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])
		N=0; result=''
		while src:
			s,src = src[:length],src[length:]
			hexa = ' '.join(["%02X"%ord(x) for x in s])
			s = s.translate(FILTER)
			result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
			N+=length
			if (len(result) > limit):
				src = "";
				result += "(analysis limit reached after %i bytes)"%limit
		return result
	
	def stringHex(self, src, length=16, limit=16):
		FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])
		N=0; result=''
		while src:
			s,src = src[:length],src[length:]
			hexa = ' '.join(["0x%02X"%ord(x) for x in s])
			s = s.translate(FILTER)
			result += "%-*s" % (length*3, hexa)
			N+=length
			if (len(result) > limit):
				src = "";
		return result		
	
	def exifToArray(self, passedTag):
		
		tag = passedTag[0]
		decoded = passedTag[1]
		value = passedTag[2]
	
		returnString = ""
		
		comments = []
	
		# Orientation
		if (tag == 274):
			
			values = {
				1: "The 0th row is at the visual top of the image, and the 0th column is the visual left-hand side.",
				2: "The 0th row is at the visual top of the image, and the 0th column is the visual right-hand side.",
				3: "The 0th row is at the visual bottom of the image, and the 0th column is the visual right-hand side.",
				4: "The 0th row is at the visual bottom of the image, and the 0th column is the visual left-hand side.",
				5: "The 0th row is the visual left-hand side of the image, and the 0th column is the visual top.",
				6: "The 0th row is the visual right-hand side of the image, and the 0th column is the visual top.",
				7: "The 0th row is the visual right-hand side of the image, and the 0th column is the visual bottom.",
				8: "The 0th row is the visual left-hand side of the image, and the 0th column is the visual bottom."
			}
			
			if (value > 0 and value <= 8):
				comments.append(values[value])	
			else:
				comments.append("Value unknown.")				
		
		# Resolution Unit
		elif (tag == 296):
			
			if (value == 2):
				comments.append("XResolution and YResolution measured in pixels/inch.")
			elif (value == 3):
				comments.append("XResolution and YResolution measured in pixels/centimeter")

		# Exposure program
		elif (tag == 34850):

			values = {
				1: "Manual",
				2: "Normal program",
				3: "Aperture priority",
				4: "Shutter priority",
				5: "Creative program (biased toward depth of field)",
				6: "Action program (biased toward fast shutter speed)",
				7: "Portrait mode (for closeup photos with the background out of focus)",
				8: "Landscape mode (for landscape photos with the background in focus)"
			}
			
			if (value in values):
				comments.append(values[value])
			else:
				comments.append("Reserved value.")
										
		# Gps Data
		# decoded
		elif (tag == 34853):

			gpsData = self.decodeGpsData(self.getGpsData(value))
			
			if (gpsData['lat']):
				comments.append("Latitude: %.8f"%gpsData['lat'])
			if (gpsData['lon']):
				comments.append("Longitude: %.8f"%gpsData['lon'])
			if (gpsData['imgDir'] and gpsData['imgDirRef']):
				comments.append("Img dir: %.2f %s"%(gpsData['imgDir'], gpsData['imgDirRef']))
			if (gpsData['timeStamp']):
				comments.append("Timestamp: %s"%gpsData['timeStamp'])
			
			for item in gpsData['other']:
				comments.append("%s: %s"%(item[0], item[1]))

			# clear value
			value = ""

		# Components Configuration
		elif (tag == 37121):
			
			values = {
				0: "",
				1: "Y",
				2: "Cb",
				3: "Cr",
				4: "R",
				5: "G",
				6: "B"
			}
			
			compString = ""
			
			if (len(value) == 4):
				for char in value:
					if (ord(char) in values):
						compString += "%s "%values[ord(char)]
					else:
						compString += "?? "

			value = self.stringHex(value)
			comments.append(compString)
			
		# Metering Mode
		elif (tag == 37383):
		
			values = {
				0: "unknown",
				1: "Average",
				2: "CenterWeightedAverage",
				3: "Spot",
				4: "MultiSpot",
				5: "Pattern",
				6: "Partial",
				255: "Mode reserved"				
			}
			
			if (value in values):
				comments.append("Mode: %s"%values[value])
			else:
				comments.append("Mode unknown")	

		# Light Source
		elif (tag == 37384):
			
			values = {
				0: "Unknown",
				1: "Daylight",
				2: "Fluorescent",
				3: "Tungsten (incandescent light)",
				4: "Flash",
				9: "Fine weather",
				10: "Cloudy weather",
				11: "Shade",
				12: "Daylight fluorescent (D 5700 - 7100K)",
				13: "Day white fluorescent (N 4600 - 5400K)",
				14: "Cool white fluorescent (W 3900 - 4500K)",
				15: "White fluorescent (WW 3200 - 3700K)",
				17: "Standard light A",
				18: "Standard light B",
				19: "Standard light C",
				20: "D55",
				21: "D65",
				22: "D75",
				23: "D50",
				24: "ISO studio tungsten",
				255: "other light source"
			}
			
			if (value in values):
				comments.append(values[value])
			else:
				comments.append("Unknown value.")

		# Flash
		elif (tag == 37385):
			
			flashString = []
			
			if (value & 0b00000001 == 0):
				flashString.append("Flash did not fire.")
			else:
				flashString.append("Flash fired.")
			
			if (value >> 1 & 0b00000011) == 0b00:
				flashString.append("No strobe return detection function.")
			elif (value >> 1 & 0b00000011) == 0b10:
				flashString.append("Strobe return light not detected.")
			elif (value >> 1 & 0b00000011) == 0b11:
				flashString.append("Strobe return light detected.")
			
			if (value >> 3 & 0b00000011) == 0b01:
				flashString.append("Compulsory flash firing.")
			if (value >> 3 & 0b00000011) == 0b10:
				flashString.append("Compulsory flash suppression.")
			if (value >> 3 & 0b00000011) == 0b11:
				flashString.append("Flash in auto mode.")						
			
			if (value >> 6 & 0b00000001) == 0b1:
				flashString.append("Red eye reduction supported.")		

			if (value >> 5 & 0b00000001) == 0b1:
				flashString = [("No flash function.")]
		
			for line in flashString:
				comments.append(line)
			
			# value in bin
			value = bin(value)

		# Subject location
		elif (tag == 37396):
			comments.append("Main subject of the photo in X: %s and Y: %s"%(value[0], value[1]))
			
			if (len(value) == 3):
				comments.append("Main subject in a circle of diameter %s"%(value[2]))
			elif (len(value) == 4):
				comments.append("Main subject in a rectangle of width %s and height %s"%(value[2], value[3]))
				
		# Maker Note
		# (will be printed as hex data)
		elif (tag == 37500):
			
			for line in string.split(self.dumpHex(value, length=16), '\n'):
				if (len(line) > 0):
					comments.append(line)
			
			# clear value
			value = ""					
		
		# UserComment
		elif (tag == 37510):
			for line in string.split(self.dumpHex(value, length=16), '\n'):
				if (len(line) > 0):
					comments.append(line)

		# Sensing Method
		elif (tag == 41495):
		
			values = {
				1: "Not defined",
				2: "One-chip color area sensor",
				3: "Two-chip color area sensor",
				4: "Three-chip color area sensor",
				5: "Color sequential area sensor",
				6: "Trilinear sensor",
				7: "Color sequential linear"				
			}
			
			if (value in values):
				comments.append(values[value])
			else:
				comments.append("Value unknown.")
		
		# File Source
		elif (tag == 41728):
		
			values = {
				3: "Digital Still Camera"
			}
			
			if (ord(value) in values):
				comments.append(values[ord(value)])
			else:
				comments.append("Value unknown")
			
			value = self.stringHex(value)
		
		# Scene Type
		elif (tag == 41729):
			
			values = {
				1: "A directly photographed image"	
			}
			
			if (ord(value) in values):
				comments.append(values[ord(value)])
			else:
				comments.append("Value unknown")
					
			value = self.stringHex(value)
		
		# Other tags
		else:
			if (isinstance(value, tuple)):
				if (len(value) == 2):
					value = "%.4f"%self._rational_to_num(value)
			
			if (tag in [41729, 41730]):
				value = self.stringHex(value)		
	
		# Building return array
		ret = {}
		ret['tag'] = tag
		ret['decoded'] = decoded
		ret['value'] = value
		ret['comments'] = comments
		
		return ret
	
	def exifToString(self, passedTag):
	
		# Analyze tag
		analyzedTag = self.exifToArray(passedTag)
		
		tag = analyzedTag['tag']
		decoded = analyzedTag['decoded']
		value = analyzedTag['value']
		comments = analyzedTag['comments']
		
		# Building return string
		returnString = "%s\t%s: %s"%(tag, decoded, value)
		for line in comments:	
			returnString += "\n\t%s"%line
		
		return returnString
	
	def printExifs(self):
		print("\nList of EXIF tags for \"%s\":\n"%self.filename)
		for element in self.exifs:
			print(self.exifToString(element).strip('\n'))
			  
		print("\nFound %i tags.\n"%len(self.exifs))


def usage():
	print("")
	print("PicciMario EXIF analyzer v. 0.1")
	print("mario.piccinelli@gmail.com")
	print("")
	print("Usage:")
	print("exifviewer.py filename")
	print("")

filename = ""

if (len(sys.argv) <= 1):
	usage()
	sys.exit(1)
else:
	filename = sys.argv[1]

# init exif data manager

exifs = ExifData()
result = exifs.openFile(filename)

if (result != 0):
	print("Unable to init data file")
	sys.exit(1)

exifs.printExifs()

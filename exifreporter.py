#!/usr/bin/env python

from exifviewer import ExifData
import sys
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer, Image, PageBreak, Table, TableStyle, NextPageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def usage():
	print("")
	print("PicciMario EXIF reported v. 0.1")
	print("mario.piccinelli@gmail.com")
	print("")
	print("Usage:")
	print("exifreporter.py filename")
	print("")

filename = ""

if (len(sys.argv) <= 1):
	usage()
	sys.exit(1)
else:
	filename = sys.argv[1]

# init exif data manager

exifData = ExifData()
result = exifData.openFile(filename)

if (result != 0):
	print("Unable to init data file")
	sys.exit(1)

exifs = exifData.getExifs()

# ------- PDF Styles ----------------------------------------------------

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

tableStyleStandard = TableStyle([
	('GRID', (0,0), (-1,-1), 1, colors.black),
	('TEXTCOLOR',(0,1),(1,-1),colors.black),
	('SIZE', (0,0), (-1,-1), 10),
	('TOPPADDING', (0,0), (-1,-1), 1),
	('BOTTOMPADDING', (0,0), (-1,-1), 2),
	('LEFTPADDING', (0,0), (-1,-1), 5),
	('RIGHTPADDING', (0,0), (-1,-1), 5),
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

codeStyle = ParagraphStyle(
	name='Code',
	fontName='Courier',
	fontSize=8,
	leading=8.8,
	firstLineIndent=0,
	leftIndent=0
)

Story = []

# ------- Header Section ----------------------------------------------------

thumbWidth = 3*inch
thumbHeight = exifData.imageHeight * (float(thumbWidth) / float(exifData.imageWidth))

im = Image(filename, thumbWidth, thumbHeight)

imgData = Table(
	[
		["Image format", exifData.imageFormat], 
		["Image mode", exifData.imageMode],
		["Image size", "%s px"%exifData.imageSize]
	],
	colWidths=[94, 210]
)
imgData.setStyle(tableStyleStandard)

t=Table([[im, imgData]], colWidths=[3*inch+6, 310])
t.setStyle(tableStyleImg)
Story.append(t)

Story.append(Spacer(10, 20))

# ------- EXIF Section ----------------------------------------------------

headerData = [
	[
		Paragraph("<font size=8>Key</font>", styles["Normal"]), 
		Paragraph("<font size=8>Name</font>", styles["Normal"]), 
		Paragraph("<font size=8>Content</font>", styles["Normal"])
	]
]
t=Table(headerData, colWidths=[40, 130, 360])
t.setStyle(tableStyleGray)
Story.append(t)
Story.append(Spacer(1, 2))

for exif in exifs:
	elementData = [
		[
			Paragraph("<font size=8>%s</font>"%str(exif['tag']), styles["Normal"]), 
			Paragraph("<font size=8>%s</font>"%str(exif['decoded']), styles["Normal"]), 
			Paragraph("<font size=8>%s</font>"%str(exif['value']), styles["Normal"])
		]
	]
	for line in exif['comments']:
		elementData.append(['', '', Paragraph(str(line), codeStyle)])
	
	t=Table(elementData, colWidths=[40, 130, 360])
	t.setStyle(tableStyleStandard)
	Story.append(t)
	
	Story.append(Spacer(1, 2))


# ------- DOC Generation ----------------------------------------------------

doc = SimpleDocTemplate("form_letter.pdf",pagesize=letter,
                        rightMargin=72,leftMargin=72,
                        topMargin=72,bottomMargin=18)

doc.build(Story)
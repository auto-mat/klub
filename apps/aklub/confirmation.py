# coding=utf-8
from datetime import datetime
import os
import reportlab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def makepdf(outfile, name, sex, street, city, year, amount):
        DIR = os.path.dirname(__file__)
	# CONFIGURATION
	logo = os.path.join(DIR, "logo.jpg")
	signature = os.path.join(DIR, "signature.png")
	statutory_name = u"Jakub Stránský"
	statutory_titles = [
		u"člen výkonné rady o.s. Auto*Mat",
		u"statutární zástupce",
	]

	# different wording based on user's sex
	if sex == 'female':
		poukazal = u"poukázala"
	else:
		poukazal = u"poukázal"

	text1 = u"""
	Potvrzujeme tímto, že %s %s za rok %d
	na účet občanského sdružení Auto*Mat dar ve výši %d,- Kč,
	určený na činnost sdružení. Dar byl použit na ekologické
    účely, konkrétně na podporu veřejné, pěší a cyklistické
    dopravy v Praze.""" % (name, poukazal, year, amount)

	text2 = u"""
	Potvrzení vydáváme pro uplatnění odpočtu hodnoty daru
	ze základu daně podle zákona 586/1992 Sb.
	při dodržení zákonných podmínek.
	"""

	footer1 = u"Auto*Mat, o.s.  – iniciativa pro lepší kvalitu života ve městě"
	footer2 = u"Kancelář: Bořivojova 108, 130 00 Praha 3 | M: auto-mat@auto-mat.cz | T: 212 240 666 | W: www.auto-mat.cz"
	footer3 = u"Sídlo: Lublaňská 18, 120 00 Praha 2 | IČ: 226 703 19 | Účet vedený u ČSOB v Praze 1: 217 359 444 / 0300"

	filename = "potvrzeni2011.pdf"
	# END OF CONFIGURATION

        folder = '/usr/share/fonts/truetype/ttf-dejavu'
        reportlab.rl_config.TTFSearchPath.append(folder) 
	pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
	pdfmetrics.registerFont(TTFont('DejaVuB', 'DejaVuSans-Bold.ttf'))

	doc = SimpleDocTemplate(outfile,pagesize=A4,
		rightMargin=72,leftMargin=72,
		topMargin=72,bottomMargin=18)
	Story=[]

	# STYLES
	styles=getSampleStyleSheet()
	styles['Normal'].fontName = 'DejaVu'
	styles['Normal'].fontSize = 10
	styles['Heading1'].fontName = 'DejaVuB'
	styles['Heading1'].fontSize = 12
	styles['Heading1'].alignment = TA_CENTER
	styles.add(ParagraphStyle(name='Indented', leftIndent=290))
	styles['Indented'].fontName = 'DejaVu'

	# START OF THE DOCUMENT
	im = Image(logo, 5.98*cm, 2.54*cm)
	Story.append(im)
	Story.append(Spacer(1, 30))

	Story.append(Paragraph(name, styles["Indented"]))
	Story.append(Spacer(1, 6))
	Story.append(Paragraph(street, styles["Indented"]))
	Story.append(Spacer(1, 6))
	Story.append(Paragraph(city, styles["Indented"]))
	Story.append(Spacer(1, 48))

	Story.append(Paragraph(u"Potvrzení o přijetí daru", styles["Heading1"]))
	Story.append(Spacer(1, 36))

	d = datetime.now()
	datestr = "%d. %d. %d" % (d.day, d.month, d.year)
	Story.append(Paragraph(u"V Praze dne %s" % datestr, styles["Indented"]))
	Story.append(Spacer(1, 96))

	Story.append(Paragraph(text1, styles["Normal"]))
	Story.append(Spacer(1, 24))
	Story.append(Paragraph(text2, styles["Normal"]))
	Story.append(Spacer(1, 72))

	Story.append(Paragraph(statutory_name, styles["Normal"]))
	for t in statutory_titles:
		Story.append(Spacer(1, 6))
		Story.append(Paragraph(t, styles["Normal"]))

	def firstPageGraphics(canvas, doc):
		canvas.saveState()

		im = Image(signature, 5.8*cm, 4.7*cm)
		im.drawOn(canvas, 100, 100)
		canvas.setLineWidth(.3)
		canvas.line(45,80,550,80)
		canvas.setFont('DejaVuB', 9)
		canvas.drawString(145,65,footer1)
		canvas.setFont('DejaVu', 9)
		canvas.drawString(50,50,footer2)
		canvas.drawString(60,35,footer3)
		canvas.restoreState()

	doc.build(Story, onFirstPage=firstPageGraphics)
	# done

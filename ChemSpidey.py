#!/usr/bin/env python
#
#!/usr/bin/python2.4
#
# 
"""ChemSpidey - a ChemSpider robot for Wave.

Gives you the an image of a named chemical for text in a blip. Heavily dependant on
'Grauniady' the Guardian API Robot written by Chris Thorpe
"""

__author__ = 'cameron.neylon@stfc.ac.uk (Cameron Neylon)'

from waveapi import events
from waveapi import model
from waveapi import robot
import waveapi.document as doc
import re

import ChemSpiPy

def SetManualLink(blip, text, value, key='link/manual'):
    """Aims to find text in the passed blip and then create link via setting annotation."""

    contents = blip.GetDocument().GetText()
    if text in contents:
        r = doc.Range()
	r.start = contents.find(text)
        r.end = r.start + len(text)
	blip.GetDocument().SetAnnotation(r, key, value)



def OnBlipSubmitted(properties, context):
    blip = context.GetBlipById(properties['blipId'])
    contents = blip.GetDocument().GetText()
    key = '(chem)'
    leftdelim = '\\['
    query = '([a-zA-Z0-9-]{1,20})'
    optintspacer = ';?'
    optfloat = '\\s?(\\d{0,5}\\.?\\d{0,5})?'
    optunits = '\\s?([mgl]{1,2})?'
    optional  = optintspacer + optfloat + optunits
    rightdelim = '\\]'

    compiledregex = re.compile(key+leftdelim+query+optional+rightdelim, re.IGNORECASE|re.DOTALL)
    chemicallist = compiledregex.finditer(contents)

    if chemicallist != None:
        count = 0
        changeslist = []
        for chemicalname in chemicallist: 
            r = doc.Range(0,0)
            r.start = chemicalname.start()
            r.end = chemicalname.end() + 1
            query = chemicalname.group(2)
            compound = ChemSpiPy.simplesearch(query)
            url = "http://www.chemspider.com/Chemical-Structure.%s.html" % compound
            insert = query + " (csid:" + compound 

            if chemicalname.group(3) != None and chemicalname.group(4) == 'mg':
                nanomoles = 1000*(float(chemicalname.group(3))/compound.molweight())
                nanomoles = round(nanomoles, 2)
                insert = insert + ", " + chemicalname.group(3) + 'mg, ' + str(nanomoles) + " nanomoles"

            if chemicalname.group(3) != None and chemicalname.group(4) == 'g':
                millimoles = 1000*(float(chemicalname.group(3))/compound.molweight())
                millimoles = round(millimoles, 2)
                insert = insert + ", " + chemicalname.group(3) + 'g, ' + str(millimoles) + " millimoles"

            insert = insert + ") "
                    
            changeslist.append([r, insert, compound, url])
            count = count + 1

        while count != 0:
            count = count - 1
            blip.GetDocument().SetTextInRange(changeslist[count][0], changeslist[count][1])
            SetManualLink(blip, changeslist[count][2], changeslist[count][3])
            SetManualLink(blip, changeslist[count][1], 'chem', 'lang')
            

def OnRobotAdded(properties, context):
  """Invoked when the robot has been added."""
  root_wavelet = context.GetRootWavelet()
  root_wavelet.CreateBlip().GetDocument().SetText("Hello, I'm ChemSpidey, I will convert text of the form chem[chemicalName] to a link to ChemSpider. If you add a semicolon and a weight in g or mg within the square brackets I will also calculate ththe number of moles for you. This is Version 3 of ChemSpidey")



if __name__ == '__main__':
  ChemSpidey = robot.Robot('chemspidey',
                         image_url='http://www.chemspider.com/ImagesHandler.ashx?id=236',
			 version = '3',
                         profile_url='http://www.google.com')
  ChemSpidey.RegisterHandler(events.BLIP_SUBMITTED, OnBlipSubmitted)
  ChemSpidey.RegisterHandler(events.WAVELET_SELF_ADDED, OnRobotAdded)

  ChemSpidey.Run(debug=True)

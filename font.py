#!/usr/bin/python

from struct import *;
import string

font_name_identifiers = ("Copyright Notice", "Font Family", "Font Subfamily",
"Unique Subfamily Identification", "Real Name", "Version", "PostScript Name",
"Trademark notice", "Manufacturer Name", "Designer", "Description", "Vendor URL",
"Designer URI", "License Description", "License Information URL", "Reserved",
"Preferred Family", "Preferred Subfamily", "Full Name", "Sample Text");

def hexdump (Data, data_offset = 0):
	Counter = 0;
	Div = 4;
	Buffer = "";
	LineData = ""
	for Ch in Data:
		if (Counter % 16) == 0:
			Buffer += (hex (Counter + data_offset) + " ").rjust (7) + " ";
		Div -= 1;
		Buffer += string.zfill ((hex ( ord(Ch)) [2:]), 2) + " ";
		if (ord (Ch) >= 32) & (ord (Ch) < 127):
			LineData += Ch;
		else:
			LineData += ".";
		if Div == 0:
			Div = 4;
			Buffer += " ";
		if (Counter % 16) == 15:
			Buffer += " " + LineData + "\n";
			LineData = "";
		Counter += 1;
	Length = Counter % 16;
	return Buffer + LineData.rjust (53 - ((Length * 3) + int(Length / 4)) + len (LineData));

def ttf_getname (fname):
    global font_name_identifiers
    f = open(fname,"r")
    version, tnum, searchrange, entryselector, rangeshift = unpack (">iHHHH", f.read(12))
    #look for headers
    headers={}
    for i in range(0, tnum):
        tag = f.read(4)
        headers[tag] = unpack (">LLL", f.read(12))
    #find name
    cs, ofs, len = headers['name'];
    f.seek (ofs);
    format, count, strofst = unpack (">HHH", f.read(6));
    p = open (fname, "r");
    fontname = ""
    for i in range (0, count):
        platform, encoding, language, name, length, offset  = unpack (">HHHHHH", f.read(12));
#	print font_name_identifiers [name];
        if (((name == 4) | (name == 6)) & ((platform == 1) | (platform == 3))):
            p.seek (ofs + strofst + offset);
	    fontname = p.read (length);
    return fontname;


def nicename (name):
    name = string.lower (name)
    rname = ""
    for c in name:
	if (ord (c) >= 97) & (ord (c) < 123):
            rname = rname + c
    return string.lower (rname)

import sys, os, shutil, fnmatch, re

try:
    os.mkdir ("old")
except:
    pass

try:
    os.mkdir ("renamed")
except:
    pass


ttfname = re.compile (".*\.[tT][tT][fF]")

for origname in os.listdir("."):
    if ttfname.match (origname):
        newname = ttf_getname (origname);
        newname = nicename (newname);
        print newname;
        if (newname != ""):
            shutil.copy (origname, "renamed/" + newname + ".ttf")
            shutil.move (origname, "old/" + origname)

#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# This file exists because I have no idea what I'm doing in unicode in python.
#
#    !/usr/bin/python

def cauterize(textToCauterize):
    """
    Just kills me.
    """
    workingText = textToCauterize.replace(u'\u00C3', "A")
    workingText = workingText.replace(u'\u00AE', "(R)")
    workingText = workingText.replace(u'\u00A9', "(C)")
    workingText = workingText.replace(u'\u00C1', "a")
    workingText = workingText.replace(u'\u00C9', "E")
    workingText = workingText.replace(u'\u00CD', "i")
    workingText = workingText.replace(u'\u00CE', "I")
    workingText = workingText.replace(u'\u00D1', "N")
    workingText = workingText.replace(u'\u00D7', "X")
    workingText = workingText.replace(u'\u00E1', "a")    
    workingText = workingText.replace(u'\u00E2', "a")    
    workingText = workingText.replace(u'\u00E4', "a")
    workingText = workingText.replace(u'\u00E8', "e")
    workingText = workingText.replace(u'\u00E9', "e")
    workingText = workingText.replace(u'\u00ED', "i")
    workingText = workingText.replace(u'\u00F1', "n")
    workingText = workingText.replace(u'\u00F3', "o")
    workingText = workingText.replace(u'\u00F6', "o")
    workingText = workingText.replace(u'\u00F8', "o")
    workingText = workingText.replace(u'\u00FA', "u")
    workingText = workingText.replace(u'\u00FC', "u")
    workingText = workingText.replace(u'\u00FD', "y")
    workingText = workingText.replace(u'\u0107', "c")
    workingText = workingText.replace(u'\u010D', "c")
    workingText = workingText.replace(u'\u011B', "e")
    workingText = workingText.replace(u'\u0142', "l")
    workingText = workingText.replace(u'\u0159', "r")
    workingText = workingText.replace(u'\u015D', "s")
    workingText = workingText.replace(u'\u015E', "S")
    workingText = workingText.replace(u'\u0160', "S")
    workingText = workingText.replace(u'\u0161', "s")
    workingText = workingText.replace(u'\u016F', "u")
    workingText = workingText.replace(u'\u017E', "z")
    workingText = workingText.replace(u'\u0392', "Beta")
    workingText = workingText.replace(u'\u03B1', "alpha")
    workingText = workingText.replace(u'\u03B2', "beta")
    workingText = workingText.replace(u'\u03B4', "delta")
    workingText = workingText.replace(u'\u03b8', "theta")
    workingText = workingText.replace(u'\u03c3', "sigma")
    workingText = workingText.replace(u'\u0422', "T")   # Cyrillic
    workingText = workingText.replace(u'\u2010', "-")
    workingText = workingText.replace(u'\u2013', "-")
    workingText = workingText.replace(u'\u2014', "-")
    workingText = workingText.replace(u'\u2015', "-")
    workingText = workingText.replace(u'\u2018', "'")
    workingText = workingText.replace(u'\u2019', "'")
    workingText = workingText.replace(u'\u201C', '"')
    workingText = workingText.replace(u'\u201D', '"')
    workingText = workingText.replace(u'\u2021', "+")   # double dagger
    workingText = workingText.replace(u'\u2022', "*")
    workingText = workingText.replace(u'\u2026', "...")
    workingText = workingText.replace(u'\u2032', "'")   # prime
    workingText = workingText.replace(u'\u2212', "-")   # minus
    workingText = workingText.replace(u'\u2606', "*")
    workingText = workingText.replace(u'\xa0', " ") # http://www.charbase.com/00a0-unicode-no-break-space
    workingText = workingText.replace(u'\xb7', ".") # http://www.charbase.com/00b7-unicode-middle-dot
    workingText = workingText.replace(u'\xce', "I") # http://www.charbase.com/00ce-unicode-latin-capital-letter-i-with-circumflex
    workingText = workingText.replace(u'\xd6', "O") # http://www.charbase.com/00d6-unicode-latin-capital-letter-o-with-diaeresis
    workingText = workingText.replace(u'\xde', "P") # http://www.charbase.com/00de-unicode-latin-capital-letter-thorn
    workingText = workingText.replace(u'\xe7', "c") # http://www.charbase.com/00e7-unicode-latin-small-letter-c-with-cedilla
    workingText = workingText.replace(u'\xea', "e") # http://www.charbase.com/00ea-unicode-latin-small-letter-e-with-circumflex
    workingText = workingText.replace(u'\xeb', "e") # http://www.charbase.com/00eb-unicode-latin-small-letter-e-with-diaeresis
    workingText = workingText.replace(u'\xef', "i") # http://www.charbase.com/00ef-unicode-latin-small-letter-i-with-diaeresis
    workingText = workingText.replace(u'\xc0', "A") # http://www.charbase.com/00c0-unicode-latin-capital-letter-a-with-grave
    workingText = workingText.replace(u'\xe3', "a") # http://www.charbase.com/00e3-unicode-latin-small-letter-a-with-tilde
    workingText = workingText.replace(u'\xe5', "a") # http://www.charbase.com/00e5-unicode-latin-small-letter-a-with-ring-above
    
    return(workingText)

def cauterizeWithDecode(textToCauterize):
    """
    Just kills me.
    """
    workingText = textToCauterize.decode("utf-8")
    return(cauterize(workingText))
    

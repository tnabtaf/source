#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file exists because I have no idea what I'm doing in unicode in python.
#

def cauterize(textToCauterize):
    """
    Just kills me.
    """
    workingText = textToCauterize.replace(u'\u00C3', "A")
    workingText = workingText.replace(u'\u00A9', "(C)")
    workingText = workingText.replace(u'\u00C1', "a")
    workingText = workingText.replace(u'\u00CD', "i")
    workingText = workingText.replace(u'\u00CE', "I")
    workingText = workingText.replace(u'\u00D1', "N")
    workingText = workingText.replace(u'\u00E1', "a")    
    workingText = workingText.replace(u'\u00E2', "a")    
    workingText = workingText.replace(u'\u00E4', "a")
    workingText = workingText.replace(u'\u00E8', "e")
    workingText = workingText.replace(u'\u00E9', "e")
    workingText = workingText.replace(u'\u00ED', "i")
    workingText = workingText.replace(u'\u00F3', "o")
    workingText = workingText.replace(u'\u00F6', "o")
    workingText = workingText.replace(u'\u00FC', "u")
    workingText = workingText.replace(u'\u00F1', "n")
    workingText = workingText.replace(u'\u0392', "Beta")
    workingText = workingText.replace(u'\u03B1', "alpha")
    workingText = workingText.replace(u'\u03B2', "beta")
    workingText = workingText.replace(u'\u2010', "-")
    workingText = workingText.replace(u'\u2013', "-")
    workingText = workingText.replace(u'\u2014', "-")
    workingText = workingText.replace(u'\u2015', "-")
    workingText = workingText.replace(u'\u2018', "'")
    workingText = workingText.replace(u'\u2019', "'")
    workingText = workingText.replace(u'\u201C', '"')
    workingText = workingText.replace(u'\u201D', '"')
    workingText = workingText.replace(u'\u2022', "*")
    workingText = workingText.replace(u'\u2026', "...")
    workingText = workingText.replace(u'\u2606', "*")
    
    return(workingText)

def cauterizeWithDecode(textToCauterize):
    """
    Just kills me.
    """
    workingText = textToCauterize.decode("utf-8")
    return(cauterize(workingText))
    

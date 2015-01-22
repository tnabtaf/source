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
    workingText = workingText.replace(u'\u00CE', "I")
    workingText = workingText.replace(u'\u00D1', "N")
    workingText = workingText.replace(u'\u00E4', "a")
    workingText = workingText.replace(u'\u00E8', "e")
    workingText = workingText.replace(u'\u00E9', "e")
    workingText = workingText.replace(u'\u00ED', "i")
    workingText = workingText.replace(u'\u00F6', "o")
    workingText = workingText.replace(u'\u00FC', "u")
    workingText = workingText.replace(u'\u00F1', "n")
    workingText = workingText.replace(u'\u0392', "Beta")
    workingText = workingText.replace(u'\u03B1', "alpha")
    workingText = workingText.replace(u'\u03B2', "beta")
    workingText = workingText.replace(u'\u2010', "-")
    workingText = workingText.replace(u'\u2013', "-")
    workingText = workingText.replace(u'\u2022', "*")
    
    return(workingText)

def cauterizeWithDecode(textToCauterize):
    """
    Just kills me.
    """
    workingText = textToCauterize.decode("utf-8")
    return(cauterize(workingText))
    

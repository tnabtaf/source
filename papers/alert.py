#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Generic class to represent alerts.
# Each alert describes a list of papers from a particular source, reported as a group.

import re
import HTMLParser


class PaperAlert(object):
    """
    Abstract class for alerts from any source.
    Class def serves as a template and hopes to intercept any method/attribute
    references that aren't overridden by subclasses.
    """

    def __init__(self):
        """
        
        """
        self.title = None
        self.authors = None
        self.source = None
        self.doiUrl = None
        self.doi = None
        self.url = None                   # a non-DOI URL
        self.search = None
        return None

    def getTitleLower(self):
        return(self.title.lower())
        
    def getFirstAuthorLastName(self):
        """
        Don't assume any consisten way to get this.  This had better be overriden.
        """
        return 1/0

    def getFirstAuthorLastNameLower(self):
        firstAuthor = self.getFirstAuthorLastName()
        if firstAuthor:
            firstAuthor = firstAuthor.lower()
        return firstAuthor

    def debugPrint(self):
        print("Title: " + self.title)
        print("Authors: " + self.authors)
        print("Source: " + self.source)
        print("DOI URL: " + self.doiUrl)
        print("DOI: " + self.doi)
        print("-----------------")
        return(None)

        
class Alert(object):
    """
    All the information in an alert.
    """

    def __init__(self):

        self.papers = []               # alerts must contain one or more papers
        self.search = ""               # used to identify which alert papers are from
        return None
        

    def getPapers(self):
        """
        Return list of referencing papers in this alert.
        """
        return(self.papers)

    def getSearch(self):
        """
        Returns text identifying what web os science search this alert is for.
        """
        return(self.search)

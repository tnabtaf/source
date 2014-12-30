#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Module to access a CiteULike library.

import json

class CiteULikeEntry(object):
    '''
    Provide access to a CiteULike JSON Entry
    '''

    def __init__(self, CUL_JSON):
        """
        Given a python encoded JSON description of a paper from CiteULike,
        create a python object for it.
        """
        self.culJson = CUL_JSON
        return

    def getTitle(self):
        return(self.culJson["title"])

    def getTitleLower(self):
        return(self.culJson["title"].lower())

    def getCulUrl(self):
        return(self.culJson["href"])

    def getDoi(self):
        return(self.culJson.get("doi"))

    def getJournalName(self):
        if self.getPublicationType() == "JOUR":
            return(self.culJson["journal"])
        else:
            return("")

    def getAuthors(self):
        return(self.culJson.get("authors"))

    def getFirstAuthorLastName(self):
        authors = self.getAuthors()
        if authors:
            return(authors[0].split()[-1])
        else:
            return None

    def getFirstAuthorLastNameLower(self):
        firstAuthor = self.getFirstAuthorLastName()
        if firstAuthor:
            firstAuthor = firstAuthor.lower()
        return firstAuthor


class CiteULikeLibrary(object):
    """
    Encapsulates a CiteULike library in an accessible structure.
    """
    def __init__(self, culSource):

        """
        Given either a CiteULike JSON file, or a URL from with that file can be
        obtained.  Process that into a library that can be used by the caller.
        """
        try:
            culFile = open(culSource, "r")
            self.fileName = culSource
            
        except IOError as err:
            # not a file, let's hope its a URL.
            print("Heh, heh.  Need write codde to deal with URL's as sources.")
            raise

        self.culJson = json.load(culFile)   # get whole file at once.

        self.byTitleLower = {}
        self.byDoi = {}
        self.by1stAuthorLastNameLower = {}

        for culPub in self.culJson:
            culEntry = CiteULikeEntry(culPub)
            # print(culPub)

            titleLower = culEntry.getTitleLower()
            self.byTitleLower[titleLower] = culEntry
            doi = culEntry.getDoi()
            if doi:
                self.byDoi[doi] = culEntry
                authorLower = culEntry.getFirstAuthorLastNameLower()
                if authorLower not in self.by1stAuthorLastNameLower:
                    self.by1stAuthorLastNameLower[authorLower] = {}
                self.by1stAuthorLastNameLower[authorLower][titleLower] = culEntry

        culFile.close()

        return(None)


    def getByTitleLower(self, titleLower):
        return(self.byTitleLower.get(titleLower))

    def getByDoi(self, doi):
        return(self.byDoi.get(doi))

    def getBy1stAuthorLastNameLower(self, lastNameLower):
        return(self.by1stAuthorLastNameLower.get(lastNameLower))


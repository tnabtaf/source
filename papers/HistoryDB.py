#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Keep track of and use information from out previous runs.  The DB is just a tab delimited file.

import csv

import Matchup

NEW     = "new"
TITLE   = "title"
AUTHORS = "authors"
DOI     = "doi"

COLUMNS = [NEW, TITLE, AUTHORS, DOI]


class HistoryDB(object):
    def __init__(self, csvInFileName):

        self.byTitleLower = {}
        self.byDoi = {}
        csvIn = open(csvInFileName, "r")
        csvReader = csv.DictReader(csvIn, fieldnames=COLUMNS, dialect="excel-tab")
        for row in csvReader:
            
            self.byTitleLower[row[TITLE].lower()] = row
            self.byDoi[row[DOI]] = row

        csvIn.close()
        
        return None

    def getByTitleLower(self, lowerTitle):
        return(self.byTitleLower.get(lowerTitle))

        
    def getByDoi(self, doi):
        return(self.byDoi.get(doi))

        


def writeHistory(matchups, sortedTitles, csvOutFileName):
    
    csvOut = open(csvOutFileName, "w")
    csvWriter = csv.DictWriter(csvOut, fieldnames=COLUMNS, dialect="excel-tab")
    csvWriter.writeheader()

    for title in sortedTitles:
        matchup = matchups[title]
        row = {}
        newPaper = not matchup.culEntries
        if newPaper:
            row[NEW] = 1
        else:
            row[NEW] = 0

        row[TITLE]   = matchup.papers[0].title
        row[AUTHORS] = matchup.papers[0].authors
        row[DOI]     = Matchup.getDoiFromPaperList(matchup.papers)

        csvWriter.writerow(row)

    return None

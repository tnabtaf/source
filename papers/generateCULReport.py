#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Generate reports about the Galaxy CiteULike library.
# Reports are generated in both TSV and MoinMoin markup.
#


import argparse

import CiteULike                          # CiteULike Handling

class FastCulLib(object):
    """
    Provides quick access to a citeulike library.
    """

    def __init__(self, culLib):
        """
        Given a CiteULike library, build quick index strucutures needed by
        reports.
        """
        self.culLib = culLib

        # These are replaced by frozensets at the end.
        byYear = {}          # unordered array of papers from that year
        byTag = {}           # value is unordered array of papers w/ tag
        byJournal= {}        # unordered list of papers in each journal
    
        for paper in culLib.allPapers():

            # Process Year
            year = paper.getYear()
            if year == "unknown":
                print("Year UNKNOWN", paper.culJson) # Fix these when you find them.
            if year not in byYear:
                byYear[year] = []
            byYear[year].append(paper)

            # Process tags
            tags = paper.getTags()                # every paper should have tags
            for tag in tags:
                if tag not in byTag:
                    byTag[tag] = []
                byTag[tag].append(paper)
            if len(tags) == 0:
                # should not happen, fix it when it happens.
                print("Paper missing tags", paper.getTitle(), paper.getCulUrl())

            # Process Journal
            jrnl = paper.getJournalName()
            if jrnl:
                if jrnl not in byJournal:
                    byJournal[jrnl] = []
                byJournal[jrnl].append(paper) 

        # create set versions
        self.byYear = {}
        for year in byYear:
            self.byYear[year] = frozenset(byYear[year])
        self.byTag = {}
        for tag in byTag:
            self.byTag[tag] = frozenset(byTag[tag])
        self.byJournal = {}
        for journal in byJournal:
            self.byJournal[journal] = frozenset(byJournal[journal])
        
        return(None)

    def getYears(self):
        """
        Return a list of years that papers were published in, in chronological
        order.
        """
        return(sorted(self.byYear.keys()))

    def getTags(self):
        """
        Return an unordered list of tags that exist in this lib.
        """
        return(self.byTag.keys())

    def getJournals(self):
        """
        Return an unordered list of Journal names.
        """
        return(self.byJournal.keys())

    def getPapers(self,
                  tag = None,
                  year = None,
                  journal = None):
        """
        Given any combination of tag, year and.or journal, return the only the
        set of papers that have the sepcified combination of values.
        """
        sets = []
        if tag:
            sets.append(self.byTag[tag])
        if year:
            sets.append(self.byYear[year])
        if journal:
            sets.append(self.byJournal[journal])

        if len(sets) == 0:
            return(culLib.allPapers())
        elif len(sets) == 1:
            return(sets[0])
        else:
            narrowed = sets[0]
            for restriction in sets[1:]:
                narrowed = narrowed.intersection(restriction)
            return(narrowed)


def genMoinTagYearReport(fastCulLib):
    """
    Generate a papers by tag and year report in MoinMoin markup.
    Report is returned as a multi-line string.
    """
    # Preprocess. Need to know order of tags and years.
    tags = fastCulLib.getTags()
    # Count number of papers with each tag
    nPapersWTag = {}
    for tag in tags:
        nPapersWTag[tag] = len(fastCulLib.getPapers(tag=tag))

    # sort tags by paper count, max first
    tagsInCountOrder = [tag for tag in
                        sorted(nPapersWTag.keys(),
                               key=lambda keyValue: - nPapersWTag[keyValue])]

    report = []                # now have everything we need; generate report
    
    # generate header
    report.append('||<|2 class="th"> Year ' +
                  '||<-' + str(len(tags)) + ' class="th"> Tags ||' +
                  '||<|2 class="th"> # ||\n')

    for tag in tagsInCountOrder:
        report.append('||<class="th"> ' + tag + ' ')
    report.append('||\n')

    # generate numbers per year
    for year in fastCulLib.getYears():  # years are listed chronologically
        nPapersThisYear = len(fastCulLib.getPapers(year=year))
        report.append('||<class="th"> ' + year + ' ')
        for tag in tagsInCountOrder:
            papersForTagYear = fastCulLib.getPapers(tag=tag, year=year)
            if papersForTagYear:
                count = str(len(papersForTagYear))
            else:
                count = ""
            report.append('||<)> ' + count + ' ')
        report.append('||<)> ' + str(nPapersThisYear) + ' ||\n')

    # generate total line at bottom
    report.append('||<class="th"> Total ||<) class="th"> ' +
                  str(len(fastCulLib.getPapers())) + ' ')
    for tag in tagsInCountOrder:
        report.append('||<) class="th"> ' + str(nPapersWTag[tag]) + ' ')
    report.append('||\n')

    return("".join(report))


    
def argghhs():
    """
    Process and provide access to command line arguments.
    """

    argParser = argparse.ArgumentParser(
        description="Generate reports for the CiteULike Galaxy library.")
    argParser.add_argument(
        "-c", "--cullib", required=True,
        help="JSON formatted file containing CiteUlike Library; obtained by going to http://www.citeulike.org/json/group/16008")
    argParser.add_argument(
        "--tagyear", required=False, action="store_true",
        help="Produce table showing number of papers with each tag, each year.")
    argParser.add_argument(
        "--journalyear", required=False, action="store_true",
        help="Produce table showing number of papers in different journals, each year.")
    argParser.add_argument(
        "--moin", required=False, action="store_true",
        help="Produce report(s) using MoinMoin markup")
    argParser.add_argument(
        "--csv", required=False,
        help=("Produce report(s) in CSV format"))

    return(argParser.parse_args())


        
# =============================================================
# MAIN

args = argghhs()                          # process command line arguments
# print str(args)

# create database from CiteULike Library.
culLib = CiteULike.CiteULikeLibrary(args.cullib)

fastCulLib = FastCulLib(culLib)

if args.tagyear:

    # Generate them reports

    # options are to have one routine per report/format combo, or create a Moin
    # report, or a csv report and then have their separate methods do the dirty
    # work. Try that.

    # report showing papers by tag by year requested.
    if args.moin:
        # generate a tag year report in MoinMoin format.
        moinReport = genMoinTagYearReport(fastCulLib)
        print(moinReport)
    if args.csv:
        # generate tag year data in a tab delimited file
        csvReport = genCsvTagYearReport(fastCulLib)
        print(csvReport)

if args.journalyear:
    # Count how many papers appeared in each jounal in each year.
    # Generate CSV here?  Need to sort it somehow.  X axis should be year.
    # Y axis Journal.  Put the journal with the most all time pubs at the top
    # And also include publisher as we care about BMC.

    for year in fastCulLib.getYears():
        for journal in fastCulLib.getJournals():
            papers = fastCulLib.getPapers(journal=journal, year=year)
            if papers:
                print("year/Journal/nPapers ", year, journal, len(papers))

    print("=====================")

    for journal in fastCulLib.getJournals():
        print("Journal total", journal, len(fastCulLib.getPapers(journal=journal)))
                

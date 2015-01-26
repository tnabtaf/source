#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Generate reports about the Galaxy CiteULike library.
# Reports are generated in both TSV and MoinMoin markup.
#


import argparse

import CiteULike                          # CiteULike Handling


def genMoinTagYearReport(byTagThenYear, byYear):
    """
    Generate a papers by tag and year report in MoinMoin markup.
    Report is returned as a multi-line string.
    """
    # Preprocess. Need to know order of tags and years.
    nTags = len(byTagThenYear)
    years = sorted(byYear.keys())  # years are listed chronologically

    # Count number of papers with each tag
    nPapersWTag = {}
    for tag in byTagThenYear.keys():
        nPapersWTag[tag] = 0
    for tag, tagYears in byTagThenYear.items():
        for year, papers in tagYears.items():
            nPapersWTag[tag] += len(papers)

    # sort tags by paper count, max first
    tagsInCountOrder = [tag for tag in
                        sorted(nPapersWTag.keys(),
                               key=lambda keyValue: - nPapersWTag[keyValue])]

    # no have everything we need; generate report        
    report = []

    # generate header
    report.append('||<|2 class="th"> Year ' +
                  '||<-' + str(nTags) + ' class="th"> Tags ||' +
                  '||<|2 class="th"> # ||\n')

    for tag in tagsInCountOrder:
        report.append('||<class="th"> ' + tag + ' ')
    report.append('||\n')

    # generate yearly numbers
    nPapers = 0
    for year in years:
        nPapersThisYear = len(byYear[year])
        nPapers += nPapersThisYear
        report.append('||<class="th"> ' + year + ' ')
        for tag in tagsInCountOrder:
            if year in byTagThenYear[tag]:
                count = str(len(byTagThenYear[tag][year]))
            else:
                count = ""
            report.append('||<)> ' + count + ' ')
        report.append('||<)> ' + str(nPapersThisYear) + ' ||\n')

    # generate total line at bottom
    report.append('||<class="th"> Total ||<) class="th"> ' +
                  str(nPapers) + ' ')
    for tag in tagsInCountOrder:
        report.append('||<) class="th"> ' + str(nPapersWTag[tag]) + ' ')
    report.append('||\n')

    return("".join(report))
        

class Argghhs(object):
    """
    Process and provide access to command line arguments.
    """

    def __init__(self):
        argParser = argparse.ArgumentParser(
            description="Generate reports for the CiteULike Galaxy library.")
        argParser.add_argument(
            "-c", "--cullib", required=True,
            help="JSON formatted file containing CiteUlike Library; obtained by going to http://www.citeulike.org/json/group/16008")
        argParser.add_argument(
            "--tagyear", required=False, action="store_true",
            help="Produce table showing number of papers with each tag, each year.")
        argParser.add_argument(
            "--moin", required=False, action="store_true",
            help="Produce report(s) using MoinMoin markup")
        argParser.add_argument(
            "--csv", required=False,
            help=("Produce report(s) in CSV format"))
        self.args = argParser.parse_args()

        return(None)


        
# =============================================================
# MAIN

args = Argghhs()                          # process command line arguments
# print str(args.args)

# create database from CiteULike Library.
culLib = CiteULike.CiteULikeLibrary(args.args.cullib)

# Basically want papers categorized by tag and year.  And we'll want a
# way to get papers
#  by year and then tag
#  by tag and then year
# Do we actually care about the papers?  Probably not, but just as easy to
# keep the papers as to keep a count of them.
# So keep papers in tag/year, just as a list.
# then have year be a dict of tags that point the same list.
# and vice versa

byTagThenYear = {}
byYearThenTag = {}
byYear = {}

for paper in culLib.allPapers():
    year = paper.getYear()

    if year == "unknown":
        print("Year UNKNOWN", paper.culJson)
    if year not in byYear:
        byYear[year] = []
        byYearThenTag[year] = {}
    byYear[year].append(paper)
        
    tags = paper.getTags()                # every paper should have tags
    for tag in tags:
        if tag not in byTagThenYear:
            byTagThenYear[tag] = {}         # will be indexed by year
        if year not in byTagThenYear[tag]:
            byTagThenYear[tag][year] = []   # unordered list of papers
            # use the same list that byTagThenYear entry points at.
            byYearThenTag[year][tag] = byTagThenYear[tag][year]
        byTagThenYear[tag][year].append(paper)
    if len(tags) == 0:
        print("Paper missing tags", paper.getTitle(), paper.getCulUrl())


# All papers indexed by [tag][year] and [year][tag]

# Generate them reports

# options are to have one routine per report/format combo, or create a Moin
# report, or a csv report and then have their separate methods do the dirty
# work. Try that.

if args.args.tagyear:
    # report showing papers by tag by year requested.
    if args.args.moin:
        # generate a tag year report in MoinMoin format.
        moinReport = genMoinTagYearReport(byTagThenYear, byYear)
        print(moinReport)
    if args.args.csv:
        # generate tag year data in a tab delimited file
        csvReport = CsvTagYearReport(byTagThenYear)
        print(csvReport)


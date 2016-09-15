#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Program to compare newly reported publications with a library of pubs.
# For each new pub
#   determine if it's already in the publication lib or not.
#   If it's not, generate a bunch of links that will make it easier to add
#   the pub to the library.
#
# This doesn't modify the library at all.  It merely makes it easier for the human
# operator to add the pubs.


import argparse
import getpass

import CiteULike                          # CiteULike Handling
import Matchup                            # Matchup between newly reported papers and what's in CUL
import HistoryDB                          # record what was found in this run
import IMAP                               # Nasty Email handling.
import WOS                                # web of science
import ScienceDirect                      # Science Direct reports
import Springer
import GoogleScholar
import MyNCBI
import Wiley                              # Wileay Online Library Saved Search Alerts

SOURCE_MAPPING = {
    "sciencedirect": ScienceDirect,
    "webofscience":  WOS,
    "springer":      Springer,
    "googlescholar": GoogleScholar,
    "myncbi":        MyNCBI,
    "wiley":         Wiley
    }

PAPERS_MAILBOX = "Papers"

# indexes into tuple for each part
FROM    = 0
SUBJECT = 1

            
class PaperLibrary(object):
    """
    Keeps track of all the new papers/reference, and their match in CUL entries, if any.
    """
    def __init__(self):
        self.byTitleLower = {}
        self.byDoi = {}
        self.by1stAuthorLastNameLower = {}

        # Google truncates titles, but this lib expects full paper titles.
        # Therefore we hack it.
        self.titleLenCaches = {}
        
        return(None)

    def getAllMatchupsGroupedByTitle(self):
        """
        Returns list of all matchups, grouped and indexed by lower case title.
        """
        return(self.byTitleLower)

    def getByDoi(self, doi):
        return(self.byDoi.get(doi))
        
    def addPaper(self, paper):
        """
        Add a paper to the library
        """
        titleLower = paper.getTitleLower()
        if titleLower not in self.byTitleLower:
            # Google is a special case, as they truncate titles. The paper library
            # is not set up for that.
            if type(paper).__name__ == "GSPaper" and paper.titleIsTruncated():
                # see if we have already set up a cache for this length
                truncLen = len(paper.title)
                if truncLen not in self.titleLenCaches:
                    print("      Creating new cache for length: " + str(truncLen))
                    self.titleLenCaches[truncLen] = {}
                    for lowerTitle, paperList in self.byLowerTitle.items():
                        truncLowerTitle = lowerTitle[:min(truncLen, len(lowerTitle))]
                        self.titleLenCaches[truncLen][truncLowerTitle] = papersList
                if titleLower not in self.titleLenCaches[truncLen]:
                    # Longer vesrion of paper does not exist.  Add to cache and to overall list.
                    self.byTitleLower[titleLower] = []
                    self.titleLenCaches[truncLen][titleLower] = self.byTitleLower[titleLower]
            else:
                self.byTitleLower[titleLower] = []
                # add this to any cached entries as well
                for length in self.titleLenCaches:
                    self.titleLenCaches[length][titleLower] = self.byTitleLower[titleLower]
            self.byTitleLower[titleLower].append(paper)
        else:
            self.byTitleLower[titleLower].append(paper)

        if paper.doi:
            if paper.doi not in self.byDoi:
                self.byDoi[paper.doi] = []
            self.byDoi[paper.doi].append(paper)

        firstAuthorLower = paper.getFirstAuthorLastNameLower()
        if firstAuthorLower not in self.by1stAuthorLastNameLower:
            self.by1stAuthorLastNameLower[firstAuthorLower] = []
        self.by1stAuthorLastNameLower[firstAuthorLower].append(paper)

        return(None)

    def verifyConsistentDois(self):
        """
        Confirm that any papers we think are the same, either have the same DOI, or
        don't have a DOI.
        """
        for lowerTitle, papersWithTitle in self.byTitleLower.items():
            doi = None
            for paper in papersWithTitle:
                if paper.doi:
                    if not doi:
                        doi = paper.doi
                    elif doi != paper.doi:
                        print("Papers with same title, don't have same DOIs:<br />")
                        print("  Title: " + paper.title + "<br />")
                        print("  Conflicting DOIs: " + doi + ", " + paper.doi + "<br />")

    def verifyConsistent1stAuthor(self):
        """
        Verify that any papers that we think are the same, either have the same
        first author last name, or no author specified.
        """
        for lowerTitle, papersWithTitle in self.byTitleLower.items():
            author1 = None
            for paper in papersWithTitle:
                firstAuthorForThisPaper = paper.getFirstAuthorLastNameLower()
                if firstAuthorForThisPaper:
                    if not author1:
                        author1 = firstAuthorForThisPaper
                    elif author1 != firstAuthorForThisPaper:
                        print("Papers with same title, don't have same first authors: <br />")
                        print("  Title: " + paper.title + "<br />")
                        print("  Conflicting authors: <br />")
                        print(u"    Author A: '" + author1 + u"' <br />")
                        print(u"    Author B: '" + firstAuthorForThisPaper + u"' <br />")

        
        
class Argghhs(object):
    """
    Process and provide access to command line arguments.
    """

    def __init__(self):
        argParser = argparse.ArgumentParser(
            description="Given a list of data sources for papers, generate a report showing which papers are possibly new, and which papers we already have in CiteULike.")
        argParser.add_argument(
            "-c", "--cullib", required=True,
            help="JSON formatted file containing CiteUlike Library; obtained by going to http://www.citeulike.org/json/group/16008")
        argParser.add_argument(
            "-e", "--email", required=True,
            help="Email account to pull notifications from")
        argParser.add_argument(
            "--sentsince", required=True,
            help=("Only look at email sent after this date." +
                    " Format: DD-Mon-YYYY.  Example: 01-Dec-2014."))
        argParser.add_argument(
            "--sentbefore", required=False,
            help=("Optional. Only look at email sent before this date." +
                    " Format: DD-Mon-YYYY.  Example: 01-Jan-2015."))
        argParser.add_argument(
            "--sources", required=True,
            help="Which alert sources to process. Is either 'all' or comma-separated list: sciencedirect,webofscience,myncbi,wiley,googlescholar")
        argParser.add_argument(
            "--historyin", required=False,
            help="Read in history of previous run. Tells you what you've seen before.")
        argParser.add_argument(
            "--historyout", required=False,
            help="Create a history of this run in CSV format as well.")
        self.args = argParser.parse_args()

        # split comma separated list of sources
        self.sources = self.args.sources.split(",")
        
        return(None)





    
# MAIN

args = Argghhs()                          # process command line arguments
# print str(args.args)

# create database from CiteULike Library.
culLib = CiteULike.CiteULikeLibrary(args.args.cullib)

history = None

if args.args.historyin:
    # read in history of previous run
    history = HistoryDB.HistoryDB(args.args.historyin)

# Now build a library of newly reported papers.
papers = PaperLibrary()

# connect to email source
gmail = IMAP.GMailSource(args.args.email, getpass.getpass())



# Need to rationalise this before it prliferates any more. But not today.

# Process ScienceDirect emails
sdSearch = IMAP.buildSearchString(sender = ScienceDirect.SD_SENDER,
                                  sentSince = args.args.sentsince,
                                  sentBefore = args.args.sentbefore)
for email in gmail.getEmails(PAPERS_MAILBOX, sdSearch):
    sdEmail = ScienceDirect.SDEmail(email)
    for paper in sdEmail.getPapers():
        paper.search = sdEmail.getSearch()
        papers.addPaper(paper)

# Process Web Of Science emails
wosSearch = IMAP.buildSearchString(sender = WOS.WOS_SENDER,
                                   sentSince = args.args.sentsince,
                                   sentBefore = args.args.sentbefore)
for email in gmail.getEmails(PAPERS_MAILBOX, wosSearch):
    wosEmail = WOS.WOSEmail(email)
    for paper in wosEmail.getPapers():
        paper.search = wosEmail.getSearch()
        papers.addPaper(paper)

# Process My NCBI emails
myNCBISearch = IMAP.buildSearchString(sender = MyNCBI.MYNCBI_SENDER,
                                    sentSince = args.args.sentsince,
                                    sentBefore = args.args.sentbefore)
for email in gmail.getEmails(PAPERS_MAILBOX, myNCBISearch):
    myNCBIEmail = MyNCBI.MyNCBIEmail(email)
    for paper in myNCBIEmail.getPapers():
        paper.search = myNCBIEmail.getSearch()
        papers.addPaper(paper)

# Process Wiley Emails
wileySearch = IMAP.buildSearchString(sender = Wiley.WILEY_SENDER,
                                    sentSince = args.args.sentsince,
                                    sentBefore = args.args.sentbefore)
for email in gmail.getEmails(PAPERS_MAILBOX, wileySearch):
    wileyEmail = Wiley.WileyEmail(email)
    for paper in wileyEmail.getPapers():
        paper.search = wileyEmail.getSearch()
        papers.addPaper(paper)

        
# Process Google Scholar emails last because of truncated titles
gsSearch = IMAP.buildSearchString(sender = GoogleScholar.GS_SENDER,
                                  sentSince = args.args.sentsince,
                                  sentBefore = args.args.sentbefore)
for email in gmail.getEmails(PAPERS_MAILBOX, gsSearch):
    gsEmail = GoogleScholar.GSEmail(email)
    for paper in gsEmail.getPapers():
        paper.search = gsEmail.getSearch()
        papers.addPaper(paper)


        
# All papers from all emails read
papers.verifyConsistentDois()      # all papers with same title, have the same (or no) DOI
papers.verifyConsistent1stAuthor() # same, but different

# Now compare new pubs with existing CUL lib.  Using title, because everything has a title
# A problem to address DOIs vs DOI URLs


byLowerTitle = {}

for lowerTitle, papersWithTitle in papers.getAllMatchupsGroupedByTitle().items():
    
    # Match by DOI first, if possible.
    doi = Matchup.getDoiFromPaperList(papersWithTitle)

    culPaper = culLib.getByDoi(doi)
    if culPaper:                # Can Match by DOI; already have paper
        # print("Matching on DOI")
        byLowerTitle[lowerTitle] = Matchup.Matchup(papersWithTitle, [culPaper])
    else:
        culPapers = culLib.getByTitleLower(lowerTitle)
        if culPapers:           # Matching by Title; already have paper
            # TODO: also check first author, pub?
            # print("Matched by title")
            byLowerTitle[lowerTitle] = Matchup.Matchup(papersWithTitle, culPapers)
        else:                      # Appears New
            # print("New paper")
            byLowerTitle[lowerTitle] = Matchup.Matchup(papersWithTitle, None)


# Get the papers in Lower Title order

sortedTitles = sorted(byLowerTitle.keys())
    
for title in sortedTitles:
    try:
        print(Matchup.reportPaper(byLowerTitle[title], history))

    except (UnicodeEncodeError, UnicodeDecodeError) as err:
        print("Encode Error.")
        for c in err.object[err.start:err.end]:
            print(hex(ord(c)))
        print("Encoding:", err.encoding)
        print("Reason:", err.reason)
        
if args.args.historyout:
    HistoryDB.writeHistory(byLowerTitle, sortedTitles, args.args.historyout)
            

    

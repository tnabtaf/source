#!/usr/bin/python
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
import urllib
import yattag

import CiteULike                          # CiteULike Handling
import IMAP                               # Nasty Email handling.
import WOS                                # web of science
import ScienceDirect                      # Science Direct reports
import GoogleScholar

PAPERS_MAILBOX = "Papers"

# indexes into tuple for each part
FROM    = 0
SUBJECT = 1

class Matchup(object):
    """
    Pairs titles (and the list of papers with that title) and CUL entry
    """

    def __init__(self, papers, culEntry):

        self.papers = papers
        self.culEntry = culEntry          # might be None
        self.lowerTitle = papers[0].getTitleLower()
        return None
            
class PaperLibrary(object):
    """
    Keeps track of all the new papers/reference, and their matchin CUL entries, if any.
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
                        print("Papers with same title, don't have same DOIs:")
                        print("Title: " + paper.title)
                        print("Conflicting DOIs: " + doi + ", " + paper.doi)

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
                        print("Papers with same title, don't have same first authors:")
                        print("Title: " + paper.title)
                        print("Conflicting authors: '" + author1 + "', '" +
                              firstAuthorForThisPaper + "'")

        
        
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
        self.args = argParser.parse_args()

        return(None)


def getDoiFromPaperList(paperList):
    """
    List is assumed to have been pre-verified to have consistent DOIs
    """
    for paper in paperList:
        if paper.doi:
            return(paper.doi)
    return(None)

def getUrlFromPaperList(paperList):
    """
    Extract a URL from paper list.  Favor DOI URLs, and then fallback to others
    if needed.
    List is assumed to have been pre-verified to have consistent DOIs
    """
    doiUrl = getDoiFromPaperList(paperList)
    if not doiUrl:  
        for paper in paperList:
            if paper.url:
                return(paper.url)

    return(doiUrl)


def createReport(matchupsByLowTitle, sectionTitle):
    
    doc, tag, text = yattag.Doc().tagtext()

    with tag("h2"):
        text(sectionTitle)

    for matchup in matchupsByLowTitle.values():

        with tag("h3"):
            text(matchup.papers[0].title)

        with tag("ol"):
            for paper in matchup.papers:
                with tag("li"):
                    text(paper.search)
                    with tag("ul"):
                        with tag("li"):
                            text(paper.authors)
                        if paper.doi:
                            with tag("li"):
                                with tag("a", href=paper.doiUrl, target="_blank"):
                                    text(paper.doi)
                        with tag("li"):
                            text(paper.source)
                        with tag("li"):
                            text(paper.title)

        if matchup.culEntry:
            with tag("p"):
                with tag("a", href=matchup.culEntry.getCulUrl()):
                    text("Paper @ CiteULike")
        else:
            with tag("ul"):
                url = getUrlFromPaperList(matchup.papers)
                if url:
                    # Got a url, post it to CiteULike, and link to it.
                    with tag("li"):
                        with tag("a", href="http://www.citeulike.org/posturl?url=" + url,
                                target="citeulike"):
                            text("Submit to CiteULike")
                    with tag("li"):
                        with tag("a", href=url, target="paper"):
                            text("See paper")
                            
                # Search for it at Hopkins, Google, too
                with tag("li"):
                    with tag("a",
                             href="https://catalyst.library.jhu.edu/?utf8=%E2%9C%93&search_field=title&" +
                             urllib.urlencode({"q": matchup.lowerTitle}),
                             target="jhulib"):
                        text("Search Hopkins")
                    
                with tag("li"):
                    with tag("a",
                             href="https://www.google.com/search?q=" + matchup.lowerTitle,
                             target="googletitlesearch"):
                        text("Search Google")
                        
    print(yattag.indent(doc.getvalue()))

    return(None)


# MAIN

args = Argghhs()                          # process command line arguments
# print str(args.args)

# create database from CiteULike Library.
culLib = CiteULike.CiteULikeLibrary(args.args.cullib)

# Now build a library of newly reported papers.
papers = PaperLibrary()

# connect to email source
gmail = IMAP.GMailSource(args.args.email, getpass.getpass())


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

oldByLowerTitle = {}
newByLowerTitle = {}

for lowerTitle, papersWithTitle in papers.getAllMatchupsGroupedByTitle().items():
    
    # Match by DOI first, if possible.
    doi = getDoiFromPaperList(papersWithTitle)

    culPaper = culLib.getByDoi(doi)
    if culPaper:                # Can Match by DOI; already have paper
        # print("Matching on DOI")
        oldByLowerTitle[lowerTitle] = Matchup(papersWithTitle, culPaper)
    else:
        culPaper = culLib.getByTitleLower(lowerTitle)
        if culPaper:           # Matching by Title; already have paper
            # TODO: also check first author, pub?
            # print("Matched by title")
            oldByLowerTitle[lowerTitle] = Matchup(papersWithTitle, culPaper)
        else:                      # Appears New
            # print("New paper")
            newByLowerTitle[lowerTitle] = Matchup(papersWithTitle, None)
        
# print("======================")

createReport(newByLowerTitle, "New Papers")
createReport(oldByLowerTitle, "Existing Papers")


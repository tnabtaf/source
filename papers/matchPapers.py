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
import urllib.parse
import yattag

import CiteULike                          # CiteULike Handling
import IMAP                               # Nasty Email handling.
import WOS                                # web of science
import ScienceDirect                      # Science Direct reports
import Springer
import GoogleScholar
import MyNCBI
import Wiley                              # Wileay Online Library Saved Search Alerts

PAPERS_MAILBOX = "Papers"

# indexes into tuple for each part
FROM    = 0
SUBJECT = 1

class Matchup(object):
    """
    Pairs titles (and the list of papers with that title) and CUL entries with that title
    """

    def __init__(self, papers, culEntries):

        self.papers = papers
        self.culEntries = culEntries          # might be None
        self.lowerTitle = papers[0].getTitleLower()
        self.title = papers[0].getTitle()
        return None

    def debugPrint(self, descrip="", indent=""):
        print(indent + "DEBUG: Matchup: " + descrip)
        print(indent + "  lowerTitle: " + self.lowerTitle)
        print(indent + "  title: " + self.title)
        print(indent + "  papers: ")
        for paper in self.papers:
            paper.debugPrint(indent=indent + "  ")
        print(indent + "  culEntries: ")
        if self.culEntries:
            for culEntry in self.culEntries:
                culEntry.debugPrint(indent=indent + "  ")
        print(indent + "  DONE")
        return(None)

            
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

def getDoiUrlFromPaperList(paperList):
    """
    List is assumed to have been pre-verified to have consistent DOIs
    """
    for paper in paperList:
        if paper.doiUrl:
            return(paper.doiUrl)
    return(None)

def getUrlFromPaperList(paperList):
    """
    Extract a URL from paper list.  Favor DOI URLs, and then fallback to others
    if needed.
    List is assumed to have been pre-verified to have consistent DOIs
    """
    doiUrl = getDoiUrlFromPaperList(paperList)
    if not doiUrl:  
        for paper in paperList:
            if paper.url:
                return(paper.url)

    return(doiUrl)

def getHopkinsUrlFromPaperList(paperList):
    """
    Extract a Hopkins specific URL from paper list.  
    Not all sources have this.
    """
    hopkinsUrl = None
    for paper in paperList:
        if paper.hopkinsUrl:
            return(paper.hopkinsUrl)
        elif Wiley.isWileyUrl(paper.url):
            # Some wiley comes from other searches.
            return(Wiley.createHopkinsUrl(paper.url))
        elif Springer.isSpringerUrl(paper.url):
            return(Springer.createHopkinsUrl(paper.url))
        elif paper.url and not hopkinsUrl:
            urlParts = paper.url.split("/")
            hopkinsUrl = "/".join(urlParts[0:3]) + ".proxy1.library.jhu.edu/" + "/".join(urlParts[3:])
    return(hopkinsUrl)

def createReport(matchupsByLowTitle, sectionTitle):
    """
    Return an HTML report of what needs to be done.
    """
    
    doc, tag, text = yattag.Doc().tagtext()

    with tag("h2", style="width: 100%; background-color: #eeeeff"):
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

        if matchup.culEntries:
            for culEntry in matchup.culEntries:
                with tag("p"):
                    with tag("a", href=culEntry.getCulUrl()):
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

                hopkinsUrl = getHopkinsUrlFromPaperList(matchup.papers)
                if hopkinsUrl:
                    with tag("li"):
                        with tag("a", href=hopkinsUrl, target="paperhopkins"):
                            text("See paper @ Hopkins")
                            
                # Search for it at Hopkins; Google and pubmed too
                with tag("li"):
                    with tag("a",
                             href="https://catalyst.library.jhu.edu/?utf8=%E2%9C%93&search_field=title&" +
                             urllib.parse.urlencode({"q": matchup.title}),
                             target="jhulib"):
                        text("Search Hopkins")
                    
                with tag("li"):
                    with tag("a",
                             href="https://www.google.com/search?q=" + matchup.title,
                             target="googletitlesearch"):
                        text("Search Google")
                        
                with tag("li"):
                    with tag("a",
                             href="http://www.ncbi.nlm.nih.gov/pubmed/?term=" + matchup.title,
                             target="pubmedtitlesearch"):
                        text("Search Pubmed")
                        
    reportHtml = yattag.indent(doc.getvalue())

    # do some cleanup
    # fix a problem with some Google Scholar URLs.  Google Scholar does not like &amp; in place of &
    reportHtml = reportHtml.replace("&amp;", "&")   # potentially risky outside of URLs
    
    return(reportHtml)


def reportPaper(matchup):
    """
    Return HTML report for this matchup
    """
    
    doc, tag, text = yattag.Doc().tagtext()

    newPaper = not matchup.culEntries
    
    if newPaper:
        # reported paper already in CiteULike
        bgColor = "#eef"
        fontColor = "#000"
        leader = "New:"
        hLevel = "h2"
 
    else:
        # report paper is new
        bgColor = "#ccc"
        fontColor = "#666"
        leader = "Known:"
        hLevel = "h3"
        
    with tag("div", style="width: 100%; color: " + fontColor + "; background-color: " + bgColor):

        with tag(hLevel):
            text(leader)
            with tag("br"):
                pass
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

        if not newPaper:
            for culEntry in matchup.culEntries:
                with tag("p"):
                    with tag("a", href=culEntry.getCulUrl()):
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

                hopkinsUrl = getHopkinsUrlFromPaperList(matchup.papers)
                if hopkinsUrl:
                    with tag("li"):
                        with tag("a", href=hopkinsUrl, target="paperhopkins"):
                            text("See paper @ Hopkins")
                            
                # Search for it at Hopkins; Google and pubmed too
                with tag("li"):
                    with tag("a",
                             href="https://catalyst.library.jhu.edu/?utf8=%E2%9C%93&search_field=title&" +
                             urllib.parse.urlencode({"q": matchup.title}),
                             target="jhulib"):
                        text("Search Hopkins")
                    
                with tag("li"):
                    with tag("a",
                             href="https://www.google.com/search?q=" + matchup.title,
                             target="googletitlesearch"):
                        text("Search Google")
                        
                with tag("li"):
                    with tag("a",
                             href="http://www.ncbi.nlm.nih.gov/pubmed/?term=" + matchup.title,
                             target="pubmedtitlesearch"):
                        text("Search Pubmed")

    reportHtml = yattag.indent(doc.getvalue())

    # do some cleanup
    # fix a problem with some Google Scholar URLs.  Google Scholar does not like &amp; in place of &
    reportHtml = reportHtml.replace("&amp;", "&")   # potentially risky outside of URLs
    
    return(reportHtml)


    
# MAIN

args = Argghhs()                          # process command line arguments
# print str(args.args)

# create database from CiteULike Library.
culLib = CiteULike.CiteULikeLibrary(args.args.cullib)

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
    doi = getDoiFromPaperList(papersWithTitle)

    culPaper = culLib.getByDoi(doi)
    if culPaper:                # Can Match by DOI; already have paper
        # print("Matching on DOI")
        byLowerTitle[lowerTitle] = Matchup(papersWithTitle, [culPaper])
    else:
        culPapers = culLib.getByTitleLower(lowerTitle)
        if culPapers:           # Matching by Title; already have paper
            # TODO: also check first author, pub?
            # print("Matched by title")
            byLowerTitle[lowerTitle] = Matchup(papersWithTitle, culPapers)
        else:                      # Appears New
            # print("New paper")
            byLowerTitle[lowerTitle] = Matchup(papersWithTitle, None)

# Get the papers in Lower Title order

sortedTitles = sorted(byLowerTitle.keys())

for title in sortedTitles:
    try:
        print(reportPaper(byLowerTitle[title]))
    except (UnicodeEncodeError, UnicodeDecodeError) as err:
        print("Encode Error.")
        for c in err.object[err.start:err.end]:
            print(hex(ord(c)))
        print("Encoding:", err.encoding)
        print("Reason:", err.reason)
        
            

    

#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Information about alerts from My NCBI


import re
import alert
import HTMLParser
import DamnUnicode

MYNCBI_SENDER = "efback@mail.nih.gov"

class MyNCBIPaper(alert.PaperAlert, HTMLParser.HTMLParser):
    """
    Describe a particular paper being reported by My NCBI alert
    """

    def __init__(self):
        """

        """
        super(alert.PaperAlert,self).__init__()
        HTMLParser.HTMLParser.__init__(self)
        
        self.title = ""
        self.authors = ""
        self.source = ""
        self.doiUrl = ""
        self.doi = ""
        self.url = ""
        self.search = "My NCBI: "
        return None
        
    def getFirstAuthorLastName(self):
        """
        Guillemi EC, Ruybal P, Lia V, Gonzalez S, Lew S, Zimmer P, Arias LL, Rodriguez JL
        This will mess up on van Drysdale etc.
        """
        if self.authors:
            return(self.authors.split(",")[0].split(" ")[0])
        else:
            return None

    def getFirstAuthorLastNameLower(self):
        firstAuthor = self.getFirstAuthorLastName()
        if firstAuthor:
            firstAuthor = firstAuthor.lower()
        return firstAuthor


        
class MyNCBIEmail(alert.Alert, HTMLParser.HTMLParser):
    """
    All the information in a Science Direct Email alert.

    Parse HTML email body from ScienceDirect.  The body maybe reporting more
    than one paper.
    """
    searchStartRe = re.compile(r'Access (the|all \d+) new result[s]*')

    def __init__(self, email):

        HTMLParser.HTMLParser.__init__(self)

        self.papers = []
        self.search = "My NCBI: "
        self.currentPaper = None
        
        self.inSearch = False
        self.inSearchText = False
        self.inTitle = False
        self.expectingAuthors = False
        self.inAuthors = False
        self.inSource = False
        self.inSourceDetails = False
        
        self.feed(email.getBodyText()) # process the HTML body text.
        
        return None
        
    def handle_data(self, data):

        data = data.strip()

        if data == "Search:":
            self.inSearch = True
        elif self.inSearchText:
            self.search += data
            self.inSearchText = False
        elif self.inTitle:
            self.currentPaper.title = data[0:-1] # clip trailing .
            self.inTitle = False
            self.expectingAuthors = True
        elif self.inAuthors:
            self.currentPaper.authors = data[0:-1] # clip trailing .
            self.inAurhors = False
        elif self.inSourceDetails:
            # volume number, DOI
            parts = data.split(" doi:")
            self.currentPaper.source += parts[0][1:] # clip leading .
            if len(parts) == 2:
                self.currentPaper.doi = parts[1][0:-1] # clip trailing .
            self.inSourceDetails = False

        return(None)
            
    def handle_starttag(self, tag, attrs):

        if self.inSearch and tag == "b":
            self.inSearchText = True
            self.inSearch = False
        elif tag == "a" and attrs[1][0] == "ref":
            self.currentPaper = MyNCBIPaper()
            self.papers.append(self.currentPaper)
            self.currentPaper.url = attrs[0][0]
            self.inTitle = True
        elif tag == "td" and self.expectingAuthors:
            self.expectingAuthors = False
            self.inAuthors = True
        elif tag == "span" and attrs[0][0] == "class" and attrs [0][1] == "jrnl":
            self.source = attrs[1][1] # Title tag has better jrnl name than display
            self.inSource = True
            
        return (None)

    def handle_endtag(self, tag):

        if tag == "span" and self.inSource:
            self.inSource = False
            self.inSourceDetails = True
            
        return (None)
    
    def handle_startendtag(self, tag, attrs):
        """
        Process tags like IMG and BR that don't have end tags.
        """
        return(None)
        
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

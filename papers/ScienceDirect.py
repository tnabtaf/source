#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Information about a ScienceDirect reference / Citation


import re
import alert
import base64
import HTMLParser
import DamnUnicode

SD_SENDER = "salert@prod.sciencedirect.com"

SD_JHU_PII_URL = "http://www.sciencedirect.com.proxy1.library.jhu.edu/science/article/pii/"
SD_PII_URL = "http://www.sciencedirect.com/science/article/pii/"

class SDPaper(alert.PaperAlert, HTMLParser.HTMLParser):
    """
    Describe a particular paper being reported by ScienceDirect
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
        self.search = "ScienceDirect: "
        return None
        
    def getFirstAuthorLastName(self):
        """
        Dita Musalkova, Jakub Minks, Gabriela Storkanova, Lenka Dvorakova
        This will mess up on van Drysdale etc.
        """
        if self.authors:
            return(self.authors.split(",")[0].split(" ")[-1])
        else:
            return None

    def getFirstAuthorLastNameLower(self):
        firstAuthor = self.getFirstAuthorLastName()
        if firstAuthor:
            firstAuthor = firstAuthor.lower()
        return firstAuthor


        
class SDEmail(alert.Alert, HTMLParser.HTMLParser):
    """
    All the information in a Science Direct Email alert.

    Parse HTML email body from ScienceDirect.  The body maybe reporting more
    than one paper.
    """
    searchStartRe = re.compile(r'Access (the|all \d+) new result[s]*')

    def __init__(self, email):

        HTMLParser.HTMLParser.__init__(self)

        self.papers = []
        self.search = "ScienceDirect: "
        self.currentPaper = None
        
        self.inSearch = False
        self.inTitleLink = False
        self.inTitleText = False
        self.inTitleTextSpanDepth = 0
        self.afterTitleBeforeSource = False
        self.inSource = False
        self.afterSourceBeforeAuthors = False
        self.inAuthors = False

        # SD email body content is base64 encoded.  Decode it.
        emailBodyText = base64.standard_b64decode(email.getBodyText())
        # print(emailBodyText)
        self.feed(emailBodyText) # process the HTML body text.
        
        return None
        
    def handle_data(self, data):

        data = data.strip()

        startingSearch = SDEmail.searchStartRe.match(data)
        if startingSearch:
            self.inSearch = True
        elif self.inSearch:
            self.search += data
            self.inSearch = False
        elif self.inTitleText:
            self.currentPaper.title += DamnUnicode.cauterizeWithDecode(data) + " "
        elif self.inSource:
            self.currentPaper.source = data
            self.inSource = False
            self.afterSourceBeforeAuthors = True
        elif self.inAuthors:
            self.currentPaper.authors = DamnUnicode.cauterizeWithDecode(data)
            self.inAuthors = False
        return(None)
            
    def handle_starttag(self, tag, attrs):

        if tag == "td" and attrs[0][0] == "class" and attrs[0][1] == "txtcontent":
            """
            Paper has started; next tag is an anchor, and it has paper URL
            We now have a long URL that points to a public HTML version of
            the paper.  We don't have a doi. But we will have a title shortly.
            Should we use the URL to get the DOI?  Or will sciencedirect
            just always be title match?
            ScienceDirect has an API we could use to extract the DOI, or we
            could putll it from the HTML page.
            For now, go with title only match
            """
            self.inTitleLink = True
            self.currentPaper = SDPaper()
            self.papers.append(self.currentPaper)

        elif tag == "a" and self.inTitleLink:
            fullUrl = attrs[0][1]
            urlArgs = fullUrl.split("&")
            for urlArg in urlArgs:
                if urlArg[0:8] == "_piikey=":
                    self.currentPaper.url = SD_PII_URL + urlArg[8:]
                    break
            inTitleLink = False
        
        elif tag == "span" and attrs[0][0] == "class" and attrs[0][1] == "artTitle":
            self.inTitleText = True
            self.inTitleTextSpanDepth = 1
        elif self.inTitleText and tag == "span":
            self.inTitleTextSpanDepth += 1
        elif tag == "i" and self.afterTitleBeforeSource:
            self.inSource = True
            self.afterTitleBeforeSource = False

        elif tag == "span" and attrs[0][0] == "class" and attrs[0][1] == "authorTxt":
            self.inAuthors = True
            self.afterSourceBeforeAuthors = False

            
        return (None)

    def handle_endtag(self, tag):

        if self.inTitleText and tag == "span":
            self.inTitleTextSpanDepth -= 1
            if self.inTitleTextSpanDepth == 0:
                self.inTitleText = False
                self.afterTitleBeforeSource = True
                self.currentPaper.title = self.currentPaper.title.strip()
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
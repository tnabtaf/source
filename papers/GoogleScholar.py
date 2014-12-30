#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Information about alert from Google Scholar


import re
import alert
import quopri                             # Quoted printable encoding
import HTMLParser

GS_SENDER = "scholaralerts-noreply@google.com"

ELLIPSIS_TAIL = "  " + unichr(8230)  #"  &hellip;"
ELLIPSIS_TAIL_LEN = len(ELLIPSIS_TAIL)

#SD_JHU_PII_URL = "http://www.sciencedirect.com.proxy1.library.jhu.edu/science/article/pii/"
#SD_PII_URL = "http://www.sciencedirect.com/science/article/pii/"

class GSPaper(alert.PaperAlert, HTMLParser.HTMLParser):
    """
    Describe a particular paper being reported by Google Scholar
    """

    def __init__(self):
        """

        """
        super(alert.PaperAlert,self).__init__()
        HTMLParser.HTMLParser.__init__(self)
        
        self.title = ""
        self.titleTruncated = False
        self.authors = ""
        self.source = ""
        self.doiUrl = ""
        self.doi = ""
        self.url = ""
        self.search = "Google "
        return None
        
    def getFirstAuthorLastName(self):
        """
        DM Meinel, G Margos, R Konrad, S Krebs, H Blum ...
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

    def titleIsTruncated(self):
        return self.titleTruncated


class GSEmail(alert.Alert, HTMLParser.HTMLParser):
    """
    All the information in a Google Scholar Email alert.

    Parse HTML email body from Google Scholar.  The body may be reporting more
    than one paper.
    """
    searchStartRe = re.compile(r'Scholar Alert: ')

    def __init__(self, email):

        HTMLParser.HTMLParser.__init__(self)

        self.papers = []
        self.search = "Google "
        self.currentPaper = None

        self.inSearch = False
        self.inTitleLink = False
        self.inTitleText = False
        self.inAuthorList = False

        # Google Scholar email body content is Quoted Printable encoded.  Decode it.
        emailBodyText = quopri.decodestring(email.getBodyText()).decode('utf-8').encode('utf-8')
        self.feed(emailBodyText) # process the HTML body text.
        
        return None
        
    def handle_data(self, data):

        data = data.strip()

        startingSearch = GSEmail.searchStartRe.match(data)
        if startingSearch:
            self.search += data
            self.inSearch = True

        elif self.inSearch:
            self.search += " " + data

        elif self.inTitleText and data:
            self.currentPaper.title = data
            if self.currentPaper.title[- ELLIPSIS_TAIL_LEN:] == ELLIPSIS_TAIL:
                # clip it, title will be only a partial match.
                self.currentPaper.title = self.currentPaper.title[0:- ELLIPSIS_TAIL_LEN]
                self.currentPaper.titleTruncated = True
                print("Clipped: " + self.currentPaper.title)

            # Fix title, stripping thing yattag can't cope with.
            self.currentPaper.title = self.currentPaper.title.decode("utf-8").replace(u'\u2022', "*")
            self.currentPaper.title = self.currentPaper.title.replace(u'\u2013', "-")
            self.currentPaper.title = self.currentPaper.title.replace(u'\u00F6', "o")
            self.currentPaper.title = self.currentPaper.title.replace(u'\u00E4', "a")
            self.currentPaper.title = self.currentPaper.title.replace(u'\u2010', "-")
            self.inTitleText = False
            self.inAuthorList = True

        elif self.inAuthorList and data:
            # Author list may also have source at end
            parts = data.split(" - ")
            self.currentPaper.author = parts[0]
            if len(parts) == 2:
                self.currentPaper.source = parts[1]
            self.inAuthorList = False

        return(None)
            
    def handle_starttag(self, tag, attrs):
        
        if tag == "h3":
            # link to paper is shown in h3.
            self.inTitleLink = True
            self.currentPaper = GSPaper()
            self.papers.append(self.currentPaper)
            self.currentPaper.search = self.search
            
        elif tag == "a" and self.inTitleLink:
            fullUrl = attrs[0][1]
            urlArgs = fullUrl.split("&")
        
            for urlArg in urlArgs:
                if urlArg[0:2] == "q=":
                    self.currentPaper.url = urlArg[2:]
                    break
            self.inTitleLink = False
            self.inTitleText = True
            
        return (None)

    def handle_endtag(self, tag):

        if tag == "b" and self.inSearch:
            self.inSearch = False
            
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

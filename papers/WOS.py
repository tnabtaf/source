#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Information about a Web of Science reference / Citation


import re
import alert
import HTMLParser

WOS_SENDER = "noreply@isiknowledge.com"


class WOSPaper(alert.PaperAlert):
    """
    Describe a particular paper being reported by Web of Science
    """

    def __init__(self):
        """
        Next thing is get DOIs and sources, clean up auhors,
        """
        self.title = ""
        self.authors = ""
        self.source = ""
        self.doiUrl = ""
        self.doi = ""
        self.url = ""
        self.search = "WoS: "
        return None

    def getTitleLower(self):
        return(self.title.lower())
        
    def getFirstAuthorLastName(self):
        if self.authors:
            return(self.authors[0].split()[-1])
        else:
            return None

    def getFirstAuthorLastNameLower(self):
        firstAuthor = self.getFirstAuthorLastName()
        if firstAuthor:
            firstAuthor = firstAuthor.lower()
        return firstAuthor


        
class WOSEmail(alert.Alert, HTMLParser.HTMLParser):
    """
    All the information in a Web of Science Email.

    Parse HTML email body from Web Of Science. The body maybe reporting more than one
    paper.
    """

    paperStartRe = re.compile(r'Record \d+ of \d+\.')

    def __init__(self, email):

        alert.Alert.__init__(self)
        HTMLParser.HTMLParser.__init__(self)
        
        self.inTitle = False
        self.inTitleValue = False
        self.inAuthors = False
        self.inCitedArticle = False
        self.inCitedArticleValue = False
        self.inSource = False

        self.feed(email.getBodyText()) # process the HTML body text.

        return None
        
    def handle_data(self, data):

        data = data.strip()
        # print("In handle_data: " + data)
        starting = WOSEmail.paperStartRe.match(data)
        if starting:
            # Each paper starts with: "Record m of n. "
            self.current = WOSPaper()
            self.papers.append(self.current) 
            
        elif data == "Title:":
            self.inTitle = True
            # print("Set inTitle")

        elif data == "Authors:":
            self.inAuthors = True

        elif data[0:14] == "Cited Article:":
            self.inCitedArticle = True
            # print("Set inCitedArticle")
            
        elif data == "Source:":
            self.inSource = True

        elif data == "Language:":
            self.inSource = False
            
        elif self.inTitleValue:
            self.current.title = data
            # print("Set Title= " + self.title)

        elif self.inAuthors:
            self.current.authors = data
            self.inAuthors = False

        elif self.inCitedArticleValue:
            self.search += data
            self.inCitedArticle = False
            self.inCitedArticleValue = False
            # print("Set Search: " + self.search)

        elif self.inSource:
            self.current.source += data + " "
            
    def handle_starttag(self, tag, attrs):

        # print("In handle_starttag: " + tag)
        if self.inTitle and tag == "value":
            self.inTitleValue = True
            # print("Set inTitleValue")
            
        elif self.inCitedArticle and tag == "font":
            self.inCitedArticleValue = True
            
        elif self.inSource and tag == "a":
            self.current.doiUrl = attrs[0][1]
            self.current.doi = self.current.doiUrl[18:]
                

    def handle_endtag(self, tag):

        # print("In handle_endtag: " + tag)
        if self.inTitleValue and tag == "value":
            # print("Clearing inTitleValue, inTitle")
            self.inTitleValue = False
            self.inTitle = False
            
        elif self.inCitedArticleValue and tag == "font":
            self.inCitedArticleValue = False
            self.inCitedArticle = False

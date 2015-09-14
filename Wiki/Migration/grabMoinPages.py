#!/usr/bin/python
#
# Walk an existing MoinMoin wiki, and download the wiki markup source for all pages.
# This assumes a 1.9.x MoinMoin wiki

import argparse
import urllib                             # copying from web to filesystem
import urllib2                            # HTTP access
import HTMLParser                         #
import os
import os.path
import time                               # I need sleep


ALL_PAGES = "TitleIndex"                  # links to all pages we can see
GET_SOURCE = "?action=raw"                # URL addendum to request Moin source
SLEEP_INTERVAL = 10                       # # secs to sleep between requests


class MoinPageList (HTMLParser.HTMLParser):
    """
    The HTML page listing all the pages on a MoinMoin Wiki.
    """

    def __init__(self, htmlText):

        HTMLParser.HTMLParser.__init__(self)

        self.inPageList = False           # once true, stays true 
        self.inPageLink  = False          # Only true in <a> tag
        self.destDir = None
        self.onlyNew = False
        self.htmlText = htmlText
        self.urlOpener = urllib.URLopener()

        return (None)


    def copyPages(self):
        """
        Copy pages from wiki site to local filesystem.
        Copies them as Moin markup.
        """
        self.feed(self.htmlText)        # process the HTML text; copying each file over

        return(None)

        
    def handle_starttag(self, tag, attrs):
        if tag == "h2":
            self.inPageList = True        # page links section has started
        elif tag == "li" and self.inPageList:
            self.inPageLink = True
        elif tag == "a" and self.inPageLink: 
            # build a page URL, then get it's Moin source
            pageUrl = self.baseWikiUrl + attrs[0][1] + GET_SOURCE
            pageFilePath = self.destDir + '/' + attrs[0][1] + ".moin"

            pageFileDir = os.path.dirname(pageFilePath)
            if not os.path.exists(pageFileDir):
                os.makedirs(pageFileDir)
            if (not os.access(pageFilePath, os.F_OK)) or (not self.onlyNew):
                # get, write Moin source    
                print pageUrl
                self.urlOpener.retrieve(pageUrl, pageFilePath)

                # avoid detection as a bad player
                time.sleep(SLEEP_INTERVAL)
            
        return(None)


    def handle_data(self, data):

        #print data

        return(None)

    def handle_endtag(self, tag):
        if tag == "a":
            self.inPageLink = False
        return(None)


class Argghhs(object):
    """
    Process and provide access to command line arguments.
    """

    def __init__(self):
        argParser = argparse.ArgumentParser(
            description='Pull all the pages from the MoinMoin Wiki.  Prints the URL of any copied page.',
            epilog = 'Example:\n    grabMoinPages.py --destdir="MoinPages" --onlynew --basewikiurl="https://wiki.galaxyproject.org/"')
        argParser.add_argument(
            "--basewikiurl", required=True,
            help="The base URL of the Moin wiki to copy")
        argParser.add_argument(
            "--destdir", required=True,
            help="Path to directory to copy pages into")
        argParser.add_argument(
            "--onlynew", required=False, action="store_true",
            help="Only get pages you don't already have a copy of")
        self.args = argParser.parse_args()

        return(None)

args = Argghhs()
        
                
# Get the HTML for page listing all pages in wiki
pageHtml = urllib2.urlopen(args.args.basewikiurl + ALL_PAGES).read()

moinPageList = MoinPageList(pageHtml)
moinPageList.destDir = args.args.destdir
moinPageList.onlyNew = args.args.onlynew
moinPageList.baseWikiUrl = args.args.basewikiurl
moinPageList.copyPages()








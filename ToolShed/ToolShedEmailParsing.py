#!/usr/bin/python
#
# Parsing emails from the tool shed in a Gmail account
# This generates wiki markup listing any tools that were added to the ToolShed or
# updated after the specified date.
#
# Wiki Markup will look like
#
# * From [[URL of user home in ToolShed|username in toolshed]]
#   * [[URL of tool in ToolShed|name of tool]]: description from one or more places.
#   * [[URL of 2nd tool in ToolShed|name of tool]]: description from one or more places.
#

import argparse
import getpass                            #
import imaplib                            # Email protocol
import urlparse
import os.path
import urllib2
import re

HOST = "imap.gmail.com"
TOOLSHED_SENDER = "galaxy-no-reply@montana.galaxyproject.org"

#MSG_PARTS = "(BODY[HEADER.FIELDS (FROM SUBJECT BODY TEXT)])"
MSG_PARTS = "(BODY.PEEK[HEADER.FIELDS (From Subject)] BODY.PEEK[TEXT])"
HEADER_PARTS = "(BODY.PEEK[HEADER.FIELDS (From Subject)])"
BODY_PARTS = "(BODY.PEEK[TEXT])"

# indexes into tuple for each part
FROM    = 0
SUBJECT = 1

LINK_LINE = 1
REPO_LINE = 2
REVISION_LINE = 3
DESCR_START_LINE = 5

TOOLSHED_API_ROOT_URL = "https://toolshed.g2.bx.psu.edu/api/"


class ToolShedRepo:
    """
    Typical email will be
    Subject: Galaxy tool shed alert for new repository named package_blast_plus_2_2_30
    OR
    Subject: Galaxy tool shed update alert for repository named package_galaxy_ops_1_0_0
    From: galaxy-no-reply@montana.galaxyproject.org
    <1 blank line>
    Sharable link:         https://toolshed.g2.bx.psu.edu/view/iuc/package_blast_plus_2_2_30
    Repository name:       package_blast_plus_2_2_30
    Revision:              0:0fe5d5c28ea2
    Change description:
    Uploaded first version, based on BLAST+ 2.2.29 definition.
    
    Uploaded by:           iuc
    Date content uploaded: 2014-10-30
    """
    
    def __init__(self, headerTxt, bodyTxt):
        """
        Takes result of two IMAP fetches to create a ToolShedRepo object.  It also uses this information
        to access the ToolShed API to extract our the description and long description of each repo.
         
        Typical header:
          [('3 (UID 3 BODY[HEADER.FIELDS (From Subject)] {95}',
            'From: galaxy-no-reply@montana.bx.psu.edu\r\n
             Subject: Galaxy tool shed repository update alert\r\n\r\n'
           ),
           ')']
        Typical Body:
          [('3 (UID 3 BODY[TEXT] {678}',
            '\r\n
            GALAXY TOOL SHED REPOSITORY UPDATE ALERT\r\n
            -----------------------------------------------------------------------------\r\n
            You received this alert because you registered to receive email whenever\r\n
            changes were made to the repository named "ssr_marker_design".\r\n
            -----------------------------------------------------------------------------\r\n
            \r\n
            Date of change: 2011-11-23\r\n
            Changed by:     john-mccallum\r\n
            \r\n
            Revision: 2:16b5aa275b42\r\n
            Change description:\r\n
            Uploaded minor revision to gff converter\r\n
            \r\n
            \r\n
            \r\n
            -----------------------------------------------------------------------------\r\n
            This change alert was sent from the Galaxy tool shed hosted on the server\r\n
            "toolshed.g2.bx.psu.edu"\r\n'
           ),
           ')']
        """
        # Parse header info
        _headers = headerTxt[0][1].split("\r\n")
        self.sender = _headers[FROM][6:]
        self.subject = _headers[SUBJECT][9:]
        if self.sender != TOOLSHED_SENDER:
            return None                   # need to raise an error.

        # split body into an array of lines of text
        self.body = bodyTxt[0][1].split("\r\n")

        # extract repo link, which also contains author url
        self.url = self.body[LINK_LINE].split()[2]
        _urlParts = urlparse.urlparse(self.url)
        _authorPath, self.name = os.path.split(_urlParts.path)
        self.authorUrl = _urlParts.scheme + "://" + _urlParts.netloc + _authorPath     

        # Extract revision ID
        self.revision = self.body[REVISION_LINE].split(":")[2]
        
        # Extract commit message
        self.commit = ""
        line = DESCR_START_LINE
        while self.body[line].split(":")[0] not in ("Uploaded by", "Changed by"):
            self.commit += self.body[line]
            line += 1

        # Extract the author
        self.author =  self.body[line].split()[2]

        # Get the synopisis and long description of the repo using the ToolShed API.
        # https://toolshed.g2.bx.psu.edu/api/repositories/get_repository_revision_install_info?name=mirplant2&owner=big-tiandm&changeset_revision=2cb6add23dfe
        _tsApiUrl = (TOOLSHED_API_ROOT_URL + "repositories/get_repository_revision_install_info?" +
                    "name=" + self.name + "&owner=" + self.author + "&changeset_revision=" + self.revision)
        _tsData = urllib2.urlopen(_tsApiUrl).read()
        # True, False, and None are not python compliant; fix that before eval.
        # looking for patterns like: "deleted": false,
        _tsData = re.sub(r': false', r': False', _tsData)
        _tsData = re.sub(r': true', r': True', _tsData)
        _tsData = re.sub(r': null', r': None', _tsData)
        _tsData = eval(_tsData)

        # passe just means we aren't interested.
        self.passe = False
        for baddie in ["deleted", "deprecated", "malicious"]:
            if baddie in _tsData[0]:
                self.passe = self.passe or _tsData[0][baddie]
        self.synopsis = ""
        self.description = ""
        self.type = "Unknown"
        if "description" in _tsData[0]:
            self.synopsis = _tsData[0]["description"]
        if "long_description" in _tsData[0]:
            self.description = _tsData[0]["long_description"]
        if "type" in _tsData[0]:
            self.type = _tsData[0]["type"]

        return None

    def isUpdate(self):
        """
        Toolshed emails are either new repos or updates.  Can tell by looking at
        the subject line
        """
        return (self.subject.split()[3] == "update")

    def isNew(self):
        """
        Toolshed emails are either new repos or updates.  Can tell by looking at
        the subject line
        """
        return (self.subject.split()[3] == "alert")

    def isPasse(self):
        """
        Answers the age old question: is this repo no longer stylish?
        """
        return self.passe

class Arrgghhss(object):
    """
    Process and provide access to command line arguments.
    """

    def __init__(self):
        argParser = argparse.ArgumentParser(
            description="Generate wiki markup to describe ToolShed updates within a given period.")
        argParser.add_argument(
            "-e", "--email", required=True,
            help="GMail account to pull ToolShed update notices from")
        argParser.add_argument(
            "--toemail", required=False,
            help="Optional. Use if the email account is different than the email address notifications are sent to.")
        argParser.add_argument(
            "--mailbox", required=True,
            help="Mailbox containing ToolShed update emails. Example 'Tool Shed' ")
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

# Main
        
newToolRepos = {}
updates = {}
passe = []

args = Arrgghhss()                        # Command line args

# Establish Email connection, get emails.

email = imaplib.IMAP4_SSL(HOST)
email.login(args.args.email, getpass.getpass())
email.select(args.args.mailbox, True)

emailSearchArgs = []
emailSearchArgs.append('SENTSINCE ' + args.args.sentsince)
if args.args.sentbefore:
    emailSearchArgs.append('SENTBEFORE ' + args.args.sentbefore)
emailSearchArgs.append('HEADER From "' + TOOLSHED_SENDER + '"')
if args.args.toemail:
    emailSearchArgs.append('To "' + args.args.toemail + '"')

emailSearch = "(" + " ".join(emailSearchArgs) + ")"

typ, msgNums = email.uid('search', None, emailSearch)


# Process the emails.

for msgNum in msgNums[0].split():
    typ, header = email.uid("fetch", msgNum, HEADER_PARTS)    
    typ, body = email.uid("fetch", msgNum, BODY_PARTS)
    repo = ToolShedRepo(header,body)
    # Save repos by type, author and then name.
    if repo.isPasse():
        passe.append(repo)
    elif repo.isNew():
        if repo.type not in newToolRepos:
            newToolRepos[repo.type] = {}
        if repo.author not in newToolRepos[repo.type]:
            newToolRepos[repo.type][repo.author] = {}
        # duplicate emails are common for new repos; avoid them
        if repo.name not in newToolRepos[repo.type][repo.author]:
            newToolRepos[repo.type][repo.author][repo.name] = repo
    elif repo.isUpdate():
        if repo.type not in updates:
            updates[repo.type] = {}
        if repo.author not in updates[repo.type]:
            updates[repo.type][repo.author] = {}
        if repo.name not in updates[repo.type][repo.author]:
            updates[repo.type][repo.author][repo.name] = []
        updates[repo.type][repo.author][repo.name].append(repo)
    else:
        print("Not a tool shed repo:")
        print(header)

# Generate that wiki markup report.
        
print("=== New Tools ===")

for repoType, authors in newToolRepos.items():
    print("\n==== %s ====" % (repoType))
    for authorRepos in authors.values(): 
        first = True
        for repo in authorRepos.values():
            if first:
                print ("\n * ''From [[%s|%s]]:''" % (repo.authorUrl, repo.author))            
                first = False
            print ("   * [[%s|%s]]: %s %s %s" % (repo.url, repo.name, repo.commit, repo.synopsis, repo.description))

print("\n\n=== Select Updates ===")
for repoType, authors in updates.items():
    print("\n==== %s ====" % (repoType))
    for authorsRepos in authors.values():
        first = True
        for repos in authorsRepos.values():
            for update in repos:
                if first:
                    print ("\n * ''From [[%s|%s]]:''" % (update.authorUrl, update.author))
                    first = False
                print ("   * [[%s|%s]]: %s" % (update.url, update.name, update.commit)) 

print("\n\n=== Passe ===")
for repo in passe:
    print ("   * [[%s|%s]]: %s" % (repo.url, repo.name, repo.commit)) 
    
email.close()                             # close mailbox
email.logout()                            # closs connection

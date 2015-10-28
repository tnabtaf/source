#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Attempting to parse everything, including whitespace.

import argparse
from pypeg2 import *                           # parser library.
import re
import os

# What are the different types of things we hit in MoinMarkup?
        
# ################
# Basic Text
# ################

class TrailingWhitespace(List):
    grammar = contiguous(re.compile(r"[ \t\f\v]*\n", re.MULTILINE))

    def compose(self, parser, attr_of):
        return ("\n")

class Punctuation(List):
    """
    Characters that aren't included in plaintext.

    Matches a single character.
    """
    grammar = contiguous(
        attr("punctuation", re.compile(r"[^\w\s]")))
    

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(self.punctuation)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        # What should work
        parse(".", cls)
        parse("/", cls)

        # What should not work
        testFail(" OK[", cls)
        testFail(" ", cls)
        testFail("<", cls)
        testFail("Uh-huh, this text does'nt mean anything. [[", cls)
        testFail("}}", cls)


# ============
# plain text
# ============

class PlainText(List):
    """
    Text with no special characters or punctuation in it.

    A couple of things can end it:
     [[   Link start
     <<   Macro start
     ]]   Link end
     }}   Image attachement end
     |    Separator within a link
     \n
    """
    grammar = contiguous(
        attr("text", re.compile(r"[\w \t\f\v]+")))

    
    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(self.text)
        
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        # What should work
        parse(" Testing with no special terminator", cls)
        parse(" OK DOKE ", cls)

        # What should not work
        testFail(" OK DOKE[[", cls)
        testFail(" OK DOKE]]", cls)
        testFail(" OK DOKE. <<", cls)
        testFail("Uh-huh, this text does'nt mean anything. [[", cls)
        testFail(" OK DOKE}}", cls)

class QuotedString(List):
    """
    String embedded in quotes, single or double.

    Match includes the string.
    """
    grammar = contiguous(
        attr("quotedText",
             re.compile(r"""(?P<quote>['"])(?P<quotedText>.+?)(?P=quote)""",
                        re.DOTALL)))


    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(self.quotedText)

    
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("'Jump'", cls)
        parse('''"I Can't do this no more!"''', cls)
        parse(r'"= LAPTOP WITH BROWSER ="', cls)





# -------------
# PagePath - defined here instead of in Links b/c of dependencies
# -------------

class PagePath(str):
    """
    path to a page.  Can be absolute or relative.
    Used when we know we have a page name.

    Allowable characters are alphanumerics, spaces, periods, hash marks,
    and slashes, in any combination
    """
    grammar = contiguous(re.compile(r"[\w \.#/]+"))

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("FrontPage/Use Galaxy", cls)
        parse("FrontPage/Use Galaxy#This Part of the page", cls)
        parse("/Includes", cls)


        
# ################
# MACROS
# ################

class NamedMacroParameter(List):
    grammar = contiguous(
        r",", maybe_some(whitespace), name(), maybe_some(whitespace), "=",
        maybe_some(whitespace), QuotedString)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse(", fish='jump'", cls)
        parse(', fish="jump high"', cls)
        parse(', from="= LAPTOP WITH BROWSER ="', cls)


class EmptyMacroParameter(List):
    grammar = contiguous(r",")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse(",", cls)
        parse(", ", cls)

               
class IncludeMacroParameter(List):
    """
    Include params after the page path can be
      empty
      from="some text"
      to="some text"
    and lots of other things we don't use.
    See https://moinmo.in/HelpOnMacros/Include
    """
    grammar = contiguous([NamedMacroParameter, EmptyMacroParameter, whitespace])

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        NamedMacroParameter.test()
        EmptyMacroParameter.test()
        parse(", fish='jump'", cls)
        parse(", ", cls)


class IncludeMacro(List):
    """
    Include Macros can have one or more params.
      <<Include(FrontPage/Use Galaxy)>>
      <<Include(/Includes, , from="= LAPTOP WITH =\n", to="\nEND_INCLUDE")>>
    The opening and closing << >> will have been stripped before parsing.
    """
    grammar = contiguous(
        "Include(",
        maybe_some(whitespace),
        attr("pagePath", PagePath),
        maybe_some(whitespace),
        attr("params", maybe_some(IncludeMacroParameter)), ")")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        if self.params:
            return("INCLUDE(" + self.pagePath + self.params + ")")
        else:
            return("INCLUDE(" + self.pagePath + ")")

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        PagePath.test()
        IncludeMacroParameter.test()
        parse("Include(FrontPage/Use Galaxy)", cls)
        parse(r'Include(/Includes, , from="= LAPTOP =", to="END_INCLUDE")', cls)
        parse('Include(/Includes, , from="= LAPTOP =\\n", to="\\nEND_INCLUDE")', cls)

class CenterDiv(List):
    grammar = contiguous("center")

    def compose(self, parser, attr_of):
        return("""<div class="center">""")

        
class KnownDivClass(List):
    grammar = contiguous(
        [CenterDiv])
#        [CenterDiv, IndentDiv, LeftDiv, RightDiv,
#         SolidDiv, TitleDiv, NewsItemListDiv])  

        
class DivMacro(List):
    """
    Div Macros can define one or more local styles, or close a div
      <<div(solid blue)>>
      <<div(center)>>
      <<div>> (closing)
    Need to figure out what to do in each situation?  Maybe take advantage of
    CSS that we control?
    """
    grammar = contiguous(
        "div",
        optional("(", KnownDivClass,
            maybe_some(omit(whitespace), KnownDivClass),
            ")"))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = ""
        for divClass in self:
            out += compose(divClass)
        if len(self) == 0:
            out = "</div>"
        return(out)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        PagePath.test()
        parse("div(center)", cls)
        parse("div", cls)


class TOCMacro(List):
    """
    TableOfContents Macros insert TOC's.  There ya go.
      <<TableOfContents>>
      <<TableOfContents([maxdepth])>>
      <<TableOfContents(2)>>
    """
    grammar = contiguous(
        "TableOfContents",
        optional(
            "(", attr("maxDepth", re.compile(r"\d+")), ")"))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = "TABLE_OF_CONTENTS"
        try:
            out += "(" + self.maxDepth + ")"
        except AttributeError:
            pass
        return(out)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("TableOfContents", cls)
        parse("TableOfContents(2)", cls)

    
class Macro(List):
    """
    MoinMoin can have macros link include, or div or TableOfContents.  Sometimes they
    have parameters.
      <<Include(FrontPage/Use Galaxy)>>
      <<div(center)>>
      <<TableOfContents>>
      <<div>>
      <<Include(/Includes, , from="= LAPTOP WITH =\n", to="\nEND_INCLUDE")>>
      TODO
    """
    grammar = contiguous(
        "<<", attr("macro", [TOCMacro, IncludeMacro, DivMacro]), ">>")


    def compose(self, parser, attr_of):
        return(compose(self.macro))
    

    @classmethod
    def test(cls):
        DivMacro.test()
        IncludeMacro.test()
        TOCMacro.test()
        parse("<<div>>", cls)
        parse("<<div(center)>>", cls)
        parse("<<Include(FrontPage/Use Galaxy)>>", cls)
        parse("<<Include(Develop/LinkBox)>>", cls)
        parse(r'<<Include(/Includes, , from="= LA T =\n", to="\nEN_CL")>>', cls)



    
# ===============
# Section Header
# ===============

class SectionHeader(List):
    """
    Section headers start and end with = signs.  The more signs the smaller the header
      = Top level Header =
      == 2nd level Header ==

    That must be the only thing on the line.  Moin does not like leading or
    trailing spaces.
    """        
    grammar = contiguous(
        attr("depth", re.compile(r"^=+")),
        re.compile(" +"),
        attr("name", re.compile(r".+(?= +=+)")),
        re.compile(r" +=+\n"))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.

        How can that be dangerous?
        """
        return("#" * len(self.depth) + " " + self.name + "\n")        

        

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        return()
        parse("= A single tool or a suite of tools per repository =\n ", cls)
        parse("= Heading 1 =\n", cls)
        parse("== Heading Too! ==\n", cls)


        
# =============
# Links
# =============


class LinkProtocol(List):
    """
    http, ftp etc.
    """
    grammar = contiguous(
        attr("protocol", re.compile(r"((http)|(https)|(ftp))\://",
                                    re.IGNORECASE)))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(self.protocol)
    
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("http://", cls)
        parse("ftp://", cls)
        parse("https://", cls)

    
class ExternalLink(List):
    """
    Links that go outside the wiki.
    """
    grammar = contiguous(
        "[[",
        attr("protocol", LinkProtocol),
        attr("path", PagePath),
        optional("|", attr("linkText", re.compile(r".+(?=\]\])"))),
        "]]")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        linkOut = compose(self.protocol) + compose(self.path)
        # Try with link text first
        try:
            out = "[" + self.linkText + "](" + linkOut + ")"
        except AttributeError:
            # err on the safe side
            out = "[" + linkOut + "](" + linkOut + ")" 
        return(out)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        LinkProtocol.test()
        parse("[[http://link.com]]", cls)
        parse("[[ftp://this.here.com/path/file.txt]]", cls)
        parse("[[https://link.com/]]", cls)
        parse("[[http://link.com|Linkin somewhere]]", cls)
        parse("[[ftp://this.here.com/path/file.txt|Text for link.]]", cls)
        parse("[[https://link.com/| Whitespace test ]]", cls)



class InternalLink(List):
    """
    Links that go inside the wiki.

    GFM inverts the syntax of relative and root-derived links, compared to
    MoinMoin.
    In Moin relative links start with "/"
    In GFM relative linking is assumed, and starting a link with "/" may be
    undefined.

    So, this calls for some knowledge of the path to the current page in
    the MoinMoin directory, and the home of th enew page in the Markdown
    directory, to correctly translate.
    TODO
    """
    grammar = contiguous(
        "[[",
        maybe_some(whitespace),
        attr("path", PagePath),
        optional("|", attr("linkText", re.compile(r".+(?=\]\])"))),
        "]]")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        # Try with link text first
        try:
            out = "[" + self.linkText + "](" + compose(self.link) + ")"
        except AttributeError:
            # err on the safe side
            out = "[" + compose(self.link) + "](" + compose(self.link) + ")" 
        return(out)
    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        # Try with link text first
        try:
            out = "[" + self.linkText + "](" + compose(self.path) + ")"
        except AttributeError:
            # err on the safe side
            out = "[" + compose(self.path) + "](" + compose(self.path) + ")" 
        return(out)

        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("[[/PathToPage]]", cls)
        parse("[[path/file.txt]]", cls)
        parse("[[path/more/path/Page Name]]", cls)
        parse("[[/PathToPage|With Text]]", cls)
        parse("[[path/file.txt|uh-huh!]]", cls)
        parse("[[path/more/path/Page Name|Whitespace test 1]]", cls)
        parse("[[path/more/path/Page Name| Whitespace test 2 ]]", cls)



class ImageLink(List):
    """
    Link that shows an image, rather than text.

    In MoinMoin these look like:
      [[http://address.com|{{attachment:Images/Search.png|Search|width="120"}}]]

    So, it's the 2nd part of the link that tells us this is an image.
      
    See http://stackoverflow.com/questions/30242558/how-do-you-create-a-relative-image-link-w-github-flavored-markdown
    for this Markdown solution:
      [[[/images/gravatar.jpeg]]](http://www.inf.ufrgs.br) 

    Many image links include sizing, and that is not supported in Markdown.
    May just be better to go straight to HTML?
    """
    grammar = contiguous(
        "[[",
        optional(attr("protocol", LinkProtocol)),
        attr("linkPath", PagePath),
        "|{{attachment:",
        attr("imagePath", PagePath),
        optional(
            "|",
            optional(attr("altText", re.compile(r"[^}|]*"))),
            optional(
                "|",
                attr("imageSize", re.compile(r"[^\}]*")))),
        "}}",
        "]]")

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        # Generate HTML img link as it can deal with alt txt and sizes
        out = "<a href='"
        try:
            out += compose(self.protocol)
        except AttributeError:
            pass
        
        out += self.linkPath + "'>"
        out += "<img src='" + compose(self.imagePath) + "'"
        
        # Add alt text
        try:
            out += " alt='" + self.altText + "'" + compose(self.link) + ")"
        except AttributeError:
            pass
        # other stuff at the end
        try:
            out += " " + self.imageSize
        except AttributeError:
            pass
        out += " /></a>"
                    
        return(out)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse('[[search/getgalaxy|{{attachment:GetGalaxySearch.png}}]]', cls)
        parse('[[http://gp.org/sch/getxy|{{attachment:Im/L/GGS.png|S all}}]]',
              cls)
        parse('[[http://gt.g/gy|{{attachment:Is/L/G.png|s a|width="120"}}]]',
              cls)
        
       

class Link(List):
    """
    Links in Moin are enclosed in [[ ]].  Some have text, some have embedded
    images, and some have extra params.
    """
    grammar = contiguous(
        attr("link", [ImageLink, ExternalLink, InternalLink]))

        
    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        return(compose(self.link))

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        ExternalLink.test()
        InternalLink.test()
        ImageLink.test()
        parse(" [[http://link.com|Link to here]]", cls)
        parse("[[LinkToPage]]", cls)
        parse("[[LinktoPage|Text shown for link]]", cls)
        

# =============
# Subelements
# =============

class Subelement(List):
    """
    Subelements can occur in paragraphs or table text.

    Subelements can also be elements.
    """
    grammar = contiguous(
        [Macro, Link, QuotedString, PlainText, Punctuation])

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = ""
        for item in self:
            out += compose(item)
        return(out)



# ===========
# Lists
# ===========

class BulletListItem(List):
    """
    An individual entry in a bullet list.

    Look like
     * Text here.

    But, can't get pypeg's whitespace to work, so grammar drops spaces.
    That's a problem as we need to know depth.
    """
    grammar = contiguous(
        attr("depth", re.compile(r" *")),
        attr("bullet", re.compile(r"\*")),
        re.compile(r" +"),
        attr("item", some(Subelement)),
        re.compile(r" *"),
        "\n"
        )


    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = "* "
        for subelement in self.item:
            out += compose(subelement)
        out += "\n"
        return(out)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse(" * E\n", cls)
        parse(" * Electric boogaloo\n", cls)
        parse(" * A simple case.\n", cls)
        parse(" * A simple case \n", cls)


class BulletList(List):
    """
    Look like
     * Text goes here
     * More text here
    """
    grammar = contiguous(some(BulletListItem))

    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        out = ""
        for item in self:
            out += compose(item)
        return(out)
        
    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        BulletListItem.test()
        parse(" * One Item Only\n", cls)
        parse(" * A simple case.\n * With two items\n", cls)
        parse(""" * A simple case.
   * With nested item
""", cls)
        parse(""" * A simpler case.
   * With nested item
   * and another
""", cls)
        parse(""" * A less simplerer case.
   * With nested item
   * And another
     * and More!
   * Uh huh.
""", cls)





# ================
# Paragraph
# ================

class Paragraph(List):
    """
    Paragraphs are text separated by blank lines or other tokens.
    """
    grammar = contiguous(some(Subelement))

    def compose(self, parser, attr_of):
        out = ""
        for item in self:
            out += compose(item)
        return(out)

    @classmethod
    def test(cls):
        """
        Test different instances of what this should and should not recognize
        """
        parse("""Let's try plain text first.
        
        """, cls)



# ================
# Elements
# ===============
    
class Element(List):
    """
    An element is anything that can stand on it's own, at the the highest level
    of the Document.

    Elements don't have to be at the top level, but they can be.
    """
    grammar = contiguous(
        [SectionHeader, BulletList, Macro, Paragraph, TrailingWhitespace])


    def compose(self, parser, attr_of):
        """
        Override compose method to generate Markdown.
        """
        if self[0] is whitespace:
            return(self[0])
        return(compose(self[0]))

            
    
class Document(List):
    """
    Parse the whole page.

    Moin pages don't have to contain anything, and most items do not have to be in a
    particular order.

    Does the page arrive as a list of text lines?
    """
    grammar = contiguous(maybe_some(Element))




# =================================
# Non grammar subs
# =================================

class Argghhs(object):
    """
    Process and provide access to command line arguments.
    """

    def __init__(self):
        argParser = argparse.ArgumentParser(
            description="Convert a single wiki page (a file) from MoinMoin to Github Flavored Markdown. Running this with no params does nothing.  Running with --debug produces a LOT of output. Markdown is sent to stdout.",
            epilog="Example: " + os.path.basename(__file__) +
            " --moinpage=Admin.moin --debug")
        argParser.add_argument(
            "--moinpage", required=False, default=None,
            help="File containing a single MoinMoin page.")
        argParser.add_argument(
            "--runtests", required=False, 
            help="Run Unit Tests.",
            action="store_true")
        argParser.add_argument(
            "--debug", required=False, 
            help="Include debug output",
            action="store_true")
        self.args = argParser.parse_args()

        return(None)


def testFail(testText, cls):
    """
    Run a parse test that should fail.
    """
    try:
        parsed = parse(testText, cls)
        print(parsed.text)
        print("ERROR: Test that should have failed did not fail.")
        print("Test:")
        print(testText)
        printList(parsed)
        raise BaseException(cls.__name__)
    except (SyntaxError, TypeError):
        pass                              # TypeError is b/c of pypeg bug.
    return()


def printList(list, indent=0):
    for item in list:
        print("." * indent, item)
        if isinstance(item, str):
            print("s" * indent, item)
        else:
            print("c" * indent, compose(item))
            printList(item, indent+2)


def runTests():
    global args

    BulletList.test()
    SectionHeader.test()
    PlainText.test()
    Link.test()
    QuotedString.test()
    PagePath.test()
    IncludeMacro.test()
    Macro.test()
    #Paragraph.test()

    text = """
<<Include(Develop/LinkBox)>>
<<Include(Admin/LinkBox)>>
<<Include(FAQs/LinkBox)>>

= Galaxy Administration =
This is the hub page for the section of this wiki on how to deploy and administer your own copy of Galaxy.

== Deploying ==

 * [[CloudMan]]
 * [[/GetGalaxy|Install own Galaxy]]
 * [[CloudMan|Install on the Cloud Infrastructure]]
 * [[Admin/Maintenance|Maintaining an Instance]]
 * [[http://deploy.com]]

== Other ==
 * [[Admin/License|License]]
 * [[Admin/RunningTests|Running Tests]]
 * [[Community/GalaxyAdmins|Galaxy-Admins discussion group]]
 * [[Admin/SwitchingToGithubFromBitbucket|Switching to Github from Bitbucket]]

<<div(center)>>
[[http://galaxyproject.org/search/getgalaxy|{{attachment:Images/Logos/GetGalaxySearch.png|Search all Galaxy administration resources|width="120"}}]]

[[http://galaxyproject.org/search/getgalaxy|Search all Galaxy administration resources]]
<<div>>
 
"""

    f = parse(text, Document)

    if args.args.debug:
        print("DEBUG: DOCUMENT UNIT TEST in COMPILED FORMAT:")
        printList(f, 2)

    # What can we do with that parse now that we have it?

    markdownText = compose(f)

    if args.args.debug:
        print("\n====\n====\nDEBUG: DOCUMENT UNIT TEST DONE\n====\n====")

    return
        

# #########################################
# MAIN
# #########################################

args = Argghhs()                          # process command line arguments

if args.args.runtests:
    runTests()


if args.args.moinpage:
    # Read in whole file at once.
    moinFile = open(args.args.moinpage, "r")
    moinText = moinFile.read()
    moinFile.close()

    # Replace the mystery character with a space.
    moinText = re.sub(" ", " ", moinText)

    parsedMoin = parse(moinText, Document)
    if args.args.debug:
        print("DEBUG: DOCUMENT in PARSED FORM:")
        printList(parsedMoin, 2)
        print("====\n====\nEND DOCUMENT in PARSED FORM\n====\n====n")

    print(compose(parsedMoin))

class BoldText:
    """
    This is wrapped in 3 single quotes. Can span multiple lines.
    """

class ItalicText:
    """
    This is wrapped in 2 single quotes. Can span multiple lines.
    """

class UnorderedList:
    """
    Unordered lists are a series of consecutive rows that start with spaces * spaces text.
    They must all have the same indent.
    """
    
class OrderedList:
    """
    Ordered lists are a series of consecutive rows that start with spaces 1. spaces text.
    They must all have the same indent.
    """

class DoublePipe:
    """
    A double pipe can start a table row, end a table row, or separate table columns.
    """
    grammar = "||"
    
class Table:
    """
    Tables are a series of consecutive rows with each line starting and ending with double
    pipes ||.
    """


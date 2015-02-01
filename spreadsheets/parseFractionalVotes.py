#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Voting for the GCC is weighted.  Every voter gets the same amount of weight and they can
distribute it across as many or as few as they want.  This program calculates the total
vote weight for each topic.

First 3 columns of ballot are:
Timestamp
Your name
Your email address

After that, there are a varaible number of columns, one for each category of topic.
Weights are distributed evenly across all topics that a person voted for, regardless
of category.
"""

import argparse
import csv

WEIGHT = "weight"
CATEGORY = "category"

def argghhs():
    """
    Process and provide access to command line arguments.
    """
    argParser = argparse.ArgumentParser(
        description="Tally up weighted votes")
    argParser.add_argument(
        "--votes", required=True,
        help="File containing votes in a CSV format")
    return(argParser.parse_args())

# =============================================================
# MAIN

voteColumns = {"Using Galaxy ": "Using",
               "Galaxy APIs": "API",
               "Deploying, Administering, and Wrapping Tools for Galaxy": "Admin"}


args = argghhs()                          # process command line arguments

topicInfo = {}

voteFile = csv.DictReader(open(args.votes, "r"), delimiter= "\t")
nVotes = 0
for voteLine in voteFile:
    nVotes += 1
    topicsFromLine = []
    for voteColumn, category in voteColumns.items():
        if voteLine[voteColumn]:
            #print(voteLine[voteColumn])
            for topic in voteLine[voteColumn].split(", "):
                #print topic
                if topic not in topicInfo:
                    topicInfo[topic] = {WEIGHT: 0.0, CATEGORY: category}
                topicsFromLine.append(topic)

    # now have all the topics that were voted on by this voter; add their weight to totals

    voteWeight = 1.0 / len(topicsFromLine)
    for topic in topicsFromLine:
        topicInfo[topic][WEIGHT] += voteWeight
    
 
# print what we've found, in a tab delimited format of course

totalWeight = 0.0

print("Topic\tWeight\tCategory")
for topic in sorted(topicInfo, key=lambda x: topicInfo[x][WEIGHT], reverse=True):
    print(topic + "\t" +
          str(topicInfo[topic][WEIGHT]) + "\t" +
          topicInfo[topic][CATEGORY])
    totalWeight += topicInfo[topic][WEIGHT]

#print(nVotes, totalWeight)     # Should be equal


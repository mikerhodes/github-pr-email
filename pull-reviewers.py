#!/usr/bin/env python
#
#  pull-reviewers.py
#
# Copyright 2015 Mike Rhodes
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ========================================
#
# Script to print out PR info
#
# Uses GitHub's API and the convention that reviewers have a line
# in the PR body that is formatted `reviewer @mikerhodes`.
#
# Useful sites:
# - https://developer.github.com/v3/pulls/
# - https://developer.github.com/v3/auth/
# - https://github.com/blog/1509-personal-api-tokens

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import random
import smtplib

import requests

# Scope info https://developer.github.com/v3/oauth/#scopes
creds = (os.environ["GH_TOKEN"], "x-oauth-basic")  # no scopes
gh_org = os.environ['GH_ORG']
included_repos = json.loads(os.environ["GH_REPOS"])

possible_reviewers = json.loads(os.environ["POSSIBLE_REVIEWERS"])

smtp_server = os.environ["SMTP_SERVER"]
smtp_port = int(os.environ["SMTP_PORT"])
smtp_username = os.environ["SMTP_USERNAME"]
smtp_password = os.environ["SMTP_PASSWORD"]
smtp_from = os.environ["FROM_ADDRESS"]
addressees = json.loads(os.environ["ADDRESSES"])
do_send = int(os.environ['SEND'])

# The number of reviewers that a PR must have for it not to be on the
# list of PRs needing more reviewers
expected_reviewer_count = 2

reviews_by_reviewer = {}  # { "@mikerhodes": [PullRequest()] }

class PullRequest:
    def __init__(self):
        self.repo_name = None
        self.title = ""
        self.opened_by = ""
        self.html_url = ""
        self.created_at = datetime.now()
        self.reviewers = []

    @property
    def delta(self):
        return datetime.now() - self.created_at


# For the given repository, get the info from Github for the pull
# request and into a RepoData object.
def get_pull_requests(repo_name):
    result = []
    pulls = requests.get(
        "https://api.github.com/repos/{0}/{1}/pulls".format(
            gh_org,
            repo_name
            ),
        auth=creds).json()
    for pull in pulls:
        pr = PullRequest()
        pr.repo_name = repo_name
        pr.title = pull["title"]
        pr.opened_by = pull["user"]["login"]
        pr.html_url = pull["html_url"]
        pr.created_at = datetime.strptime(pull["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        for line in pull["body"].split('\n'):
            if "reviewer" in line:
                reviewer = line.split()[1]
                pr.reviewers.append(reviewer)
        result.append(pr)
    return result

##
## Collect the data
##

pull_requests = []
for repo in included_repos:
    pull_requests += get_pull_requests(repo)

##
## Process the data
##

reviews_by_reviewer = {}
for reviewer in possible_reviewers:
    reviews_by_reviewer[reviewer] = []
for pr in pull_requests:
    for reviewer in pr.reviewers:
        if reviewer in reviews_by_reviewer:  # some reviewers outside team
            reviews_by_reviewer[reviewer].append(pr)

# List of people with no reviews
no_pending_reviews = filter(
    lambda r: len(reviews_by_reviewer[r]) == 0,
    reviews_by_reviewer.keys()
)

# A list of all pull requests with fewer than two reviewers (we require
# two reviewers).
prs_requiring_reviewers = []

for pr in pull_requests:
    if len(pr.reviewers) < expected_reviewer_count:
        prs_requiring_reviewers.append(pr)

##
## Write the email content
##

msg = u""

# Write out the intro.

msg += "Open pull requests:      {0}".format(len(pull_requests))
msg += "\nRequiring reviewers:     {0}".format(len(prs_requiring_reviewers))
msg += "\nPeople with no reviews:  {0}".format(
    ", ".join(no_pending_reviews) if no_pending_reviews else "-"
)

# List pull requests that have no reviewers

if prs_requiring_reviewers:
    msg += "\n\n# PRs requiring more reviewers\n"
    for pr in prs_requiring_reviewers:
        msg += "\n  - [{0}] {1} \n      {2}".format(
            pr.repo_name,
            pr.title,
            pr.html_url
        )

# Finally list the reviews each person has, or suggest if they have none.

msg += "\n\n# Pull requests by assigned reviewer"
ordered_reviewers = sorted(reviews_by_reviewer.keys())
for reviewer in ordered_reviewers:
    prs = sorted(reviews_by_reviewer[reviewer], key=lambda x: -x.delta.days)
    msg += "\n\n  {0} ({1} pending review{2}):".format(
        reviewer,
        len(prs),
        "s" if len(prs) > 1 else ""
    )
    for pr in prs:
        msg += "\n    - [{0}] {1}".format(
            pr.repo_name,
            pr.title
        )
        msg += "\n        ({0} days) {1}".format(
            pr.delta.days,
            pr.html_url)

    # Suggest reviews if there are people that are free and available PRs.
    # Choose a PR from the no reviewers list in preference to single reviewers.
    if not prs:
        if prs_requiring_reviewers:
            msg += "\n    WHY NOT REVIEW THIS ONE?"
            pr = random.choice(prs_requiring_reviewers)
            msg += "\n    [{0}] ({1} days) {2}\n    {3}".format(
                pr.repo_name,
                pr.delta.days,
                pr.title,
                pr.html_url
            )

print ""
print msg
print ""

# mail sending

if (do_send):
    email = MIMEMultipart('alternative')
    email['Subject'] = 'Open PRs: {0}'.format(datetime.now().strftime("%d %b %Y"))
    email['From'] = smtp_from
    email['To'] = ', '.join(addressees)

    text = msg
    part1 = MIMEText(text, 'plain', 'utf-8')
    email.attach(part1)

    s = smtplib.SMTP(smtp_server, smtp_port)
    s.login(smtp_username, smtp_password)
    s.sendmail(email["From"], addressees, email.as_string())
    s.quit()
else:
    print 'not sending (set SEND env var to 1 to send)'


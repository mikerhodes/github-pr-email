# GitHub PR Summary Email

This script collects PR information from specified GitHub repositories and sends out an email listing the PRs by assigned reviewer.

It also lists team members without assigned review duties, and will pick a PR which is in need of reviewers to suggest to them.

The email looks like this:

```
Open pull requests:      2
Requiring reviewers:     1
People with no reviews:  @bar

# PRs requiring more reviewers

  - [frobulate] Ensure frob can successfully ulate
      https://github.com/yourorg/frobulate/pull/38

# Pull requests by assigned reviewer

  @foo (1 pending review):
    - [frobulate] Tidy up exception handling
        (43 days) https://github.com/yourorg/frobulate/pull/210

  @bar (0 pending review):
    WHY NOT REVIEW THIS ONE?
  - [frobulate] Ensure frob can successfully ulate
      https://github.com/yourorg/frobulate/pull/38

  @baz (1 pending review):
    - [frobulate] Tidy up exception handling 
        (43 days) https://github.com/yourorg/frobulate/pull/210
```

To assign reviewers, it uses a simple convention: add a line in the PR description containing `reviewer @foo` for each reviewer. `reviewer` and the GitHub username should be the only things on the line.

### Setup

The script gets the rest of its configuration from the environment. The following script is a template which sets the variables and launches the script:

```
#!/bin/bash

# Set up env and call pull reviewers py

# token with appropriate scopes for the repos below 
# (e.g., public or private repo scope)
export GH_TOKEN='your-token'

# Only supports on GH org right now
export GH_ORG='yourorg'

# JSON string of repositories to access
export GH_REPOS='["frobulate", "dilithium"]'

export SMTP_SERVER='smtp.yourorg.com'
export SMTP_PORT='587'
export SMTP_USERNAME='username'
export SMTP_PASSWORD='password'

# JSON string of address to send email to.
export ADDRESSES='["foo@yourorg.com", "bar@yourorg.com", "baz@yourorg.com"]'

export FROM_ADDRESS='Foo <foo@yourorg.com>'

# JSON string listing possible reviewers (used to figure out who has no
# assigned reviews).
export POSSIBLE_REVIEWERS='["@foo", "@bar", "@baz"]'

# Set to '0' to not send
export SEND='1'

python pull-reviewers.py
```

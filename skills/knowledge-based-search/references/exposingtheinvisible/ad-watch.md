---
title: ad.watch, Investigating Political Ads on Facebook
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

## Overview

This chapter is a first-person case study by Manuel Beltran and Nayantara Ranganathan tracing how they built ad.watch (ad.watch), an open-research project that collects and visualizes political advertising data from Facebook and Instagram across dozens of countries. Published April 2020, the chapter covers their motivations, technical methods, specific obstacles, surprising discoveries, and the platform responses they encountered after publication.

## Why They Built It

Much online advertising is targeted: platforms use psychological and behavioral data about people to deliver different messages to different individuals. Because politicians use these same systems, political propaganda is distributed through personalized channels that are largely invisible to the public and to regulators. Even the advertisers themselves do not receive a complete picture of who their ads reach or why.

Beltran and Ranganathan began investigating during India's 2019 general elections. A specific, testable question drew them in: India's electoral law mandates a "silence period," prohibiting campaign advertising in the 48 hours before voting. They wanted to know whether Facebook was enforcing this rule online.

## Data Collection: The Facebook Ad Library API

Facebook released its Ad Library API in 2019 as a transparency measure following the Cambridge Analytica scandal. The API was poorly documented, frequently crashed, and imposed rate limits that were not clearly defined. Automated scripts triggered blocking. Queries for large datasets caused browser freezes.

Unable to automate efficiently, the investigators developed a manual workflow. They loaded query URLs in a browser, copied paginated results, added them to text files, and manually inserted commas between pages to maintain valid JSON. The human pace of copying and pasting appeared to circumvent Facebook's anti-scraping defenses more reliably than automated scripts. Fields they collected included ad creation times, delivery start and stop times, spend amounts, demographic breakdowns, and regional distribution data.

## Analyzing the Data: Tableau and Its Limits

They used Tableau, a data analysis and visualization tool, to make sense of the collected JSON files. Because their computers were too slow to handle databases exceeding five gigabytes, one investigator accessed a remote desktop at his university, an Intel Xeon processor machine with 20 GB of RAM, via Remote Desktop Protocol (RDP). This allowed large Tableau sessions to run independently of the laptop.

Tableau accepts JSON files up to 128 MB. To stay within this limit, they split larger files using a Python script called json-splitter. They also used JSONLint to validate JSON formatting. A recurring problem was that ad text contained non-Latin scripts, as well as emoji and recent Unicode characters. These caused syntax errors that prevented many open-source visualization tools from opening the files. Open-source alternatives such as Rawgraphs and Datawrapper were ruled out for this reason. Tableau Public was used for final publication.

## Key Finding: Silence Period Violations

By matching ad delivery timestamps against official regional voting schedules in India's staggered multi-phase elections, the investigators found that political actors systematically violated the silence period. The violations were routine rather than exceptional.

## What the Data Also Revealed

The structure of the data itself was revealing. Facebook classified users into a gender binary of male and female for ad targeting, even though its user-facing settings offered a broad range of gender options. This gap between the user experience and the backend advertising infrastructure was a concrete example of how the platform's transparency was limited.

The investigators also created fictitious political party pages and purchased ads to see the targeting options available to advertisers. They found that the level of targeting detail available to buyers was far greater than what appeared in the Ad Library. Targeting options included categories like "Friends of people celebrating Ramadan," which they identified as a category that could be used to exclude or target Muslims. They noted that Facebook had committed to restricting race- and gender-based targeting for ads related to employment, housing, and credit in the United States following documented discrimination cases, but that equivalent protections were not in place in other parts of the world.

## Scope and Automation

As the project expanded, they began collecting ad data from Spanish parties for the 2019 European Parliament elections and Spain's municipal and national elections. They then extended to political actors in all countries where Facebook made Ad Library data available, eventually covering 39 countries. They decided not to analyze data for countries they lacked context for, but to collect and publish it so that journalists and researchers in those countries could use it.

To handle the growing scope, Beltran and Ranganathan developed a Python script to automate data collection from the API. They added randomized time delays between queries to mimic human behavior and avoid rate-limit blocking. They stored Facebook Page IDs in text files and used two-letter ISO country codes to collect multiple countries in one run. ad.watch launched on July 26, 2019.

## Displaying Ad Visuals

Ad images and video could not be easily displayed. The API does not provide downloadable media files. Instead, ad snapshot URLs include an "access token," a unique time-bound string appended after `access_token=` in the URL that expires within an hour, making the link useless to anyone who does not supply their own token. The investigators considered scraping images with browser add-ons or Python scripts, and tried the `wget` command, but Facebook's terms of service prohibit scraping, and all such methods failed. They eventually built a workaround in Tableau allowing users to input their own access tokens to view ad content. Later, they found Facebook's Access Token Debugger tool, which allowed tokens to be extended, and incorporated extended tokens into their data collection system.

## Sharing Data with Journalists

When sharing raw data with journalists, they had to remove their personal access tokens, which were embedded in the `ad_snapshot_url` field of every ad record. With millions of ads, manual removal was impractical. The solution was a one-line command using SED (Stream Editor), a text-processing tool included with Linux terminals:

```
sed -i -e 's/[access_token_value]//g' US_20_1.json
```

SED searched for the token string and deleted it from each file automatically.

## Identity Verification and Third-Party Contractors

Gaining access to the Ad Library API required identity verification. The experience differed significantly between the two investigators.

Nayantara Ranganathan, whose primary country was India, had to verify her address through a process that offered two options: wait three weeks for a verification code delivered by post, or have someone visit her home within a week. She chose the visit. The visitor called from a company called OnGrid, an Indian identity-verification-as-a-service firm. The OnGrid representative visited her home, photographed the exterior and a nearby landmark, and collected the signature of another person present at the address.

OnGrid offers services ranging from education verification to court record checks. The investigators noted that its data retention policies differ from Facebook's. Facebook claims to permanently delete identification data collected during verification. OnGrid retains the data it collects to offer identification services to other entities, meaning Facebook's privacy commitments did not bind its third-party verification contractor.

Manuel Beltran, a Spanish citizen living in the Netherlands, went through a simpler online verification process, though final approval took approximately two days, suggesting a human review step.

## Platform Responses After Launch

Facebook's former Vice President of Ads commented positively on ad.watch after its launch. The investigators found this uncomfortable because the project was intended as a challenge to Facebook's inadequate transparency practices, not as an endorsement of them. They explicitly did not want Facebook to use the project as part of its own transparency success story.

On Twitter, two days after launch, the investigators noticed that tweets about the project were disappearing. This was an instance of shadowbanning: tweets remained visible to their authors but were hidden from others' timelines and searches, with no censorship notice issued. The project URL was also blocked in Twitter direct messages. Others attempting to share the link on LinkedIn received warning messages.

The investigators traced the block to a URL classification system. The security firm FortiGuard (fortiguard.com/webfilter) had listed ad.watch as spam based on a user report. They filed an appeal and FortiGuard reclassified the URL, noting with some irony that the new classification was "advertising." Twitter eventually removed the shadowban without providing an explanation. The investigators explored using the European GDPR right to explanation to demand an account from Twitter but this avenue was not resolved.

## After Publication

Once live, ad.watch was updated regularly. New countries were added as Facebook made their data available in the API, including Argentina, Sri Lanka, Singapore, Norway, and Switzerland. The Python collection script was improved to reduce manual intervention.

The project received coverage in Vice, HuffPost, The Hindu, and international broadcasters. Journalists from multiple countries used its data for their own investigations into political advertising. As of January 2020, the team was working on making political ad data more accessible for different audiences globally and on allowing direct data downloads for independent researchers. Visitors to the site contributed new Facebook Page IDs by email as political parties and coalitions changed.

## Broader Argument

The chapter argues that Facebook's advertising infrastructure is structurally in tension with the conditions needed for meaningful democratic participation on social media. The platform's deliberate obfuscation of its targeting mechanisms, the barriers it placed on data access, the outsourcing of verification to third-party contractors with different data policies, and the limited documentation of its API all constituted forms of opacity that undermined accountability. The investigators describe operating under the continuous awareness that Facebook had the power to revoke their API access, classify their methods as terms-of-service violations, or use its data about them in damaging ways. None of those outcomes materialized, but the risk shaped the project throughout.

## Tools Referenced

- Facebook Ad Library API (facebook.com/ads/library/api)
- Tableau (tableau.com) for data analysis and visualization, via Tableau Public for online publication
- VirtualBox for running Windows-only software on Linux
- Remote Desktop Protocol (RDP) and Remmina for remote access to a higher-powered machine
- json-splitter (github.com/jhsu98/json-splitter), a Python script for splitting large JSON files below Tableau's 128 MB import limit
- JSONLint (jsonlint.com) for validating JSON syntax
- SED (Stream Editor), a Linux command-line tool, for bulk removal of access tokens from data files
- wget (gnu.org/software/wget) for attempted image retrieval (unsuccessful)
- Facebook Access Token Debugger (developers.facebook.com/tools/debug/accesstoken/) for extending token lifetimes
- Facebook Tracking Exposed (FBTrex) (facebook.tracking.exposed), a related browser extension project
- ProPublica's Political Ad Collector and Who Targets Me, two browser plugin projects collecting political ad data through crowdsourcing
- Bash, Python, StackOverflow, Rawgraphs, Datawrapper (considered but not used for publication)
- FortiGuard (fortiguard.com/webfilter), the URL classification service that blocked ad.watch as spam
- OnGrid (ongrid.in), Facebook's third-party identity verification contractor in India

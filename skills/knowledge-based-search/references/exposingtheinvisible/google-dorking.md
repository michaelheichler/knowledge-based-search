---
title: Search Smarter by Dorking
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

This chapter, written by Gabi Sobliye, explains Google dorking (also called Google hacking), a technique for running advanced search engine queries to find publicly accessible information that does not surface through ordinary searches. The chapter covers what dorking is, how operators work across search engines, practical examples, privacy precautions, and how to use the technique defensively.

## What dorking is and why it matters

Dorking means using search engines to their full potential by combining regular search terms with special keywords called operators or filters. An ordinary search uses semantic phrasing or keywords. A dork adds technical elements that instruct the search engine to filter results by domain, file type, page title, page content, URL structure, or other criteria. The goal is to reach files and pages that exist publicly but do not appear in standard results.

The technique is used by newsrooms, investigative reporting organisations, security auditors, and attackers. It does not require technical depth. It requires knowing a small set of syntax rules plus persistence, creativity, and patience.

Johnny Long (aka j0hnnyhax) coined the term "googleDork" in 2002. In a 2011 interview he described his approach: "the simplest approach is usually the best," noting that investigators often overlook non-technical methods in favour of sophisticated tools.

## How operators work

Operators are keywords that end with a colon and are followed immediately by a search term, with no space before or after the colon. They can be combined with each other and with plain search terms.

Core examples:

- `site:domain.com` restricts results to a specific domain and its subdomains.
- `filetype:pdf` returns only results of the specified file type.
- `intitle:text` finds pages where the specified word appears in the page title.
- `intext:text` (or `inbody:text` on Bing and Yahoo) searches within page content across all four engines covered.
- `inurl:text` finds pages where the term appears in the URL.
- `allinurl:text` works on DuckDuckGo for the same purpose.
- `cache:url` retrieves a search engine's cached copy of a page (Google only).
- `related:url` finds pages similar to a given page (Google only).
- `info:url` returns information Google holds about a page (Google only).
- `meta:text` searches meta tags (Bing only).
- `contains:text` finds pages linking to specified file types (Bing only).
- `ip:address` finds sites hosted at a specific IP address (Google, DuckDuckGo).
- `language:code` filters by language (DuckDuckGo, Yahoo).
- `location:code` or `loc:code` filters by country using ISO 3166-1 codes (Bing, DuckDuckGo).
- `feed:rss` finds RSS feeds (Google, DuckDuckGo, Yahoo, Bing).
- `hasfeed:url` finds pages that have RSS or Atom feeds (DuckDuckGo, Bing).
- `book:title` searches for book titles (Google only).
- `linkfromdomain:url` finds sites whose links are mentioned in a given URL (Bing only, noted as having errors).
- `inanchor:text` searches link anchor text (Google only).
- `altloc:code` searches for location in addition to the one specified by the site's language (Bing only).

Beyond prefix operators, quoting a phrase with double quotation marks forces an exact match. Writing `OR` in all caps between terms returns results containing either term.

The `filetype:` operator does not recognise related formats automatically. Searching for `.xls` will not return `.xlsx` files. Each format must be queried separately or combined with `OR`.

Operator order can affect results on some search engines, so trying different combinations is worthwhile.

## Three worked examples

The chapter demonstrates the technique with three queries submitted across Google, Bing, Yahoo, and DuckDuckGo. All three show that the same dork returns different results on different engines.

**Example 1.** `budget site:dhs.gov filetype:xls` finds Excel spreadsheets containing the word "budget" on the United States Department of Homeland Security website. Google required solving a CAPTCHA during this test.

**Example 2.** `filetype:xls "house prices" AND "London"` finds Excel files about London housing prices.

**Example 3.** `filetype:doc "security plan" site:gov.in` finds Word documents containing the phrase "security plan" on Indian government websites.

## DuckDuckGo and the bang feature

The chapter's preferred search engine is DuckDuckGo, which claims not to collect personal information and stores queries in a way that cannot be attributed to individual users. It is also less likely than Google to block Tor users or present CAPTCHAs.

DuckDuckGo supports a feature called "bang." A bang is an exclamation mark followed by a qualifier at the start of a query. It redirects the search to another service. For example, `!w dorking` runs the query on Wikipedia, and `!twitter` routes to Twitter search. Bangs work in the address bar when DuckDuckGo is the default browser search engine. The chapter notes that using a bang removes DuckDuckGo's privacy protection for that query, because the search is then handled by the destination service.

For general browsing, the chapter also recommends StartPage, which returns Google results through a privacy filter that reduces the personal information Google can collect.

## Privacy and legal risks

Search queries are monitored and stored indefinitely by search providers and governments. A query can be recorded, linked to a person, and potentially used against them.

Accessing pages or downloading files found through dorking can be a criminal offence in some jurisdictions even when the content sits on a public server. In the United States, the Computer Fraud and Abuse Act (CFAA) is described as "vague and overreaching" and applies in some circumstances to accessing publicly accessible pages.

**Recommended precautions:**

Use the Tor Browser or Tails (an operating system that routes all traffic through Tor) when dorking. Tor masks internet traffic and separates a computer's identifying information from the pages being accessed. It does not hide the fact that the user is running Tor, which can itself flag activity as suspicious in some countries. To reduce that visibility, the Tor Browser can be configured to use a Bridge with the "obfs4" pluggable transport, which attempts to disguise Tor traffic as something else.

When Tor returns CAPTCHA challenges or blocks searches, the user can request a new Tor circuit by clicking the site information icon in the address bar and selecting "New Circuit for this Site."

If Tor is not available, a VPN (Virtual Private Network) is a less effective alternative. A VPN disguises the user's IP address by routing traffic through the VPN provider's server. The chapter recommends choosing a VPN provider that does not log traffic and warns against most free VPNs, which often fund themselves by selling usage data. Endorsed free options include Bitmask, Riseup VPN, PsIPhon, and Lantern.

## Defensive dorking

Dorking can be turned inward to find vulnerabilities or exposed data on one's own systems. The chapter calls this "defensive dorking" and describes two uses.

**Checking for security vulnerabilities.** The Google Hacking Database (GHDB) lists search terms that can reveal vulnerabilities such as exposed setup scripts or misconfigured directories. The chapter recommends coordinating with the technical administrator before running these tests unless the tester is the administrator.

**Finding exposed personal information.** The chapter recommends starting with queries like:

- `<your name> filetype:pdf` to find your name in PDF documents.
- `<your name> filetype:pdf OR filetype:xlsx OR filetype:docx` to search multiple file types at once.
- `<your name> intext:"<personal detail such as phone number or address>"` to find personal information in page text.
- `ip:[your server's IP address] filetype:pdf` to find documents associated with a server's IP address.

Removing the `site:` filter from any of these queries extends the search beyond the sites you control.

**Caution on search privacy.** If a search query includes sensitive personal details such as a social security number, those details are exposed to the search engine provider. The Tor Browser does not protect against this type of privacy leak.

## Password example

The chapter includes a worked example searching for password documents. The queries tested were:

- `password filetype:doc site:yoursite.org`
- `password filetype:docx site:yoursite.org`
- `password filetype:pdf site:yoursite.org`
- `password filetype:xls site:yoursite.org`

The authors ran the search without the `site:` filter. They found files containing actual usernames and passwords at two institutions, including a North American high school. They did not share the credentials, encrypted any files downloaded, did not test the passwords, and notified the affected organisations. The school subsequently removed the exposed list. The chapter uses this to illustrate both the power of the technique and the ethical obligations that come with it: intentions matter, and responsible use means notifying rather than exploiting.

## Cross-engine differences

A consistent theme throughout the chapter is that the same dork produces different results across search engines. Some engines return documents others do not. Some return irrelevant results. Running any dork across multiple engines gives a more complete picture than using a single engine.

The operator support table (tested as of March 2019) confirms that `site:`, `filetype:`, `intitle:`, and `intext:` (or its equivalents) work across all four major engines covered. Many other operators are engine-specific.

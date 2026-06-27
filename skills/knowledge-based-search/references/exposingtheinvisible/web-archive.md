---
title: Retrieving and Archiving Information From Websites
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

## Purpose

Websites disappear, pages get removed, and content changes without notice. This chapter explains how to find historical or deleted web content using archiving services and how to create your own archives of live pages as evidence for investigations.

## Core Archive Services

### Wayback Machine

URL: https://web.archive.org (also https://archive.org/web)

Run by the Internet Archive, a non-profit. Has archived approximately 345 billion pages going back to 1996, using automated crawlers that snapshot sites at various intervals.

The calendar interface shows available snapshots with color-coded dots: blue means a full capture, green means a redirect was recorded, orange or red means an error occurred. Clicking a date opens the list of snapshots for that day, and clicking a time loads the archived version. A timeline slider at the top lets you move across years.

Timestamps are embedded directly in archive URLs in the format YYYYMMDDhhmmss. For example: `https://web.archive.org/web/20170831060027/https://cambridgeanalytica.org` indicates an archive taken on 31 August 2017 at 06:00:27.

**URL shortcut patterns:**

| Goal | Pattern |
|---|---|
| Latest archived version of a page | `https://web.archive.org/www.yoursite.com/` |
| Calendar view of all snapshots | `https://web.archive.org/*/www.yoursite.com/` |
| All archived pages under a domain | `https://web.archive.org/*/www.yoursite.com/*` |

**Limitations:**

- Respects `robots.txt`, so pages explicitly excluded by site owners are not captured.
- Password-protected pages are not archived.
- Pages relying heavily on JavaScript rendering often archive incompletely or not at all.
- Website owners and EU "Right to Be Forgotten" rules can lead to content removal from the archive.
- No full-text search is available across the Wayback Machine's holdings.

### Archive.today

URL: https://archive.fo (formerly archive.is). Also reachable via Tor at: `archivecaslytosk.onion`

Archives individual pages on demand rather than crawling whole sites automatically. Key advantage: it ignores `robots.txt`, so it can capture content Wayback Machine cannot, such as Facebook profiles, Twitter posts, and pages that have blocked crawlers.

Each archive includes both a text version and a screenshot of the visual appearance. Full-text search of all its archived content is available. Wildcard searches work for domains, for example `*.cambridgeanalytica.org` finds all archived subdomains.

### Google Cache

Access through Google search: search for the target page, click the small arrow to the right of the result's web address, select "Cached."

Shows only the most recent cached version. No historical record is maintained. Site administrators can request removal. Treat as a short-lived fallback only, not as long-term or tamper-evident evidence.

### WebCite

URL: https://www.webcitation.org and https://www.webcitation.org/archive

Designed for preserving citations in academic and journalistic work. Supports DOI and cryptographic hash citations for tamper-evident referencing. Submit URLs via bookmarklet or the web form.

## Step-by-Step Procedures

**Look up historical snapshots with Wayback Machine:**
1. Go to https://archive.org/web.
2. Enter the target URL and press Enter.
3. The calendar view opens. Blue dots mark full captures.
4. Click a date to see the snapshot list for that day, then click a time to load the archived page.
5. Use the timeline slider at the top to jump across years.

**Archive a live page before it changes:**
1. Go to https://web.archive.org/web.
2. Enter the URL in the "Save Page Now" box.
3. Click "SAVE PAGE". The tool returns a permalink with an embedded timestamp.
4. Also archive via https://archive.fo for a second independent copy that ignores robots.txt.
5. Creating a free Wayback Machine account enables saving outlinks alongside the page and receiving email confirmation.

**Find all pages archived under a domain:**
Use the wildcard pattern `https://web.archive.org/*/www.yoursite.com/*`. This returns a list of every URL under that domain that Wayback Machine has captured.

**Download a complete archived site:**
Use the Wayback Machine Downloader script at https://github.com/hartator/wayback-machine-downloader (a Ruby script requiring Ruby 1.9.2 or later). Run it against the target domain to pull all captured pages locally with date range filtering.

## Case Studies

The chapter uses the Cambridge Analytica investigation as a primary example. Facebook's "Government and Politics" success stories page was removed by Facebook in 2018 but had been archived by Wayback Machine in 2017. Investigators recovered it via the Wayback Machine URL `https://web.archive.org/web/20170831060027/https://cambridgeanalytica.org`, illustrating how archive services preserve deleted content that would otherwise be unrecoverable.

The chapter also cites journalist and security researcher Brian Krebs, who used an archived version of a website that sold malware to identify the likely authors of that malware. The archived site contained a WebMoney account number linked to a username that had been used to promote the malware on an underground forum. Krebs traced that username back to a real identity. This shows that archives can preserve identifying details long after a site is taken down.

## Verification and Cross-Referencing

Cross-reference at least two archive services for any critical finding. Wayback Machine and Archive.today have different crawl histories and different robots.txt behavior, so together they cover more ground. Screenshot archived pages to document their exact visual appearance at a specific date. Store screenshots alongside the permalink URL. Check the timestamp embedded in the archive URL to confirm which snapshot date you are viewing.

Monitor a live site for changes using visual site monitors. These services let you specify a page or a section of a page to watch. They take a snapshot, then check for visible changes in text, images, or HTML at a set interval. When a change is detected, the service sends an email alert, sometimes with before-and-after screenshots.

Two services mentioned in the chapter are Visualping and ChangeTower. Visualping offers a free plan covering up to 62 pages per month and can run checks hourly, daily, weekly, or monthly. ChangeTower's free plan monitors up to three websites with up to six checks per day and stores results for up to a month. Both services work via the Tor Browser, which the chapter recommends using for privacy. Because these services require an account and an email address, use a separate compartmentalized email address if the investigation is sensitive.

## Limitations and Red Flags

- Archives can be removed via "Right to Be Forgotten" requests (EU law), administrator takedown requests, or robots.txt additions. A gap in the archive timeline may mean content was actively suppressed.
- Domain reregistration creates discontinuities: a domain that changed hands will show mixed content across the timeline.
- Heavily JavaScript-dependent pages (single-page apps, dynamically loaded feeds) often archive incompletely in Wayback Machine. Archive.today screenshot mode is more reliable for these.
- Google Cache is not suitable as long-term or tamper-evident evidence. Use it only for immediate retrieval, then archive the live URL independently.

## Operational Security

When you direct an archive service to a webpage, it crawls that page and the page's server automatically adds a record to its access log. This log includes the IP address of the requester (the archive service's address) but the timing of the request can indicate who triggered it if the subject monitors logs closely.

- Use a VPN or Tor Browser when accessing or submitting to archive services during sensitive investigations.
- Create compartmentalized accounts using secure email providers such as Tutanota (tutanota.de) or ProtonMail (protonmail.com), separate from any personal identity.
- Use prepaid payment methods if any service requires payment.
- Keep offline backups of critical evidence as PDF or saved HTML files in addition to online archive permalinks, in case online copies are later removed.

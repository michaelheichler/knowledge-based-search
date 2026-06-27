---
title: How to Track Online Disinformation Networks
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

Written by Nicola Bruno and published in February 2024, this chapter teaches journalists, activists, and researchers a four-step method for discovering and mapping coordinated online disinformation networks. It covers how to find a seed website, identify who runs it, trace advertising revenue connections, and monitor how content spreads through social media.

## What disinformation networks are and why they matter

Disinformation is organized into network infrastructures designed to manipulate and deceive in a coordinated way. The chapter distinguishes disinformation (deliberate, coordinated deception) from misinformation (false content shared without malicious intent). Network participants may not all know they are contributing to a disinformation operation, which is one reason the misinformation label sometimes applies.

Motivations vary. Some networks serve political goals, such as the Russian "troll factory" operated by the Internet Research Agency. Others pursue economic goals through advertising revenue, such as the Macedonian teenagers who ran clickbait sites during the 2016 US elections. A third category involves AI-generated content: NewsGuard identified a network of 125 unreliable AI-generated news sites as a recent example. What all cases share is a complex infrastructure of multiple websites acting in coordination, often amplified by social media.

The term FIMI (Foreign Information Manipulation and Interference), used by the EU External Action Service and the Media Manipulation Casebook, describes the strategic, intentional subset of this activity by state or state-affiliated actors.

## Text vs. context: why this is not fact-checking

The chapter draws a clear distinction between fact-checking and network investigation. Fact-checking verifies individual claims. This methodology instead examines everything surrounding a piece of content. The book "You Are Here" by Whitney Phillips and Ryan M. Milner is cited to make this point: investigators should "triangulate" information to trace where polluted content comes from and what forces have carried it. Pollution may be economically rooted (profit-driven institutions), interpersonally rooted (norms about what is acceptable to share), or ideologically rooted (deep memetic frames). By shifting from text to context, investigators can identify actors beyond the author of a single post and map the multi-dimensional nature of the campaign.

## The four-step method

### Step 1: Identify a disinformation website

The guide recommends starting with a website rather than a social media account or messaging app. Websites preserve historical data, reveal business connections, and expose network dynamics that social platforms do not. Disinformation sites typically focus on one of two kinds of topics: polarizing subjects (public health, migration, ongoing conflicts, culture wars) or "data voids," a term coined by Michael Golebiewski and danah boyd in a 2018 Data and Society report to mean topics where searches return minimal, low-quality, or manipulative results.

To find a seed site, the chapter recommends searching a fact-checking aggregator for a known data void keyword. The worked example uses "ivermectin": a search in the CoronaVirusFacts Alliance database or Google Fact Check Explorer turns up an AFP fact-check pointing to The Gateway Pundit as a spreader of false claims about the drug. That domain then becomes the subject for the next steps.

Databases and tools named for this step:

- Google Fact Check Explorer: aggregates debunked content from fact-checking newsrooms worldwide, searchable by keyword or image.
- EDMO Repository of Fact-Checking Articles: EU-focused database run by the European Digital Media Observatory.
- List of fake news websites on Wikipedia: useful but contested, since no standard methodology defines a site as entirely disinformation.
- UkraineFacts Database: developed by Maldita.es with IFCN partners, covering the Russia-Ukraine conflict.
- Covid-19 Misinformation Database: IFCN signatories' database for pandemic-era false claims.
- EUvsDisinfo Dataset: over 16,000 cases from Kremlin-aligned media, updated weekly.
- IO Archive: aggregator of influence operation datasets released by X (Twitter) and Reddit since 2018.

### Step 2: Discover who is behind the website

The first check is the site's "About" page and general search engine results. When those fail, the Whois protocol is the next resource. Whois records can reveal the registrant name and address, registration and last-update dates, and historical changes in IP address, registrar, and hosting. The worked example shows that a Whois lookup on sputniknews.com returns the registrant "Rossiya Segodnya," which a search engine then identifies as a media group owned and operated by the Russian government.

Privacy limits: EU GDPR has caused many Whois records to hide the registrant's name and contact details, though registration and update dates remain accessible.

ICANN's Registration Data Request Service (RDRS), launched in December 2023, allows investigators to request non-public registration data (name, address, email, phone) for generic top-level domains (.com, .org, .net, .edu, .gov, .mil). Country-code top-level domains (.fr, .to, and so on) are excluded. An ICANN account is required. The request form asks for a stated reason. Options include "Security Research" and "Research (non-security)." Access is not guaranteed, especially when a privacy or proxy service shields the registrant.

Whois tools named:

- Whois.com: standard lookup with a captcha.
- DomainTools (whois.domaintools.com): well-known, detailed records.
- Whoisology: highlights "connected domains" at a glance. Country-code domain data is paywalled.
- Whoxy: displays historical data about ownership and server changes, including data other services charge for.

### Step 3: Follow the money

Because Whois data is often obscured, advertising and traffic tracking identifiers embedded in a website's source code become the primary investigative tool. Disinformation sites depend on monetizing content through advertising, which means they embed third-party tracking IDs that remain publicly visible. Sharing a tracker ID with another site is strong evidence of a connection between the two.

The source code of any webpage can be viewed in most browsers with Ctrl+U (Windows/Linux) or Command+U (Mac). Within the source code, investigators search for specific ID prefixes with Ctrl+F or Command+F.

The two most useful Google IDs are:

- Google Analytics: formerly in the format UA-xxxxxx or GTM-xxxxxxx. As of July 1, 2023, Google Analytics 4 (GA4) uses G- prefixed IDs (Google Tags) and GTM- IDs (Google Tag Manager). Legacy UA- IDs may still appear on sites that have not removed them. The suffix in UA- IDs (for example, the "-3" in UA-3742720-3) indicated how many sites shared a core ID. Craig Silverman documented these changes in a July 2023 piece titled "What the rollout of Google Analytics 4 means for website investigations."
- Google AdSense: format CA-PUB-xxxxxxxxxxx, used for advertising revenue monitoring.

Other useful IDs include Amazon affiliate codes, Sharethis IDs, email addresses in the code, and Facebook app IDs.

The worked example: checking welovetrump.com in Builtwith's "Relationship" tab reveals other sites sharing the same tracking IDs.

Tools named for this step:

- Builtwith (builtwith.com): the recommended starting point. The "Relationship profile" tab reveals shared IDs and trackers across domains. Requires a free account. Using a dummy email address unrelated to personal or work accounts is advised.
- DNSlytics (dnslytics.com): lets investigators reverse-search by AdSense, Analytics, IP, mail server, or name server. Free version available, with a monthly paid tier.
- SpyOnWeb (spyonweb.com): useful for confirming or expanding results from other tools. Smaller database. No account required.
- AnalyzeId (analyzeid.com): shows connections in a table, including Amazon affiliate, Sharethis, email, Facebook app IDs, and a confidence rating. Exports data to CSV. Full results require a paid subscription.
- Wayback Machine (archive.org/web): when no current ID is found on a site, archived versions may retain older tracking IDs because the Wayback Machine stores source code. Used in the Gateway Pundit example to recover a historic ID.
- Bellingcat's Wayback Google Analytics Tool (github.com/bellingcat/wayback-google-analytics): released in late 2023, this command-line Python tool automates collection of Google IDs from archived websites. Described in a Bellingcat article by Justin Clark published January 9, 2024.

### Step 4: Monitor social amplification

The fourth step tracks how disinformation spreads across social media platforms. The chapter describes this as analyzing coordinated distribution patterns and the networks of accounts that amplify content, connecting what was found about websites to their associated social accounts and pages. This step is presented as recursive with the earlier steps: investigators move back and forth between steps as connections emerge rather than proceeding strictly in sequence.

A research template (an Excel spreadsheet called the Networks of Disinformation Sheet) and a pre-filled example are provided to organize data collected across all four steps.

## Considerations for investigators

The chapter closes with six standing considerations that apply to any investigation of this kind.

**Safety.** Prioritize digital and physical safety for yourself, your sources, and your peers. Use secure communication channels, strong passwords, and assessed tools. Consider VPNs and dummy accounts when researching sensitive topics. Creating accounts on social platforms, analytics tools, and web-tracking services during an investigation raises identity exposure.

**Ethics.** Respect privacy, avoid deceptive practices, and do not harm sources or subjects. Before publishing the identity of people behind a disinformation network, contact them, try to understand their motivations, and include their viewpoint if obtainable.

**Methodological rigor.** Validate sources and cross-check information. Not every finding qualifies as evidence that can survive legal challenge. Guard against confirmation bias by actively seeking evidence that could disprove your hypothesis.

**Evidence safeguarding.** Regularly archive web pages using the Wayback Machine, Archive.is, or Perma.cc, combined with screen-capture software. Good preservation protects against deletion and supports claims if challenged in court.

**Transparency.** Document every step of your investigative process so others can follow and replicate it. Clear methodology records build public trust.

**Wellbeing.** Investigating disinformation is mentally taxing. Take regular breaks, maintain open discussions with peers, and seek professional support if needed. The chapter warns against waiting until stress leads to burnout.

The chapter ends with a reminder that disinformation investigations rarely yield clear-cut conclusions: not everything is black and white, and responsible work means navigating grey areas while maintaining ethical and methodological standards.

## Key terms defined in the chapter

- **AdSense and Analytics IDs:** Unique codes for Google's advertising and analytics services, used to monitor traffic and advertising effectiveness.
- **Data voids:** Search topics that return minimal, misleading, or low-quality results, often exploited to fill the gap with disinformation.
- **FIMI (Foreign Information Manipulation and Interference):** Strategic, coordinated interference by one country in another's affairs through information manipulation.
- **Source code:** The underlying code of a website, viewable in a browser, which reveals tracking IDs and other operational details.
- **Troll factories:** Organizations that use multiple fake online identities to spread disinformation or manipulate public opinion, often state-sponsored.
- **VPN (Virtual Private Network):** Software that encrypts traffic and masks a user's real IP address.
- **Whois protocol:** A protocol for querying databases of registered domain owners, subject to privacy law limitations.
- **Web tracker:** Software used by websites to trace visitor behavior and identity.

---
title: How to See What Is Behind a Website
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

By Brad Murray and Wael Eskandar.

The chapter is a practical guide to investigating the ownership, infrastructure, and hidden content of websites. It explains the technical concepts an investigator needs to understand, the tools available for each type of lookup, and the safety precautions needed to protect the investigator during research.

## Website infrastructure: the basics

A website is a collection of digital files stored on a physical computer (a server) somewhere in the world. To reach a website, a browser needs the server's Internet Protocol address, or IP address. An IP address is written as four numbers separated by periods, each between 0 and 255. For example, 172.217.16.174 is one of the IP addresses for google.com. Because IP addresses are hard to remember, domain names translate them into readable strings.

Domain names are unique. The process of claiming one is called domain registration. The person who registers a domain is the domain registrant. The companies that manage registration are called registrars (examples: GoDaddy.com, Domain.com, Bluehost.com). They are governed by ICANN, the Internet Corporation for Assigned Names and Numbers. When a domain is registered, a record is created that tracks the owner. A separate category of companies, web hosting companies, store and serve the actual website files on servers in data centers. The registrar and web host may or may not be the same company.

## Safety: what you reveal when you visit a website

Visiting a website is not a passive act. The server receives your IP address and can also detect your device type (for example, iPhone 6 or MacBook), operating system (Windows, macOS, Linux), and installed fonts. This information can be used to identify, locate, and track you.

Two tools let you check what data you are currently sending:

- Cover Your Tracks (coveryourtracks.eff.org): tests how well your browser protects you against tracking. Works with Tor Browser.
- Browser Leaks (browserleaks.com): runs a set of security tests. Pay particular attention to WebRTC leaks and DNS leaks. A DNS leak allows your internet service provider (ISP) to see which sites you visit even when you are using a VPN.

## WHOIS lookups

When a domain is registered, the registrant's contact details are recorded as WHOIS data. This data typically includes the domain's creation and expiry dates, the registrar, and contact details for the site's owner and technical administrator. It is publicly accessible through WHOIS lookup services.

Owners who do not want to be linked to a site can register through proxy or intermediary organizations, a service called WHOIS privacy. In that case, the proxy's details appear instead of the real owner's.

Results vary across services, so the chapter recommends checking multiple sources. The example used is "usps.com" (the United States Postal Service): the ICANN WHOIS Lookup returns only dates and registrar details, while who.is returns an address, email contact, and phone number for the Postal Service.

Free services that provide WHOIS data:

- iana.org/whois: works via Tor Browser, no CAPTCHA.
- who.is: works via Tor Browser, no CAPTCHA.
- whois.domaintools.com: limited free searches, works via Tor Browser, no CAPTCHA.
- whois.com/whois/: works via Tor Browser, has CAPTCHA.
- godaddy.com/whois: works via Tor Browser, has CAPTCHA.

The chapter also points to IntelTechniques (inteltechniques.com), maintained by open source intelligence consultant Michael Bazzel, which aggregates multiple domain search tools in one place and also provides image metadata and social media search tools.

### GDPR and WHOIS

The EU's General Data Protection Regulation (GDPR) has restricted the public availability of WHOIS data for domains registered by EU-based registrants. ICANN has sued several European registrars for limiting access, arguing its own policy is GDPR-compliant. Courts have repeatedly rejected ICANN's position. As a result, WHOIS data for EU registrants is often restricted or unavailable.

## Historic WHOIS

Domain owners do not always use WHOIS privacy consistently. A person may have registered a domain with real contact details in the past and switched to a proxy later. Historic WHOIS records can reveal those earlier details and track changes in domain ownership over time.

One example the chapter gives: researchers investigating the Carbanak cybercrime gang, suspected of stealing over a billion dollars from banks, used DomainTools historical data to link hundreds of domains that had been initially registered using the same phone number and Yahoo email address. That link connected Carbanak to a Russian security company.

Services for historic WHOIS data:

- DomainTools (whois.domaintools.com): the best-known provider of historic WHOIS and hosting data. Requires a paid membership. Works via Tor Browser, no CAPTCHA.
- Whoisology: requires an account. The free tier is limited to the latest historical archive only, not the full history. Full historical archives require payment. Does not work via Tor Browser and may use CAPTCHAs.

The chapter recommends creating a separate email address when registering with these services, to avoid connecting your regular identity to investigative activity.

## Reverse WHOIS lookups

A reverse WHOIS lookup starts from a piece of contact information, such as an email address, phone number, or name, and returns all domains registered to that contact. This mirrors the logic of old printed reverse phone directories, which sorted entries by phone number rather than by name.

This technique is useful when a site owner has hidden their identity on one domain but used real contact details on another. Enumerating all domains linked to a shared email or phone number can map the full network of sites controlled by one person or organization.

Services for reverse WHOIS:

- ViewDNSinfo (viewdns.info): free, searches by email or phone number. Also offers historical IP address searches (a list of IP addresses a domain has been hosted on over time, with geographic location). Works via Tor Browser, no CAPTCHA. IP address owners are sometimes listed as "unknown," so combining results from multiple sites helps.
- Domain Eye: 10 free searches per day after registration. Works via Tor Browser, no CAPTCHA.
- DomainTools: paid, no free reverse WHOIS demo. Works via Tor Browser, no CAPTCHA.

## Finding information with shared hosting and reverse IP search

Websites sometimes share the same server to reduce costs or because their administrators are related. Analyzing the other domains sharing the same hosting can shed light on the owner or administrator of a site under investigation.

Tools for reverse IP and shared hosting searches:

- ViewDNSinfo (viewdns.info/reverseip): free reverse IP search that returns other domains hosted at the same IP address. The chapter demonstrates this with tacticaltech.org, whose IP address 213.108.108.217 returned 19 related domains belonging to the same organization.
- Bing IP search: prefix an IP address with "IP:" in the Bing search engine to find sites sharing that address. Returns both domain names and specific page addresses.
- Robtex (robtex.com): aggregates information from multiple sources to estimate website popularity. The free version covers basic results. Paid credits allow downloading detailed findings including reverse WHOIS reports. Works via Tor Browser.
- Netcraft (searchdns.netcraft.com): displays domain information including web trackers, hosting history, and site technology.
- Webhostinghero (webhostinghero.com): shows which web hosting company hosts a domain. Administrators managing multiple sites often use the same provider, which can reveal connections between domains.
- Built With (builtwith.com): scans websites to identify underlying technologies. Related sites often use identical software stacks, which can suggest connections between suspected domains.

## Source code examination

The page a visitor sees in a browser is a rendered translation of underlying code. That code, called source code, is written in languages such as HTML (HyperText Markup Language) and JavaScript. You can view it in any browser by right-clicking the page and selecting "View page source," or by pressing Ctrl+U on Windows and Linux.

Source code often contains information that does not appear in the rendered page:

- Developer comments: HTML comments begin with `<!--` and end with `-->`. They are never shown to visitors but may contain plain-language notes including street addresses, copyright designations, or hints about who maintains the site.
- Tracking codes and other identifiers embedded by site administrators.

### Reverse Google Analytics ID lookups

Google Analytics (analytics.google.com) allows one account to track multiple websites. Each site that uses Google Analytics embeds an ID number in its source code. All such IDs begin with "UA-" followed by an account number (example: "UA-12345678-2"). The number immediately after the first dash is the account number. The final number indicates how many sites share that account. A number greater than one means the account covers multiple sites.

Because multiple sites share one account, finding other sites that use the same Analytics ID can reveal connections between domains, especially when an owner has hidden their identity on one site but not on others.

To find a site's Google Analytics ID, open the source code and use Ctrl+F (or Command+F) to search for "UA-". The chapter works through this with whitehouse.gov, whose ID is UA-12099831-10.

Tools for reverse Analytics ID searches:

- DNSLytics (dnslytics.com/reverse-analytics): select "Reverse Analytics" from the Reverse Tools navigation menu.
- DomainIQ (domainiq.com/reverse-analytics).

The chapter cautions that results must be treated as leads, not evidence. Source code is sometimes copied from one site to another without removing the original Analytics ID. When that happens, an unrelated site will appear to share the ID. Results also differ between services, so searching more than one produces a more complete list.

#### Google Analytics 4 update (as of July 1, 2023)

Google retired the UA- ID format as part of the launch of Google Analytics 4. New sites no longer receive a UA- ID. However, Google does not require existing sites to remove a legacy UA- ID, so many sites still carry one. Google Analytics 4 uses the G- ID (the Google tag). Sites using Google Tag Manager show a GTM- ID. DNSlytics has been collecting G-, AW-, DC-, and GTM- IDs since Q4 2022. The suffix on a legacy UA- ID (the number after the final dash) is being eliminated in the migration.

## Metadata analysis

When software creates a file (a document, PDF, spreadsheet, or photograph), it automatically embeds metadata. Metadata is information about the file itself rather than its content: file size, creation date, date last modified, author name, or the name of the device used to create it.

If domain ownership cannot be established through WHOIS or source code, downloading files hosted on the site and examining their metadata can reveal the author's name or other identifying details.

Limitations: not all documents contain metadata, authors can delete or alter it before sharing, and metadata can reflect the device of an editor rather than the original author. Any metadata finding requires verification through multiple sources.

## Exposing hidden web content

### Robots.txt

The robots.txt file instructs web crawlers which parts of a site they may or may not access. Examining it can reveal areas of a website the owner wants to keep out of search indexes, which may point to content worth investigating further.

### Sitemap.xml

A sitemap.xml file lists the pages on a website to help search engines index them. Reviewing it gives an investigator a map of the site's complete structure and content, including pages that may not be linked from the public-facing navigation.

### Subdomain enumeration

Subdomains are prefixes added to a main domain (for example, mail.example.com or staff.example.com). They can host separate services or internal tools. Subdomain enumeration is the process of discovering which subdomains exist for a given domain by querying DNS records.

- DNSDumpster (dnsdumpster.com): a free tool that performs subdomain enumeration by querying DNS records to map the complete infrastructure associated with a domain.

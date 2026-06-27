---
title: OSINT, Diving Into an Ocean of Information
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

## What the chapter is about

This chapter, written by an OSINT researcher and published in March 2021, explains open source intelligence (OSINT) as a practice of combining publicly available information to produce actionable knowledge. The chapter is U.S.-centred by the author's own acknowledgment. It opens with the 2020 George Floyd protests as context, uses two detailed examples to show how OSINT works in practice, and then addresses leaks, transparency, safety, and the tension between open data and personal privacy.

## What OSINT means

OSINT stands for Open Source Intelligence. The chapter calls it "a professionalization of a basic concept." In this context, "open source" does not mean software. It means "free or inexpensive information, tools, or media that can be accessed, reviewed and used by average people, without licenses or active permissions." "Intelligence" simply means information, data, or knowledge.

OSINT refers to information legally accessible to a member of the public. Examples the chapter gives: an unprotected tweet, an unsealed court document, an Etsy review, a construction site's activities visible from the street. OSINT also covers information that was once private but has been leaked to the public, such as the Panama Papers or material published by WikiLeaks. The chapter notes that what counts as legally accessible varies by jurisdiction and by who is asking: a police officer has different access than a private citizen, and a U.S.-based investigator has different social-media access than one in China.

The chapter's central claim is that individual data points may seem useless on their own, but layering multiple sources together creates deeper understanding. The chapter uses two metaphors for this: waves of an ocean saturating sand, and dip-dyeing fabric, where each pass adds color until you reach the shade you want.

## Opening example: Lore-Elizabeth Blumenthal

The chapter opens with the FBI identification of Lore-Elizabeth Blumenthal, who allegedly set fire to two empty police cars on May 30, 2020, in Philadelphia. FBI investigators found her by combining aerial footage and social media footage of protesters, noticing a unique t-shirt she wore, finding the t-shirt's slogan in an Etsy store, and then comparing the public profile she used to leave a review for the t-shirt against other social media profiles using the same or similar name. The chapter uses this case to argue that the arrest was not evidence of "supercop" investigators or overreaching surveillance but of ordinary OSINT techniques that require no professional training and are free and available to anyone with decent internet access.

## Example 1: NYC building ownership

The chapter traces ownership of a $240 million Manhattan apartment at 220 Central Park South, which the Wall Street Journal in October 2019 called the most expensive home in the U.S. The deed (found in New York City Department of Finance property records at a836-acris.nyc.gov) records a January 23, 2019 purchase of Block 1030 Lot 1026 for $239,958,220. The seller was VNO 225 West 58th Street LLC. The buyer was NYCP LLC.

The deed's fifth page shows that the "sole member" of NYCP LLC is another company, K.P. Holdings, LLC., and that an individual named Molly McEvily is an authorized signatory. A search of the New York State Division of Corporations (apps.dos.ny.gov/publicInquiry/) returns no results for either entity. A search of the OSINT database OpenCorporates (opencorporates.com) is also consulted. A public LinkedIn profile for Molly McEvily shows she worked at Citadel LLC in the office of the CEO for several years. A Google search shows that the CEO of Citadel LLC has been Kenneth C. Griffin since he founded the company in 1990. The chapter calls this a reasonable lead that Griffin's money might be behind the purchase, while noting it is not a proven confirmation. Griffin was already linked to the purchase in media reports.

The chapter also notes that looking up the apartment address in the U.S. Securities and Exchange Commission's full-text database EDGAR (sec.gov/edgar/search/) yields 170 results, which an investigator could explore further.

The lesson drawn: many governments and corporations must publicly register information, but often in decentralized ways. The power comes from combining datasets that have mutual importance, pulling them from different sources until a picture emerges.

## Example 2: Radio12 and ScanMap

During the 2020 protests, it became widely known that some NYPD radio channels are publicly accessible. The organization Radio12 (radio12.org) organized volunteers to monitor these channels and publish relevant dispatches to Twitter under the hashtag #NYCScannerDuty. Protesters and bystanders needed to know, in real time, whether police were being dispatched to their location, whether prisoner vans were being sent, or whether a kettling operation was forming. Listening to a live scanner is not practical while moving in the street.

Radio12 built ScanMap (scanmap.mobi/NY/), a tool that takes those scanner-derived tweets and places them on a live map of New York City. The chapter calls the result "a mobile, free, accessible tool pulling together OSINT data points to perfectly serve an immediate need." The live public scanner alone was not useful for people in the street, but combined with public geographic data and maps it became an indispensable source of knowledge for people in protest actions.

## Leaks, transparency, safety, and power

The chapter discusses leaks as a category of OSINT. The Panama Papers were documents that were legally private before being leaked to the German newspaper Süddeutsche Zeitung, which published them in cooperation with the International Consortium of Investigative Journalists (ICIJ). Once published, they became OSINT. The ICIJ created a public Offshore Leaks Database (offshoreleaks.icij.org) from this material.

The chapter raises a second example involving Rebekah Jones, a former Florida state data scientist who said she was fired for refusing to manipulate COVID-19 infection data. Jones published her own COVID-19 data for Florida using the Florida Covid Action Community Database. In early December 2020, Florida agents raided her home. Jones stated she believed the raid was retaliation for her criticism of state data and for publishing independent data. The chapter uses this case to argue that creating OSINT tools that combine multiple datasets in simple, free, and intuitive ways can be threatening to governments and those in power precisely because they challenge official data and invite the public to ask questions.

The chapter then addresses the central tension in OSINT. Greater transparency can reveal corporate misconduct and political relationships. The same capabilities can be turned against ordinary individuals through doxxing (defined in the chapter as "publishing the identity or other personal information found about an individual to harm them, professionally or physically"). Without strict and well-intentioned data regulations, average people are poorly protected from data leaks, doxxing, and corporate mining of personal information. The chapter identifies a tension between open, transparent data as a possible human right and personal privacy as a possible human right, and suggests the tension may not be resolved until data protections for corporations and the assets they hide can be properly separated from those for natural persons.

Open data sources can also prevent governments from manipulating data and controlling information for political reasons, which is part of what made Jones's dashboard a target.

## Protecting yourself from OSINT targeting

The chapter describes two categories of defensive practice. In-person operational security (OPSEC, a term borrowed from the U.S. military) includes wearing unremarkable clothing, covering identifiable features, and using black bloc tactics. Online, protection includes keeping social media profiles private, using end-to-end encrypted messaging services, scrubbing metadata from photos and videos before sharing them, and obscuring the identities of participants in documentation of political actions.

## The nature of OSINT work

The chapter closes by characterizing OSINT investigations as requiring creativity and intuition: seeing where different datasets fit together, imagining where useful information might be found, and pursuing new sources after dead ends. Sometimes the information sought does not exist as OSINT. Layering sources, pulling in additional context, and adding small details to a pool of data can usually produce results. The chapter uses two final metaphors: OSINT resources can lock together like puzzle pieces, or develop a picture like photo chemicals used together.

## Key tools and databases mentioned

- New York City Department of Finance property records: a836-acris.nyc.gov/CP/
- New York State Division of Corporations: apps.dos.ny.gov/publicInquiry/
- OpenCorporates: opencorporates.com
- EDGAR (SEC full-text database): sec.gov/edgar/search/
- Offshore Leaks Database: offshoreleaks.icij.org
- Radio12: radio12.org
- ScanMap: scanmap.mobi/NY/
- Etsy: etsy.com

## Glossary terms defined in the chapter

- Doxxing: publishing the identity or other personal information found about an individual to harm them, professionally or physically.
- Metadata: information that describes properties of a file (image, document, sound recording, map, etc.), such as the date an image was taken, the location, and the device used. Distinct from the visible content of the file.
- Offshores (also tax havens or fiscal paradises): jurisdictions that offer attractive tax deductions and other financial benefits to foreign companies incorporating locally.
- OSINT: Open Source Intelligence. Free or inexpensive information, tools, or media accessible to average people without licenses or active permissions.
- Shell company: a company pre-registered by third parties and available for purchase by those who want a company without setting one up. Also called "paper companies." Not illicit by nature but can be used for illicit purposes, especially to obscure a beneficial owner.

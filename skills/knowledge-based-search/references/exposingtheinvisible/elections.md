---
title: Exploring Connections Between Political Parties and Personal Data Brokers in the UK
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

## Overview

This chapter, written by Amber Macintyre and published in April 2019, describes how Tactical Tech investigated the use of voters' personal data in UK political campaigns. The investigation covered the 2015 and 2017 general elections and the 2016 Brexit referendum. It is part of a broader Tactical Tech project called "The Influence Industry," which examined data-driven political campaigning across many countries including Brazil, Kenya, India, Mexico, and the United States. The UK findings are detailed separately in "Data and Democracy in the UK" (available as a PDF from Tactical Tech).

The chapter's purpose is methodological: it explains how investigators gathered and analysed evidence, rather than reporting all the substantive findings. It is aimed at people who want to conduct similar investigations elsewhere.

## The Problem Being Investigated

Political campaigns increasingly rely on detailed personal data about voters: contact information, political preferences, interests, travel routines, shopping habits, and online browsing behaviour. Data brokers and digital campaign consultants collect and process this data to build voter profiles, then sell or apply those profiles to help campaigns craft targeted messages and choose communication channels (TV, social media, door-to-door visits). The practice is not illegal by default unless data is obtained fraudulently, but it raises concerns about privacy violations, campaign law breaches, manipulative messaging, and exclusion of certain social groups through selective targeting. A key problem is opacity: voters have little visibility into what data is collected about them or how it is used.

## Research Scope and Starting Assumptions

The team examined the 2015 and 2017 general elections (for UK House of Commons seats) and the 2016 EU membership referendum. Studying all three events allowed comparison of how digital spending and tactics evolved over time and how a recurring general election differs from a one-off high-stakes referendum.

The researchers assumed from the outset that direct access to parties and campaign firms would rarely be possible, partly because campaign practices are treated as trade secrets during active elections, and partly because the Cambridge Analytica scandal had already made parties and vendors more guarded.

The chapter notes that the level of public information available in the UK, particularly from the Electoral Commission, is not matched in every country. Investigators elsewhere should check whether comparable regulatory data exists.

## Four Data Collection Methods

**1. Reading existing investigations and articles.** Investigators started by mapping prior reporting, including Guardian articles on the 2015 election's social media spending, BBC and Guardian coverage of the 2016 referendum, and a series of parliamentary hearings by the UK Department for Digital, Culture, Media and Sport (DCMS) in 2017 and 2018 on the impact of fake news. Those hearings confirmed how widespread data-driven campaign practices had become in the UK.

**2. Collecting and analysing data from UK regulators.** The UK Electoral Commission (electoralcommission.org.uk) is legally required to set spending limits for elections and to collect and publish invoices submitted by each campaign group. The Commission's database covers all official campaigning individuals and groups since 2001 and can be searched by party type, financial category (donations, loans, spending, accounts), election type, and event.

**3. Participating as a user or supporter.** Signing up to party email lists, joining campaign apps, and browsing party websites revealed data practices from the inside: what information parties collect at the point of donation, what privacy policies say about third-party data sharing, and what user data a campaign app requests (location, contacts, device type). Watching demo videos from campaign software vendors is another method. NationBuilder, used by many smaller UK political groups and local politicians, offers video demonstrations and free trials showing its data-collection and voter-profiling capabilities.

**4. Analysing self-published materials from parties and campaigners.** Blogs, press releases, industry publications, and interviews often contain concrete details about campaign tactics. For example, the blog of Dominic Cummings (campaign director of Vote Leave) described strategy in detail. In one post he wrote that Vote Leave chose to "put almost all our money into digital (~98%)" and to "hold the vast majority of our budget back and drop it all right at the end with money spent on those adverts that experiments had shown were most effective (internal code name 'Waterloo')." Such accounts are subjective and must be fact-checked, but they provide historical and technical leads. The chapter also points to the Conservative Home blog and Mark Pack's blog about the Liberal Democrats as similar first-hand party sources.

## How to Use Electoral Commission Data

The chapter walks through the process step by step.

**Obtaining the data.** The Electoral Commission database is at http://search.electoralcommission.org.uk/. Users select the type of political actor (parties, third-party campaigners, referendum participants, regulated donees) and the type of financial record (spending, donations, loans, etc.). The team ran separate searches for each of the three electoral events to keep the datasets separate. The data can be exported as a CSV file and opened in LibreOffice Calc, Excel, or Google Sheets.

**Spreadsheet columns available.** The CSV includes: Reference Number, Reporting Period Name, Regulated Entity Type, Total Expenditure, Date Incurred, Expense Category Name (overheads, transport, market research/canvassing, unsolicited material to electors, advertising, campaigning broadcasts, rallies and events, manifesto or referendum material), Supplier Name, Supplier Address, amounts split by England/Scotland/Wales/Northern Ireland, and a link to an image of the invoice. For the 2015 election, total expenditure per invoice ranged from 0.12 GBP to 528,670.21 GBP.

**Sorting and filtering.** The team filtered by specific supplier names such as Facebook and Google, and sorted the amount column to surface the largest expenditures. Pivot tables were used to aggregate spending by supplier and by category, making it possible to calculate how much a given party spent on advertising or on data-focused companies.

**Creating a custom category.** Because the Commission's own expense categories do not isolate "data" spending, the team created a custom category: "companies that received political party money for working with personal data." Building this required inspecting individual invoices.

## Investigating Invoices and Companies

Each invoice image linked in the database gives context about what a payment was for. However, many invoices are vague. The team used a two-step approach.

**Step 1: Context clues from the invoice.** An invoice for Alchemy Social, a service used by the UK Labour Party, combined with an online search, revealed that Alchemy Social is run by Experian plc, a large international consumer credit reporting company that collects and aggregates data on people and businesses and has allegedly built detailed profiles on more than a billion people. This showed that Labour's social advertising spending passed through a company whose core business is personal data aggregation.

**Step 2: Investigating the service provider directly.** When invoices lacked enough detail, the team consulted company websites, LinkedIn profiles, and official business records. In the UK, Companies House (gov.uk/get-information-about-a-company) provides free online access to business records. Searching by company name or by the name of a founder or director shows the main type of activity and the names of founders and directors, which can reveal connections to political parties or to other businesses.

The chapter describes a general structure of money flows: a political party pays Facebook directly, or pays an intermediary firm such as Alchemy Social, which in turn connects the party to Facebook using Experian's data infrastructure behind the scenes.

## Hidden Money Flows

Two mechanisms caused campaign spending to evade straightforward documentation.

**Spending routed through third parties.** Vote Leave was fined by the Electoral Commission for funnelling over 600,000 GBP to BeLeave, a pro-Brexit youth group, to avoid breaching its 7 million GBP campaign spending limit imposed by the Commission on all campaigns. This spending would not appear directly under Vote Leave's invoices.

**Services provided free by friendly companies.** If a company donates its services, no invoice is submitted to the Commission. The UK Information Commissioner found that Leave.EU used customer data from Eldon Insurance, which is owned by Arron Banks (a key financial backer of Leave.EU), to target those customers with political messages. This was uncovered through a legal investigation rather than through the Commission's database.

## Cross-Referencing and Verification

A concrete example illustrates why verification across sources matters. In May 2017, The Guardian reported that Vote Leave spent 3.9 million GBP with AggregateIQ, described as more than half its official 7 million GBP campaign budget. That figure was repeated in Business Insider and Bloomberg. The Electoral Commission's spending records show Vote Leave's total spend was 3.5 million GBP across all suppliers combined, 400,000 GBP less than the Guardian's claim. The chapter uses this discrepancy to demonstrate that even prominent outlets sometimes get figures wrong and that going to primary regulatory sources is essential.

The chapter advises investigators to follow reporters' citations back to original sources, to cross-reference multiple sources before treating a finding as confirmed, and to consider the political bias and ownership history of any news outlet they rely on.

## Expectations vs. Findings

The investigation did not always produce the results the team expected. Rather than treating this as failure, the team concluded that the gaps themselves were a finding: the lack of transparency and the incompleteness of public reporting are significant facts about the system. Identifying and reporting on those gaps became part of the investigation's contribution.

## Key Terms (from the chapter's glossary)

- **Data broker:** a company or person that uses data as an asset by collecting it from various sources including database records, polling, and social networks, and gathering it through subscriptions, purchases, and tracking cookies.
- **Data-driven campaigning:** campaign activities reliant on people's data, such as using social media data to build voter profiles and develop targeted ads.
- **Voter profiling:** a technique used to understand the behaviour, personality, and characteristics of individual voters or groups, to predict what political causes they are likely to support and what messages they will respond to.
- **Personalised content:** messaging created for specific segmented groups rather than broad audiences, personalised in text, imagery, and style.
- **Selective message targeting:** sharing messages on channels designed to reach only certain groups selected by location, profession, preferences, or other attributes.

## Resources Named in the Chapter

- UK Electoral Commission database: http://search.electoralcommission.org.uk/
- UK Companies House: https://www.gov.uk/get-information-about-a-company
- Tactical Tech report "Data and Democracy in the UK" (PDF): https://ourdataourselves.tacticaltech.org/media/ttc-influence-industry-uk.pdf
- Tactical Tech project "The Influence Industry": https://ourdataourselves.tacticaltech.org/projects/data-and-politics/
- Dominic Cummings blog: https://dominiccummings.com/
- Conservative Home blog: https://www.conservativehome.com/
- Mark Pack's blog (Liberal Democrats): https://www.markpack.org.uk/about/
- NationBuilder: https://nationbuilder.com/
- LibreOffice Calc pivot table help: https://help.libreoffice.org/Calc/Creating_Pivot_Tables
- Cambridge Analytica Files (Guardian series): https://www.theguardian.com/news/series/cambridge-analytica-files

---
title: Crowdsourcing Evidence for Investigations
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

## Overview

This chapter, written by Tetyana Bohdanova, covers crowdsourcing as a method for gathering, corroborating, and presenting evidence in investigations. It is aimed at journalists, activists, and researchers who want to engage communities in collecting information about social issues, disasters, or conflicts. The chapter defines the concept, surveys real-world examples, weighs advantages against disadvantages, and walks through an eight-step process from defining purpose to presenting findings. It gives extended attention to tool selection and security tradeoffs, verification standards, and community engagement strategy.

## What Crowdsourcing Is

The term "crowdsourcing" was coined by Jeff Howe in a 2006 Wired Magazine article, where he described it as a new way of sourcing labor enabled by the internet. The Tow Center for Digital Journalism at Columbia University defines journalism crowdsourcing as "the act of specifically inviting a group of people to participate in a reporting task (such as news gathering, data collection, or analysis) through a targeted, open call for input, personal experiences, documents, or other contributions."

Crowdsourcing has been used in journalism, crisis mapping, governance accountability, and human rights work for more than fifteen years. Wikipedia and Kickstarter are both crowdsourcing projects, drawing on collective knowledge and collective funding respectively.

## Who Uses It and How

**Journalism examples:**

- In 2022, the Bureau of Investigative Journalism and OjoPúblico mapped schools in Lima, Peru by the density of cigarette advertising near them, using images crowdsourced from across the metropolitan area. The investigation revealed that Big Tobacco companies drove this approach in Peru and similar regions while behaving differently in more regulated markets such as Europe.
- Since 2022, the Ukrainian government has run the WarCrimes platform, coordinated by the Office of the Prosecutor General, where any user can submit evidence of crimes committed by Russian military forces.
- German outlet CORRECTIV built CrowdNewsroom, a platform for collaborative investigations based on data, grievances, and suggestions from affected communities. In 2019 it investigated ownership and rent control in Hamburg's non-transparent real estate market using rental contract data collected from residents.
- In 2018, ABC Australia ran the country's largest crowdsourced investigation into aged care, gathering personal experiences from citizens.
- In 2014, Bellingcat used crowdsourced multimedia materials and crowd-verified open-source evidence in its flagship investigation into the downing of Malaysia Airlines Flight 17 (MH17) over Ukraine.

**Activist mapping (crowdmapping) examples:**

- In 2021-2023, an academic and humanitarian project in collaboration with Humanitarian OpenStreetMap (HOT) and OpenStreetMap Ethiopia crowdmapped food security in Ethiopia.
- In 2020, Harry Machmud of Humanitarian Open Street Maps used the Ushahidi platform to map handwashing stations in Indonesia during the COVID-19 pandemic.
- Since 2014, Missing Maps has used OpenStreetMap to chart disaster-affected areas lacking coverage, so that first responders and humanitarian organizations can prioritize relief.

**Governance and human rights examples:**

- Since 2016, Amnesty International has engaged at least 50,000 digital volunteers through its Decoders Initiative to help investigate human rights abuses.
- Since 2008, "I Paid a Bribe" crowdmaps anonymous reports of corruption across India and has expanded to five continents.
- Since 2007, the open-source FixMyStreet platform by mySociety collects citizen reports about street problems in the UK, maps them, and forwards them to the responsible councils.
- In 2020, women activists added services often overlooked by men to a crowdsourced map of Mexico City.

The chapter also notes that crowdsourcing is increasingly combined with Open Source Intelligence (OSINT). Ukrainian activists, for example, combine both frameworks to document the ongoing Russian military invasion.

## Pros and Cons

Crowdsourcing allows access to data that is otherwise inaccessible, engages diverse contributors, can save time and cost, and opens avenues for collaboration. The risks are data manipulation, the need for substantial know-how and resources, the possibility of coming up empty-handed, and potential safety risks for organizers and contributors. The chapter recommends weighing these carefully in each case, and considering alternatives when the cons outweigh the pros.

## The Eight-Step Process

### 1. Define purpose

Setting the goal is the key first step. The goal shapes the type of data collected, its format, the extent of verification needed, and how findings will be presented. Examples of distinct goals include: telling a complete story of an event (ProPublica's Electionland project), engaging citizens around a systemic issue (global air quality monitoring), or building a legal case (Ukraine's WarCrimes platform). Clarity at this stage makes every subsequent step easier.

### 2. Consider ethics and safety

The chapter identifies several ethics and safety dimensions: accuracy of information, privacy and security of contributors and the team, data ownership, accessibility, and legal implications. It recommends conducting a risk-based assessment and having a mitigation plan before engaging contributors. The organizer's responsibility is to ensure potential contributors understand the risks and can make an informed decision. Where anonymity is needed, the organizer must choose submission tools that protect identity and minimize metadata. Data may also need to be anonymized before further processing. The chapter notes that contributors may not always come from the population most affected by the issue. The Bureau of Investigative Journalism's crowdsourced investigation into homelessness in the UK is cited as an example.

### 3. Define audience, scope, and duration

Identifying the target audience requires thinking about demographic characteristics (age, gender, geographic location) and about whether the tools and outreach methods will reach marginalized groups or will widen existing digital divides. The chapter notes that crowdsourced data cannot be representative in a sociological sense, but that variety across locations and groups still produces a more comprehensive picture. Scope and duration follow from the goal: a project tied to a specific event has a natural endpoint. Resource constraints must also be factored in. The team must define in advance what volume of data counts as sufficient to work with.

### 4. Identify the best method

The chapter distinguishes two submission types, drawn from the Tow Center's crowdsourcing guide:

- **Structured**: A targeted request to specific groups for information in a predefined format, captured in a searchable database. This makes analysis easier but limits what contributors can submit. Example: In 2017, NPR and ProPublica published a questionnaire for women who had experienced life-threatening complications in childbirth, as part of an investigation into maternal mortality in the US.
- **Unstructured**: An open call to the public via multiple channels (email, telephone, SMS, online polling software) to submit whatever material they choose. This allows a greater variety of data from more contributors but makes verification and analysis more labor-intensive and time-consuming. Example: In 2016, a reporter at The Correspondent published an open appeal to Shell employees to share information about what the company knew about its contribution to climate change.

Large collaborative projects may combine both approaches, especially when evidence needs to be cross-referenced across multiple data streams.

### 5. Identify the right tools

The chapter cautions against selecting a tool first and designing the operation around it. Tools should be chosen based on three factors: the technical environment of the target audience (internet access, device types, digital literacy); privacy and security requirements (whether participation carries risk for contributors); and familiarity (users are reluctant to change established habits, so using platforms they already know reduces friction).

The chapter provides a detailed table of secure communication tools with their characteristics and tradeoffs:

- **Signal** (signal.org): Free, open-source, end-to-end encrypted messaging for iOS and Android, developed by Open Whisper Systems. Records virtually no metadata. Requires users to register with a phone number, though an alias option is now available. Less widely used than WhatsApp.
- **PGP email encryption**: An encryption standard using public key cryptography, popular among journalists. Each user has a public key (shared openly) and a private key (kept secret). Software implementations include GPG Suite (Mac), GPG4win (Windows/Linux), Thunderbird with the Enigmail extension, and Mailvelope. Requires technical knowledge.
- **ProtonMail** (protonmail.com): Free email with PGP integration built in, usable without technical training. Uses zero-access encryption, meaning ProtonMail itself cannot read stored emails. However, emails sent to external addresses are not end-to-end encrypted by default, so sensitive communication should stay within the ProtonMail service.
- **SecureDrop** (securedrop.org): Open-source whistleblower submission system for news organizations. Allows completely organization-owned servers, minimizes metadata, encrypts data, and enforces strong security practices. Used by The New York Times, The Washington Post, ProPublica, The Globe and Mail, and The Intercept. Available in 20 languages. Costly and technically demanding to set up.
- **Tella** (tella-app.org): Free, open-source mobile data collection application designed for limited internet connectivity and high-risk environments. Available on Android in multiple languages. Customizable but requires user training and backend server setup.
- **OnionShare** (onionshare.org): Peer-to-peer file transfer tool. Requires a separate communication channel to coordinate. Better suited to small-scale initiatives or working with individual whistleblowers than to large crowdsourcing campaigns.
- **Tresorit** (send.tresorit.com): Free file sending (up to 5 GB per link), end-to-end encrypted. Proprietary code, but audited by third parties. Links are not password-protected by default, and intercepted links can expose data.

On WhatsApp and Telegram: WhatsApp stores phone numbers, is owned by Meta, and shares user phone numbers and analytics with Meta. It can be compelled to share data in response to court orders, subpoenas, or law enforcement requests. It may also back up unencrypted messages to iCloud or Google Drive (a feature that can be disabled). An end-to-end encrypted backup option is available. Telegram is widely used but its closed-source code means security experts cannot verify its safety.

### 6. Engage the target audience

Community engagement is described as "half the success" of a crowdsourcing effort. Key recommendations:

- Account for the social and political conditions in which contributors operate. If participation carries risk, people will only engage if they believe tangible change may result. Closing the feedback loop with the audience (including anonymous contributors) matters.
- Precede the call for submissions with awareness-raising and trust-building work: information campaigns, outreach to opinion leaders, engagement with the most active community members.
- Create a "snowballing effect" by securing early contributions immediately after launch. When potential contributors see others actively participating, they are more likely to join. Some initiatives publish data their own members collected alongside submissions from the audience. Others mix crowdsourced data with OSINT-collected data. If different collection methods are combined, the publication must differentiate between data types.

Examples cited: The Global Investigative Journalism Network lists community meetings and listening events as effective outreach methods. Internews provides resources through its Listening Post Collective. "Wall Evidence," a project crowdsourcing photos of inscriptions left by Russian soldiers in Ukraine, first published photos documented by its own members in the Kyiv and Chernihiv regions, then invited residents to submit more. Documentary filmmakers of "Anyone's Child: Mexico" set up a free telephone line through which families affected by the drug war could share stories, and callers could also listen to other contributors' stories.

### 7. Develop a verification protocol

The chapter describes verification as important and treats it as a process that must be designed before submissions arrive, not after.

Steps recommended:

- Decide in advance what level of verification is enough for data to be published.
- If data cannot be fully verified, vet it by cross-referencing against other sources and asking: Do the contributions resemble what was expected? Is there other verified information that confirms this data directly or indirectly? Is the data arriving at the expected time (reports of voting irregularities cannot arrive before polls open)? Is the data coming from expected locations?
- Clearly mark unverified data in any publication. State the extent of verification transparently.
- Supplement crowdsourcing with other data collection methods when possible: drone footage, satellite imagery, field teams.

The chapter warns that crowdsourcing carries an inherent risk of manipulation, particularly against malign actors using bots or organized user campaigns to corrupt data. If data appears intentionally corrupted, the organization should consider whether to publish at all.

Example: The Russian election violation crowdmapping platform "Karta Narusheniy," run by the independent election monitoring organization Golos, publishes user-submitted reports of voting irregularities without additional verification, clearly labeling them as such. When a serious incident is uncovered, a mobile field team investigates on the ground. Golos was disbanded under pressure from the Russian government and now operates as an unregistered civil movement.

### 8. Analyse data and present collected evidence

The final audience and the contributors may be different groups. Findings should be presented in a format accessible to the intended audience, which may in turn influence the submission format chosen earlier. Presenting data honestly and truthfully is described as essential for credibility. This requires describing both the data collection methods and how conclusions were reached, and clearly stating whether and to what extent data has been verified. The chapter also recommends thinking of the "story" the data tells and presenting it in an engaging way.

Example cited: "I Paid a Bribe" highlights a map of India by report density, publishes individual reports in real time, totals them by category, and provides an overview of resulting news publications.

Example cited: NPR and ProPublica's "Lost Mothers: Maternal Mortality in the US" series, built from crowdsourced personal stories.

## Collaboration Opportunities

Crowdsourcing can reveal other groups or activists working in the same space. The chapter recommends checking for existing efforts before launching, to avoid duplicating data and to enable cross-referencing. Partnerships can also produce mixed data collection approaches that neither partner would have developed alone. Example: ProPublica's Electionland project for the 2020 US elections assembled a coalition of over 150 newsrooms and ran a public call to voters, poll workers, and election administrators to report problems via multiple channels.

## Crediting Contributors

Credit should be given to collaborating organizations, tools and software used, and named contributors if they consent. The organizer must weigh the risks of naming contributors, ensure everyone is aware of those risks, and protect the anonymity of anyone who needs it. Example: Amnesty International and Airwars listed and credited all partners, tools, and major contributors in their investigation into civilian deaths during the 2017 bombing of Raqqa, Syria (published at raqqa.amnesty.org).

## Closing Argument

The chapter concludes that crowdsourcing represents a democratization of information gathering, turning evidence collection into a community-driven activity that connects media, civil society, and affected groups. Combined with OSINT and other methods, it provides a way to document dynamic events, address local concerns, and expose systemic injustice. At the same time, the chapter stresses that crowdsourcing must be conducted ethically, fairly, and responsibly to protect the integrity of information, safeguard contributors, and ensure positive impact on communities.

The chapter was published in May 2024 and was written by Tetyana Bohdanova. The author also produced a workshop curriculum titled "Crowdsourcing Information for Investigations" for Exposing the Invisible and Tactical Tech.

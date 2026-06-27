---
title: The Making of an Anti-biometric Mass Surveillance Campaign
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
use_when: An agent needs concrete tactics for investigating, exposing, or campaigning against government surveillance deployments, including FOI denial handling, evidence archiving, community organizing, petition infrastructure, and crowdsourced verification.
---

## Context

Case study by Filip Milosevic, SHARE Foundation (https://www.sharefoundation.info/en/). 18-month campaign in Belgrade, Serbia against a Huawei-supplied facial recognition camera network (8,000 cameras). The government announced the system in January 2019 without public discussion. The campaign ended with the government withdrawing a proposed law to legalize the system.

## Phase 1: Initial Research

**FOI requests as evidence, not just information.**

SHARE Foundation sent Freedom of Information requests to the Serbian Ministry of Interior requesting camera locations, the analysis behind location selection, and procurement details. The Ministry replied that procurement documents were classified "confidential." The denial became the story: it was published via press release to independent media and framed as the starting point for public debate.

A denied FOI request is publishable evidence of opacity, not a dead end.

**Finding what governments hide through corporate sources.**

After the FOI denial, researchers searched publicly available sources. Huawei had published a detailed case study on its own website describing the Belgrade deployment and its cooperation with the Ministry of Interior. The Serbian government had withheld this information while the vendor published it for marketing.

As soon as the Foundation analyzed and published the Huawei material, Huawei removed the case study from their site.

**Web archive retrieval as an investigative step.**

The team retrieved the deleted Huawei page from two archives:

- Archive Today: https://archive.li/pZ9HO
- Wayback Machine: https://web.archive.org/web/20190313232443/https://e.huawei.com/en/case-studies/global/2018/201808231012

Related Kit guide: https://kit.exposingtheinvisible.org/en/how/web-archive.html

When a vendor or government removes a page that was previously indexed, check Archive Today and the Wayback Machine immediately. Save new captures before publishing to prevent the same loss.

## Phase 2: Community Infrastructure

**Minimum viable campaign infrastructure:**

1. Single-page HTML microsite with ASCII art (tool: https://manytools.org/hacker-tools/convert-images-to-ascii-art/), a few strong sentences, several supporting links, a contact form, and a Telegram channel link.
2. A domain name that doubles as a hashtag: www.hiljadekamera.rs / #hiljadekamera ("thousands of cameras" in Serbian).
3. A Telegram channel (chosen because privacy-aware audiences already use it).

The microsite contained only enough content for everyone to read, enough to make the point, a few links for deeper reading, and one clear action: fill in the contact form.

**Street-level tactics:**

- Stickers styled to look like official surveillance warning signs (police are legally required to mark surveilled areas but were not doing it). Placed on camera poles. Each included a QR code linking to the campaign site. Official appearance reduced removal by city services.
- Art installation at an open city festival: a comfortable bench with two dummy cameras (red blinking LEDs) positioned above it. A QR code on a caption plate linked to a short questionnaire about how people felt being under surveillance ("Would you share secrets to a friend, would you dance, lie down, kiss or sext your partner under these cameras?"). The bench drew people at a crowded festival where seating was scarce, forcing engagement with the surveillance framing.

## Phase 3: Collaborative Sprint Event

After approximately one year of research, the team organized a one-day sprint event with 30 confirmed volunteers to build a full campaign website.

**Recruitment:** Returned to the contact form from the microsite (50+ submissions including help offers from visual artists, web designers, developers, researchers, journalists, and lawyers). Sent invitations to around 60 people (half known personally, some through mutual contacts, some from the form). Sent a second single-page ASCII site as an event explainer.

**Working group structure:**

- .TXT: researchers and journalists writing human-readable content from gathered information
- .EXE: engineers visualizing and explaining the architecture of smart surveillance systems
- .PDF: lawyers and advocates analyzing legal issues and strategizing at policy level
- .MAP: developers building a crowdsourcing application for camera location mapping
- .HTML: web designers integrating all outputs into the new website

**Logistics:** free community space gallery with tables, chairs, electricity, wi-fi. Morning coffee and croissants, fruit throughout, pizza later. The space was kept simple and comfortable so people felt safe discussing sensitive topics.

**Output in 8 hours:** all textual content, visual identity, infographic concept for the surveillance system architecture, several iterations of the mapping application.

**Final website:** https://hiljade.kamera.rs (also available in English)

**Independence policy:** the campaign refused organizational funding to avoid geopolitical bias accusations. Financial support came only from crowdfunding.

## Phase 4: Public Mobilization (Three Calls to Action)

### CTA 1: "The Hunt" (camera crowdsourcing)

The Ministry had not published camera locations. The campaign asked citizens to submit photos of surveillance cameras with locations.

**Mechanics:** Citizens sent photos via Twitter with the campaign hashtag, or directly via email. The team did not use an open-form submission app to avoid spam. Incoming submissions required manual verification, but this kept data quality high.

**Campaign page:** https://hiljade.kamera.rs/lov/ with basic instructions, graphics of camera models ("how to recognize a camera that recognizes you?"), and a temporary map.

**Why Twitter over an app:** Citizens' public posts drove organic promotion of the campaign account and demonstrated active engagement to media.

### CTA 2: "Reclaim Your Face" (petition against biometric surveillance)

Organized with European Digital Rights (EDRi, https://edri.org/) and other European organizations simultaneously across multiple countries.

**Avoided generic petition platforms for three reasons:**

1. Petition saturation on social media limits visibility.
2. Standard platforms sell email addresses and have data leaks, trackers, and cookies.
3. Generic design prevents tailored functionality and engagement.

**Built a custom petition platform** that was private by design (no trackers, localized privacy policy), translated and color-coded per country, embedded in each organization's own site. Most assets were created collaboratively across organizations and then localized.

**Result:** thousands of signatures in the first hours. After several days, nearly 10,000 new email list subscribers who had opted in while signing (no dark patterns). This mailing list became the campaign's most important communication tool, replacing dependence on Facebook, Twitter, and other gatekeepers.

The petition's primary long-term value was not signatures but the opt-in email list it generated.

### CTA 3: "Together Against Thousands of Cameras" (crowdfunding)

Run during the holiday season. In collaboration with two local streetwear brands, the campaign designed and sold masks, beanies, bandanas, and hoodies. This also served as a brand-awareness mechanism.

Crowdfunding goal was initially 5,000 Euro (reached in one day during pre-release to family and friends), then raised to 10,000 Euro, also reached before the deadline. Platform used: https://www.donacije.rs/projekat/hiljade-kamera/

## Phase 5: Multimedia Production

**Formats used (ranked by reach):**

1. Short video documentary (up to 15 minutes): filmed cameras around the city, key campaign actions, interviews with initiative members and the National Data Protection Commissioner. Used drone footage and music from local artists. Aired on at least three cable TV stations multiple times. Cable TV stations will air free content that fits their aesthetic and time slot needs.
2. Live-stream event on YouTube, produced to avoid "Zoom fatigue." Setup: grey backdrop, several light panels, one DSLR camera, one webcam, one computer, all fed into OBS (Open Broadcasting Software, https://obsproject.com/) via HDMI capture cards. Format: host plus five activists on-site speaking back to back on different segments, four external guests via video call (journalist, security professional, technology expert, law expert), then a live Q and A.
3. Podcast: experimental, streamed a few thousand times, valued by niche communities.

**PR philosophy:** zero paid advertising. No payments to Facebook, Google, or similar platforms. Content spread entirely organically.

## Evidence and Narrative Techniques

**Cross-referencing surveillance data with other government databases** to communicate concrete risks: metadata retained from protest attendance could be cross-referenced against public sector employment databases, social aid recipient lists, or small business tax records to deny people jobs, scholarships, or kindergarten admission for their children, or to coerce their votes years later.

**Chilling effect as a concrete, demonstrable concept:** during 2020 Belgrade protests, government officials publicly threatened to use surveillance footage to identify protesters, which reduced turnout. This provided a real-time example to explain self-censorship dynamics in media appearances.

**Leak from the surveillance system** (footage leaked during the campaign): when SHARE asked the Ministry to confirm, they did. This became evidence that the system's data was not secure, usable in every subsequent communications moment.

## Verification and Monitoring Tactics

- Monitor government websites for draft laws posted without media notification. The Ministry posted a draft law legalizing biometric surveillance on its own website with less than three weeks' public comment period and no press notification. The Foundation found it one week before the deadline.
- Monitor public hearings at national assemblies. A Ministry representative confirmed at a public assembly hearing (21 May 2021) that facial recognition would not be activated without public debate and an assembly vote. This became a public commitment on record.
- File comments on draft laws formally. SHARE comments on the withdrawn draft: https://www.sharefoundation.info/wp-content/uploads/Draft-Law-on-Internal-Affairs_Comments_SHARE-Foundation.pdf
- Alert international and community media simultaneously when a draft law surfaces. Combined with EDRi's international network, this created pressure across multiple jurisdictions.

## Key Tactical Principles

- Decentralized, leaderless campaign structure increases participant ownership and prevents single points of failure.
- A denied FOI is publishable evidence of government opacity.
- Corporate promotional materials (case studies, press releases, technical whitepapers) often contain what governments classify. Search vendor sites and archive them immediately after finding.
- Email lists outperform social media followers because they are not controlled by platform gatekeepers.
- Custom petition infrastructure with opt-in email collection is more valuable than generic platform petitions.
- A campaign name that works as a domain, a hashtag, and a brand identity reduces cognitive overhead across channels.
- Visual content and a concrete call to action are what media appearances require. Prepare them before outreach.
- Financial independence (crowdfunding only) removes attack vectors about foreign funding or geopolitical bias.

## Resources Referenced

- "10 Tactics for Turning Information into Action": https://archive.informationactivism.org/basic1.html
- CIVICUS Campaign Toolkits and Guides: https://www.civicus.org/index.php/media-center/resources/toolkits
- SHARE Foundation Anti-Biometric Surveillance Campaign website: https://hiljade.kamera.rs/en/home/
- EDRi (European Digital Rights): https://edri.org/
- OBS (Open Broadcasting Software): https://obsproject.com/
- Archive Today: https://archive.li/
- Wayback Machine: https://web.archive.org/
- ASCII art tool: https://manytools.org/hacker-tools/convert-images-to-ascii-art/
- Chilling effect explainer: https://www.eff.org/deeplinks/2016/05/when-surveillance-chills-speech-new-studies-show-our-rights-free-association
- Dark patterns reference: https://datadetoxkit.org/en/wellbeing/darkpatterns/
- Kit guide on web archives: https://kit.exposingtheinvisible.org/en/how/web-archive.html
- EDRi summary of Serbia withdrawal: https://edri.org/our-work/serbia-withdraws-a-proposed-biometric-surveillance-bill-following-national-and-international-pressure/

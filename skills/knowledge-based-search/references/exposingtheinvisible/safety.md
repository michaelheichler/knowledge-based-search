---
title: Safety First: Digital, Physical, and Psychological Safety for Investigators
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

## Overview

Safety is not a checklist to complete before an investigation begins. It is an ongoing mindset woven into every decision an investigator makes. This chapter covers three interlocking areas: protecting the people you work with, protecting yourself, and protecting the data you collect. It applies equally to online research and to physical fieldwork, and it treats digital and physical safety as inseparable.

## Do No Harm

The foundational principle is borrowed from the humanitarian sector: every action and behavior produces consequences, positive or negative or both. The goal is to avoid introducing more risk and harm than already existed. A simple formula captures this: **Actions + Behaviours = Consequences**. Applying it means asking, at every step, how a planned action could affect sources, collaborators, the investigator, and the information at stake.

## What You Are Protecting

Three categories need protection.

**Contacts.** Sources, collaborators, colleagues, and anyone else whose information you access, collect, use, or store. Their safety is your responsibility while you hold their data.

**Yourself.** Your own physical, digital, and psychological safety must be actively managed throughout an investigation.

**Data.** Information you collect must be shielded from unauthorized access and must be recoverable if a device is lost, damaged, or stolen.

## Context Determines Threat

There is no universal safety setup. The threats that matter depend on who or what you are investigating, where you are working, and what methods you are using. Searching NGO reports from home carries different risks than interviewing people in a conflict zone. Online and offline risks are linked: what you do digitally can affect physical safety, and physical exposure can compromise digital security. Safety must be approached holistically and cannot be addressed in isolation from the safety of others you work with.

In short: safety is about the function you perform and the context in which you perform it. It cannot be divided neatly into digital and non-digital, and it cannot be addressed in isolation from the people you work and communicate with.

## Risk Assessment and Risk Mitigation

Before starting any investigation, list the anticipated risks. This is risk assessment. Then develop a plan to prevent, respond to, and resolve each problem. This is risk mitigation. The plan should be revisited throughout the investigation as circumstances change.

The more complex or dangerous the activity, the more thorough the assessment needs to be. There is no single required template. Individual investigators must adapt the process to their methods, context, and investigation subject. Investigating alone demands extra care. The chapter recommends always collaborating with trusted others, because collaboration improves mitigation.

A threat matrix from Tactical Tech's Holistic Security manual frames the core idea: threats are assessed by two factors, the likelihood they will occur and the impact if they do. Higher likelihood or higher impact means higher risk.

Recommended external resources for risk planning:

- Surveillance Self-Defence from the Electronic Frontier Foundation (ssd.eff.org)
- Pre-assignment Preparation from the Committee to Protect Journalists (CPJ)
- Risk Management for NGOs from UNDP Somalia (generally applicable)
- DSD Working Papers on Research Security, for dangerous field contexts
- What to Do When Authorities Raid Your Home, from the Global Investigative Journalism Network (GIJN)
- Holistic Security manual from Tactical Tech, particularly the chapter "Identifying and Analysing Threats"

## Digital Safety

Digital safety has two goals: preventing unauthorized access to data, and ensuring data can be recovered if lost.

The data at risk includes contacts, location, passwords, and digital habits. It can be exposed through devices, communications, online accounts, and internet traffic.

A critical point in the chapter: tools alone are not enough. Most breaches come from human behavior, not technical failures. What you choose to share, how you communicate, what links you click, which services you use, and who you share information with all matter more than which app you install. Digital safety is a group responsibility. If a collaborator's device is compromised and holds the same data as yours, your own precautions may be undone. Sources must also be made aware of the risks.

### Practices to Protect Credentials and Data

- Use long passphrases.
- Use two-factor authentication.
- Use a password manager to store credentials.
- Set up account recovery options such as a recovery email.
- Back up data regularly.
- Encrypt data.
- Prefer tools with end-to-end encryption, which prevents even the service provider from reading content.
- Know who has access to your data.
- Assess every tool before using it.

### Evaluating a Digital Tool

Five criteria to check before adopting a tool:

1. **Open source.** Is the source code publicly available? Open code can be independently audited even by people who cannot read it themselves. (Open source means the code is available to read. Source code is the human-readable instruction set for a program.)
2. **End-to-end encryption.** Data is encrypted before transmission and only the recipient can decrypt it, not the service provider.
3. **Minimal data storage.** The tool collects only what it needs to function. Excess stored data is excess exposure.
4. **No data leakage.** No unnecessary data is exposed to the public or third parties during normal use.
5. **No data sharing.** The tool does not sell or share user data with third parties. Check the Terms of Use and Data Policy.

### The Security Trade-off

Every tool choice involves a balance between security, usability, and functionality. A highly secure tool may require a password on every use. A more convenient one may save credentials and become a liability if the device is stolen. The key is identifying your weakest points rather than reinforcing your strengths, because weaknesses are what get exploited. "The devil is in the defaults" means that default settings usually favor convenience over privacy.

### Data and Device Encryption

Encrypt devices using full disk encryption. Full disk encryption means the entire storage medium is unreadable without decryption first, not just a portion of it. Recommended tools: Bitlocker (Windows), FileVault (macOS), dm-crypt (Linux), VeraCrypt, or Cryptomator for file-level encryption. Back up data to both cloud storage and physical hard drives.

### Online Research and Browsers

Online investigation leaves traces. Use a separate browser for research and a different one for personal browsing. This practice is called compartmentalization. Do not log in to personal email or social media in your research browser.

Test your browser's fingerprint resistance with Cover Your Tracks (coveryourtracks.eff.org). Even without logging in, browsers can be fingerprinted using settings like window size and system information. Some mitigations involve changing behavior (such as opening different-sized windows) or using tools that obfuscate system information.

**Recommended browsers:**

- **Tor Browser.** The best privacy-protective browser. Open source, masks IP address, encrypts traffic. May be blocked or banned in some jurisdictions. Tor Bridges can work around some blocks. Some websites block Tor by default. The chapter describes it as having a built-in way of changing your IP address and encrypting your traffic, and notes it can also bypass internet filters.
- **Firefox.** Built-in Enhanced Tracking Protection. Set Content Blocking to "Strict" to activate it, as it is off by default. Your IP address remains visible to the sites you visit.
- **Brave.** Privacy-protective defaults without needing extensions. Has a Shields feature to block ads and trackers. Offers a "Private Tab with Tor" mode that routes traffic through the Tor network and allows access to .onion sites (sites that end in .onion and are configured to be accessed only by Tor-enabled browsers). Keep the Brave Payments feature disabled, as it sends data that could identify you.
- **DuckDuckGo.** A privacy-aware search engine, not a browser. Claims not to collect personal data about users. Does save search queries but not in a personally identifiable way. Can be combined with Tor Browser for additional privacy. Customize settings at duckduckgo.com/settings.

### Accounts

When services require account creation, limit exposure by:

- Using a compartmentalized email account through services like Tutanota or Protonmail.
- Creating separate social media accounts for investigative work to keep it separate from your personal online identity.
- Creating a single-use identity for a specific investigation and discarding it afterward, especially for sensitive work.

### VPNs

A VPN (Virtual Private Network) masks your IP address by routing traffic through the VPN provider's server. Sites you visit see the VPN's IP, not yours. It is less effective than Tor for anonymity but useful when Tor is unavailable or blocked.

The chapter explains VPNs with a phone-call analogy: visiting a website is like making a phone call. Your IP address is your "number." A VPN creates a tunnel so that the site, your ISP, and the web browser cannot see your real IP. Traffic looks like it originates from the VPN provider's location rather than yours. This matters in scenarios like repeatedly visiting a corporation's board of directors page, which normally gets little traffic, where your repeated visits from a specific location could alert the company to your research.

Choose VPN providers that claim no-log policies. Most free VPNs fund themselves by selling users' traffic logs. Recommended no-cost or low-cost VPNs: Bitmask, Riseup VPN, Psiphon, Lantern. Safety Detectives is suggested for more balanced VPN analysis, as most VPN reviews are not independent.

Note: verify that using encryption is legal in your jurisdiction. Some countries restrict encryption use.

### Secure Communication

Intercepted communication is one of the highest risks in investigative work.

- Use **PGP (Pretty Good Privacy)** for email. PGP encrypts the content of an email but not its metadata. Metadata includes the sender, receiver, subject line, timestamps, and header information. All of that remains readable even when message content is encrypted.
- For calls and messages, use **Signal** or **Wire**. These are preferred over WhatsApp or Telegram. Signal and Wire are not available everywhere. Wire is blocked in some regions.
- When forced to use unencrypted calls or landlines, share only the minimum necessary information. Establish in advance what details are less risky to communicate.

Mobile phones are inherently trackable. Network providers know the location of every device on their network at all times. GPS, Wi-Fi, and Bluetooth expand that tracking further and allow more third parties to access location data. If you believe your phone is monitored, consider a burner phone: a disposable device not linked to your identity, used briefly and then discarded.

Bringing more devices into the field improves your ability to collect and manage information but increases tracking risk. A smart phone is always a tracking device. A device might take you safely to a meeting and back, but it might expose your source forever. Make conscious choices about what to bring, and do not take risks on behalf of others.

The Guardian Project (guardianproject.info) produces vetted, security-focused mobile apps.

**Metadata** is "data about data": information that describes the properties of a file. For an image, the visible content is the data. The date, location, and device information captured by the camera are its metadata. Metadata can expose where a photo was taken or reveal identifying information about the photographer or device.

## Field Safety

Physical fieldwork carries risks that desktop research does not. Travel, filming, and using certain equipment can draw attention in sensitive contexts. Planning and risk assessment remain essential even when an activity seems low-risk. Have a clear plan established in advance. Know your important contacts and which individuals or organizations could provide assistance in the field.

Key considerations for field safety:

- **Assess source vulnerability explicitly.** If your investigation involves confidential or vulnerable sources, address the risks they face in your assessment. Discuss with them the vulnerabilities they may face while collaborating with you.
- **Sequence information collection carefully.** Start with background research and lower-risk interviews or fieldwork. Progress to higher-risk activities as your understanding grows. Always reassess risks as you go.
- **Protect confidentiality.** Disclosing sensitive information about your investigation or your sources can put you and collaborators at risk depending on the context and issues you are researching.

## Key Terms

- **Full Disk Encryption (FDE):** Encrypting an entire storage medium so that it is unreadable without decryption first, not just a portion of it.
- **Metadata:** Data that describes the properties of a file, such as the date, location, and device recorded alongside a photograph.
- **Open source:** Software whose underlying code is publicly available to read and audit.
- **Source code:** The human-readable instruction set for a program.
- **Tor Browser:** A browser that disguises identity and protects web traffic from many forms of internet surveillance. Can also bypass internet filters.

## Resources Cited

Articles and guides:
- Holistic Security manual (Tactical Tech): holistic-security.tacticaltech.org
- Surveillance Self-Defence (EFF): ssd.eff.org
- Security in a Box: securityinabox.org
- Data Detox Kit: datadetoxkit.org
- Pre-assignment Preparation (CPJ): cpj.org
- What to Do When Authorities Raid Your Home (GIJN)
- De-escalate Anyone, Anywhere, Anytime (RightResponse.org)
- DSD Working Papers on Research Security (SSRC)

Tools:
- Cover Your Tracks: coveryourtracks.eff.org
- Guardian Project: guardianproject.info
- VeraCrypt, Cryptomator (file and disk encryption)
- Signal, Wire (encrypted messaging)
- Tor Browser, Brave, Firefox, DuckDuckGo (browsers and search)
- Bitmask, Riseup VPN, Psiphon, Lantern (VPNs)
- Tutanota, Protonmail (encrypted email)
- PGP (email encryption)

*Chapter published August 2020, updated November 2021.*

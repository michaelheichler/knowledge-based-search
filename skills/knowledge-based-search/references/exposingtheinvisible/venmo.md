---
title: Extracting Information From Social Apps: A Case of Exposed Financial Data
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

## Overview

This chapter, written by Hang Do Thi Duc, is a first-person account of an investigation into Venmo, a US mobile payments app owned by PayPal. The chapter demonstrates how a publicly accessible API allowed anyone to download hundreds of millions of user transactions without authentication, what that data reveals about individuals, and how to handle such data responsibly. It also covers the technical steps used for data collection and the digital security practices required when holding sensitive information about other people.

## The Problem: Public by Default

Venmo is a social payments app. When users send or receive money, they can attach a text message to the transaction. By default, those transactions, along with the sender's name, the recipient's name, their profile links, and the transaction message, appear in a public feed visible to anyone in the world. Dollar amounts are not shown, but everything else is.

Hang Do Thi Duc registered on Venmo in May 2015. She later discovered that all of her transactions had been displayed publicly without her realizing it. She changed her settings immediately, but the experience stayed with her.

By 2018, millions of users were still sharing transactions publicly. Their real names, profile links, and in many cases their Facebook IDs (linked at signup) were all visible, enough to reconstruct a detailed map of a person's social network and daily habits.

Her project, PublicByDefault.fyi, set out to show how much private information Venmo users were unknowingly sharing with the world, and to put pressure on the company to change the default setting.

## The API: No Authentication Required

The key technical fact is that Venmo's public API required no authentication. An API (application programming interface) is the mechanism by which a platform makes its data accessible to external developers. Platforms typically require an API key, user permission, or registration to limit access. Venmo required none of these. Its public API was simply a URL: `venmo.com/api/v5/public`.

This was discovered by developer Dan Gorelick, who documented it in a blog post from October 2016. He found it by inspecting the "Network" tab in a browser's developer console while browsing venmo.com. Venmo's only restriction was a rate limit, meaning it limited how quickly requests could come from a single source.

## Collecting 207 Million Transactions

Hang Do Thi Duc's goal was to download all public Venmo transactions from the year 2017. The strategy involved making one API request per minute of the year.

**Converting timestamps.** The API accepts time ranges expressed as UNIX epoch timestamps (seconds elapsed since 00:00:00 on 1 January 1970). She converted human-readable dates to epoch format using a tool called Epoch Converter, which can be accessed via Tor Browser without a CAPTCHA.

**The request format.** A sample request looked like this:

```
http://venmo.com/api/v5/public?limit=2000&since=1483228800&until=1483228860
```

This retrieves up to 2,000 transactions between 1 January 2017 00:00:00 and 00:01:00. She made 525,600 such requests (365 days x 24 hours x 60 minutes), with a one-second overlap between consecutive requests to avoid missing transactions at the boundary.

**Infrastructure.** She wrote scripts in Node.js to make requests and store results. Her laptop went offline frequently while traveling, so she rented a Virtual Private Server (VPS) running Ubuntu for 26 euros per month. After a few days, Venmo's rate limit started blocking that server. Her solution was to rent three additional, smaller servers to share the request load and distribute traffic across different IP addresses. Within about two weeks she had collected all 2017 public transactions: 207,984,218 in total.

**Storage.** She stored the data in MongoDB, a document database that holds data in JSON format as key-value pairs. MongoDB was installed on each VPS. Once collection was complete, she merged all databases onto the most powerful server. She used Google and DuckDuckGo for research help, and Stack Overflow for developer questions (both accessible via Tor without CAPTCHAs).

**Each transaction record contained:**
- Payment ID
- Permalink (permanent link to the transaction on venmo.com)
- Username, first name, last name, profile photo link, and account creation date for both sender ("actor") and receiver ("target")
- Date and time of the transaction
- Type (payment or charge)
- Transaction message
- Likes and comments

## Analyzing the Data

Before analysis she cleaned the dataset by removing duplicates created by the one-second overlap in requests. She then added a MongoDB index to the "message" field to speed up searches.

She queried the data by writing MongoDB queries. For example:

```
db.collection.find( { message: "🏠💸" } )
```

This returns all transactions containing the house and money-with-wings emojis, which Venmo's autocomplete suggests when users type "rent."

Her investigative questions included:
- What are the most common words and emojis in transaction messages?
- Who had 1,000 or more transactions in 2017, and what did they spend money on?
- Are there users who made many transactions of the same type?
- Which transactions received the most likes and comments?
- Are there pairs of users who only sent money to each other?

She used Robomongo and Studio 3T as graphical tools for querying MongoDB and exporting data. She exported results as JSON and CSV. She built her final PublicByDefault.fyi website using HTML, CSS, and JavaScript with libraries including jQuery, PixieJS, GSAP, D3.js, Lodash, and Moment.js.

## What the Data Revealed

About 350 users had 1,000 or more transactions in 2017. Most were small businesses accepting Venmo payments. The data exposed intimate details about real people, including:

- A cannabis retailer whose transaction history, combined with his customers', disclosed the neighborhood where he operated.
- A couple whose Venmo exchanges documented the entire arc of their relationship from affection to conflict.
- A woman whose daily fast food and soda purchases formed a pattern that would flag her as a health risk to an insurance company. (The chapter notes that insurance companies are known to scan social media to build risk profiles of current and potential clients.)

The chapter makes the point that the aggregate of small, innocuous-seeming data points can reconstruct someone's location, habits, finances, health, and relationships in detail. This makes the data valuable to data brokers, health insurers, financial institutions, and law enforcement. For investigators looking into corruption, bribery, or money laundering, the same dataset could reveal financial links between individuals or organizations.

## Impact and Venmo's Response

PublicByDefault.fyi launched in July 2018. It received coverage from The Guardian, Ars Technica, and other outlets. Around the same time, a Twitter bot began automatically tweeting Venmo's public transactions, drawing additional attention.

Venmo responded with three changes:
1. It added privacy reminder pop-ups informing users that their transactions are public.
2. It significantly reduced the rate at which data could be retrieved from the public API, making bulk collection at scale no longer possible.
3. It disabled the "since" and "until" date parameters, making it impossible to request historical transactions.

However, as of early 2019 (the publication date of the chapter), the default setting remained public and the public API still existed. The rate limit could still be bypassed by running multiple servers with different IP addresses.

In August 2018, Bloomberg reported that PayPal executives were considering whether to remove the public transaction feature entirely. In September 2018, Mozilla delivered a petition with over 25,000 signatures calling on Venmo to change its privacy defaults. In early 2019, computer science student Dan Salmon independently replicated the process and scraped seven million transactions across six months, confirming that the data remained accessible.

The chapter closes this section by noting that Venmo is not exceptional. Many platforms share user data publicly or with third parties by default. The author's view is that a payment service should treat privacy as a design priority from the start ("privacy by design"), and that it had not done so.

## Ethical Dilemmas

The chapter addresses a contradiction at the center of the project: exposing a privacy failure required processing and re-publicizing private data. This amplified the harm it was meant to illustrate.

The author's resolution was to withhold all real names, usernames, and profile pictures from the final published output. This kept the focus on the platform's design flaw rather than on the individuals affected. She also chose to retain the full dataset locally and not share it with anyone, and she urges other investigators to think carefully about what to do with sensitive data after publication ends.

Her earlier work included Data Selfie (dataselfie.it), a browser extension that showed users what Facebook might infer about them from their own data. The extension no longer exists but illustrates her broader interest in making data collection legible to the people it concerns.

## Digital Security When Holding Other People's Data

The chapter concludes with a practical security guide for investigators who hold sensitive datasets. The core principle is to store sensitive data locally rather than on remote servers or cloud services, and to encrypt it.

**Three questions to answer before storing sensitive data:**
1. What tool will encrypt data on your computer or phone?
2. What tool will encrypt data on an external storage device?
3. What password will you use?

**Full disk encryption by operating system:**
- Mac: FileVault (built in, recommended for all Mac users)
- Windows: BitLocker (available only on Pro and higher editions, which is a reason to buy the Pro version)
- Linux: LUKS (Linux Unified Key Setup), ideally configured at installation time
- iPhone: "Data Protection" is on by default
- Android: "Encrypt device" setting, which may need to be activated manually

For cross-platform use, VeraCrypt is a free, open-source tool that encrypts a specific folder and works on Mac, Windows, and Linux. Security-in-a-Box provides tutorials for using it on each platform.

**Encrypting external drives.** Each operating system can reformat a USB drive or external hard drive with encryption enabled (Mac Disk Utility, Windows BitLocker, Linux "Disks" tool). The limitation is that a drive encrypted on one OS is not readable on another, which is another reason to consider VeraCrypt for cross-platform work.

**Passwords.** Encryption is only as strong as the password protecting it. A strong password must be:
- Long: at least 16 random characters mixing symbols, lowercase, uppercase, and numbers. Passwords using words or personal information must be much longer.
- Not in any dictionary, including cracking dictionaries that contain common phrases, song lyrics, alternate spellings (like "alt3rn@t1ve"), and similar patterns.
- Unique to each device or account.

One recommended technique is "diceware": select several random words and string them together to form a passphrase.

## Key Resources Named in the Chapter

- PublicByDefault.fyi: the project website with anonymized stories from the research.
- Dan Gorelick's blog post "Scraping Venmo" (October 2016): the document that identified the public API endpoint.
- Epoch Converter: the tool used to convert human-readable dates into UNIX epoch timestamps.
- MongoDB and Node.js: the database and scripting tools used for collection and storage.
- Robomongo and Studio 3T: graphical tools for querying MongoDB and exporting results.
- Ubuntu: the Linux distribution used on the virtual servers.
- Stack Overflow: developer Q&A site used for troubleshooting.
- VeraCrypt, FileVault, BitLocker, LUKS: encryption tools.
- Security-in-a-Box: resource for VeraCrypt tutorials.
- D3.js, jQuery, PixieJS, GSAP, Lodash, Moment.js: JavaScript libraries used to build the final website.
- Data Selfie (dataselfie.it): the author's earlier browser extension for self-inspection of Facebook data.

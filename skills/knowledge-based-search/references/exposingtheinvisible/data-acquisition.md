---
title: Data Acquisition for Beginners
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

By Lylla Younes.

Data acquisition is the process by which researchers find and gather information. The central challenge is that data is frequently not available in a ready-to-analyze form. It may be scattered across PDF files, embedded in a webpage table with no download button, or nonexistent and in need of creation from scratch. The chapter covers the main file types a researcher will encounter and four concrete methods for getting data into machine-readable format.

## Why data acquisition matters

Investigative work often depends on converting raw, inaccessible information into structured data. The chapter offers three examples. ProPublica built a database of credibly accused priests. The Guardian's "The Counted" project documented every police killing in the US in 2015 and 2016 by combing local news clippings. Ad.watch collects data on political ads across Facebook, Snapchat, Instagram, and other platforms to show the scale of voter targeting.

## File types and machine-readable formats

Machine-readable data is information structured so that computer software or a programming language can process it. An unstructured text file cannot be opened in a spreadsheet and displayed in rows and columns. Any data intended for computer analysis must be machine-readable.

**Delimited files (CSV and TSV).** A CSV (comma-separated values) file stores each row of data as a line, with commas separating each field. A TSV (tab-separated values) file uses a tab character instead. The separating character is called a delimiter. Files may carry the extension .csv, .tsv, or .txt, or no extension at all. Delimited files are easy to read, write, and move between software and programming languages.

**JSON (JavaScript Object Notation).** JSON is primarily used to transmit data between a website and a server. It is human-readable, editable in a text editor, and can be compressed to a single line, making it lightweight (faster for programs to read).

**Shapefiles.** Shapefiles (extension .shp) are used for mapping and geospatial analysis. They store geographic features as points, lines, or polygons and typically come in a folder containing multiple related files.

## Opening delimited files in Excel

The chapter uses a concrete example: downloading a water-quality data file from the USGS (United States Geological Survey) water data portal (https://waterdata.usgs.gov/nwis). The file has no extension. Opening it in a text editor (Sublime Text is recommended, free and open-source with syntax highlighting) reveals that columns are separated by tabs.

Steps to import into Excel:

1. Add the extension .txt to the file so Excel recognizes it.
2. Remove the first 75 or so lines of header notes (copy them to a separate text file for reference, then delete them from the original).
3. Open a new Excel workbook, click File > Import, select "Text File," and click Import.
4. Select the file, choose "Delimited," click Next, then Finish, and accept the default cell location.

The result is a clean spreadsheet ready for analysis. The same process applies to any delimited file. LibreOffice and Apache OpenOffice offer similar import functionality. Google Sheets runs in a browser and can crash or slow on large files (such as a file with a million rows).

## Scraping tables from webpages with Google Sheets

When data appears in a table on a webpage and there is no download button, copying and pasting often produces jumbled output. Google Sheets provides the built-in function IMPORTHTML, which scrapes tables or lists from a webpage directly into a spreadsheet.

The function takes three arguments:

1. The URL of the page, in quotation marks.
2. The type of structure: "table" or "list", in quotation marks.
3. The number of the table or list on the page, without quotation marks (1 for the first table, 2 for the second, and so on).

Example using a Wikipedia table of historical nuclear weapons stockpiles:

```
=IMPORTHTML("https://en.wikipedia.org/wiki/Historical_nuclear_weapons_stockpiles_and_nuclear_tests_by_country","table",1)
```

Punctuation must be exact. Type the formula into cell A1 of a new Google Sheet and press Enter. The data appears in clean tabular form and can be downloaded for further analysis.

## Extracting tables from PDFs with Tabula

PDFs often contain pages of tables that are not machine-readable. Writing Python code to scrape them is one option, but it requires programming knowledge. Tabula is a free, open-source alternative that requires no coding. Its stated purpose is "liberating data tables locked inside PDF files." It opens in a browser window rather than as a standalone application. If it does not open automatically after launch, navigate to http://localhost:8080.

Steps to extract a table:

1. Download Tabula from https://tabula.technology/ for your operating system. Installation instructions appear halfway down the page.
2. Open Tabula by double-clicking the icon (it launches in the browser).
3. Click Browse, locate the PDF, and click Import. Uploading may take time for large files.
4. Once the PDF preview appears, click AutoDetect Tables. Tabula highlights the detected table area with a semi-transparent red rectangle. Drag the corners manually if the selection is off.
5. Click Repeat This Selection to apply the same selection area to every page in the document.
6. Click Export to download the data as a CSV file, which can then be opened in Excel.

AutoDetect Tables works best when all tables in the document share the same layout. A commercial alternative, Comet Docs (https://www.cometdocs.com/), requires a paid subscription.

## Retrieving data from APIs

An API (Application Programming Interface) is a software tool that lets a user send a request to a remote server and receive structured data in return. The chapter uses the metaphor of an internet post office: you send a request and receive a parcel of data.

Every webpage is stored on a remote server. When a browser requests a URL, the server processes the request through its API and sends a response. Some organizations publish their APIs with documentation, enabling anyone to request data directly. Examples mentioned: Google's Geocoding API (geographic data), Spotify's API (metadata about artists, songs, and albums from Spotify's catalog), a weather API at weatherapi.com, PredictHQ's weather forecasting API (used by Uber and Alaska Airlines), and TomTom's Traffic API (traffic flow and incidents in over 77 countries). The Twitter API has been used by journalists to study public opinion and the spread of misinformation. In 2023, Twitter made drastic changes to its free API, including aggressive limits and removal of features, making it much less useful.

Key vocabulary:

- Base URL: the root URL of the API, to which parameters are appended.
- Parameters: values appended to the URL to specify what data to request. Some are required.
- API key: a unique identifier issued when you register for access, used to authenticate requests. An API key is almost always a required parameter.
- Query: the act of requesting data from an API.

Digital safety note: when signing up for an API key or any online service used for investigation, the chapter recommends creating an email address not connected to a personal or regular work account.

### Practicing with the Holiday API and Postman

The chapter demonstrates API requests using the Holiday API (https://holidayapi.com/) and Postman, a free desktop tool for building and sending API requests without writing code.

Steps:

1. Sign up at https://holidayapi.com/signup and obtain a free API key from the account dashboard.
2. Read the API's developer documentation (the Developers tab) to find the base URL and required parameters. The Holiday API requires three: the API key ("key"), the country code ("country"), and the year ("year"). Country codes must follow ISO 3166-1 alpha-2 (two-letter) or ISO 3166-1 alpha-3 (three-letter) format. States and provinces use ISO 3166-2 format. The full list of supported countries and codes is at https://holidayapi.com/countries.
3. Create a Postman account and download the desktop application.
4. In Postman, click "+ New," then "Request." Give the request a name and optional description.
5. Add the request to a Collection (a named folder for organizing requests). Click "+ Create Collection," name it, click the checkmark, and click Save.
6. Under Query Params, enter each required parameter and its value: key (your API key), country (for example "BR"), year (for example "2019").
7. Click Send.

The API returns a response in JSON. JSON data is organized as key-value pairs, with each key on the left of a colon and the value on the right. In the Holiday API response, a "status" key with value "200" confirms success. The key "holidays" contains a list of all holidays for the requested country and year, with each holiday as a JSON object holding metadata (name, date, and related fields). The response can be saved as a JSON file using the Save Response button.

The chapter closes by noting that APIs cover data as varied as shipping routes, geographic locations, and social media activity, and that learning to query them is a broadly applicable skill in investigative work.

## Glossary of key terms (as defined in the chapter)

- **API**: a software tool that facilitates communication between a user and a dataset. Platforms can make data accessible to external developers for free or under conditions and fees.
- **Data acquisition**: the process by which you find and gather information.
- **Data wrangling**: converting data from its raw, unstructured form to a form analyzable by computer software and programming languages.
- **Hashtag**: a metadata tag using the # symbol on social networks, letting users find messages on a specific theme.
- **Machine-readable data**: information in a form that can be processed by computer software or a programming language, typically organized in a format like CSV or JSON.
- **Metadata**: information that describes properties of a file, such as the date, location, and device on which an image was taken.
- **Programming language**: a formal language with a set of instructions for producing output. Python is an example. Like a human language, programming languages have syntax (rules for how to write code).
- **Python**: a programming language used for web applications, websites, and data analysis tools.
- **Scraping**: extracting data from human-readable content (such as a webpage) into a machine-readable format like CSV.
- **Server**: a computer program or hardware device that provides a service to another program and its user (the client). A typical service is providing data to other computers.

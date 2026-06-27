---
title: Geolocation Methods: A Step by Step Guide
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

## What Geolocation Is and Why It Matters

Geolocation means identifying the exact geographic location of an object or event on the Earth's surface, typically by finding its latitude and longitude coordinates. Applied to photos and videos, it means determining where in the world the image was captured.

Latitude measures north-south position from the equator (0 degrees), ranging to 90 degrees N or S. Longitude measures east-west position from the prime meridian (0 degrees), ranging to 180 degrees in either direction. Coordinates can be written in degrees/minutes format (52 degrees 31.86797' N), degrees/minutes/seconds format, or decimal format (52.5311329 lat, -13.4005015 long), where north and east are positive and south and west are negative.

Geolocation matters to journalism and open source intelligence (OSINT) because it answers the questions of where and when an event occurred. Confirming location is often key evidence that an event happened or did not happen as claimed. It enables journalists to map military conflicts, track movement of forces, follow criminal activity across locations, and verify transfers of equipment between countries.

OSINT (Open Source Intelligence) refers to free or inexpensive information, tools, or media accessible to ordinary people without special licenses or permissions.

## Mapping Services

Several free mapping services are available for geolocation work.

**OpenStreetMap (openstreetmap.org)** is a non-profit mapping project maintained by volunteers, sponsored by universities and organizations. It does not track users, allows downloading of its mapping databases, and is designed to be shared and built upon.

**Google Maps, Google Earth, and Google Earth Pro** are commercial services from Alphabet (formerly Google Inc). Google Maps includes Street View, a technology providing 360-degree ground-level images captured by Google vehicles or uploaded by users. Street View is navigated by placing the "yellow man" icon on a street.

**Satellites.pro** aggregates multiple map providers in one interface. It also displays names of neighborhoods, villages, and small towns within the visible screen frame, which is useful for finding local place names and their transliterations.

**World Imagery Wayback** (livingatlas.arcgis.com/wayback) is a free historical photo archive from ESRI. The rate of photo updates varies by provider input.

**Sentinel** (apps.sentinel-hub.com/eo-browser) provides satellite imagery updated frequently (approximately three to four times per week) but at lower resolution than the other services.

All services except Sentinel offer high-resolution satellite imagery. Using multiple services gives access to images taken at different times and with varying levels of detail, which helps build a reliable geographic overview and a more accurate timeline of events. Satellite imagery has limitations: laws, government censorship, and deliberate blurring restrict access to high-resolution images in some regions, including areas around military installations, contested territories, and locations of endangered species.

## The Four-Phase Methodology

Every geolocation case is unique and may require different methods and tools. The author frames the process as solving a puzzle, requiring both a way of thinking and a set of tools. The methodology has four phases.

**Phase 1: Collect information.** List all details visible in the image or video without filtering for apparent usefulness. This is a visual scan. Also collect surrounding context: details about the incident, its circumstances, when it occurred, and what commenters or sources say about it.

**Phase 2: Process information.** Classify the collected details to decide where to begin searching. The key question is which element offers the best starting point. Fixed elements (a store name, a building, infrastructure) are preferable to movable elements (a license plate, a vehicle) because fixed elements are more likely to remain in the same location over time.

**Phase 3: Search.** Use the selected starting element to search, whether by looking it up in Google Maps, doing a reverse image search on the whole image, or cropping a portion of the image to focus on a specific detail. The search will produce candidate results that need to be compared against the original.

**Phase 4: Check result.** Verify whether the search findings match the original image. If the result is negative (no match), repeat the four phases using a different element or a different tool. Each attempt informs the next: for example, if a shop name turns out to have multiple branches in multiple countries, a license plate can be used to narrow the country or city, and the shop search can be repeated within that area. A car with a plate registered in Belgrade, Serbia could be parked in Cairo, Egypt, so plates confirm registration region, not current location. The process of choosing starting points changes with every case based on available information. Success depends on collecting the most information possible and being patient in searches.

## Reverse Image Search

Reverse image search lets users search by uploading or linking an image rather than typing keywords. Results quality varies by engine. Tools mentioned in the guide:

- TinEye (tineye.com)
- Yandex Images (yandex.com/images)
- Bing Visual Search (bing.com/images)
- Google Images / Google Lens (google.com/imghp): Google Lens can recognize text, faces, buildings, and clothing within an image and search for them. It also allows the user to select specific areas of the image to focus the search.

Reverse image search can locate the original publication of a photo and surface news articles with additional location details, which can replace or complement direct mapping searches. Within Google Lens results, "find image source" retrieves the original publication rather than visually similar images.

## Case Study 1: Beginner Level (Badrawy Hospital, Alexandria, Egypt)

The task was to locate a photo showing two buildings of different colors with air conditioners and shower trays visible on the facade, and a board reading "Badrawy Hospital."

Collect: The hospital name on the board is the most important element. Process: A fixed named institution is the best starting point. Search: A Google Maps search for "Badrawy Hospital" returns results in Egypt, specifically pointing to Badrawy Hospital in the Smouha area of Alexandria. Check: Comparing the Google Maps photos of the Smouha branch to the original image reveals no match. The facades are completely different.

Repeating the search reveals multiple branches. Searching for "Badrawy Hospital 2" finds a branch in the Sidi Beshr area of Alexandria. Google Maps has no photos of this branch, so Street View is used. The "yellow man" icon is placed on the street in front of Badrawy Hospital 2. Adjusting its position via the small screen on the left side of the interface produces a matching facade view.

Outcome: The photo was taken in front of Badrawy Hospital 2, Sidi Beshr, Alexandria. A search for "Badrawy Hospital fire" surfaces news articles confirming a fire at that hospital in June 2020 in which Covid-19 patients died.

Alternative method: A Google Images reverse search of the original photo leads through "find image source" to an article in Al-Youm Al-Sabe newspaper published June 29, 2020. The article describes a fire at a private hospital in Bishr area, Mohamed Naguib street, Alexandria, and provides the address directly.

## Case Study 2: Average Level (Egyptian Armored Vehicles and a Libya Claim)

In June 2020, a Facebook video showed Egyptian military vehicles on a highway, with users claiming the convoy was heading to Tobruk, Libya.

Collect: Several military vehicles bear the Egyptian flag. The road is wide, suggesting a highway. A gas station with a distinctive blue sign appears in the video. A Toyota vehicle is also visible. Process: The gas station is the best starting point because it is a fixed building with a distinctive sign.

Search: The video quality does not allow reading the station name directly. A Google search for "Egypt gas station" and comparison of logo images identifies the blue sign as belonging to Al Taawun (CO-OP Egyptian) gas stations. Since the claim involves equipment heading to Libya, the search is narrowed to Al Taawun stations along the western coastal road connecting Egypt to Libya. This returns approximately 12 results. The video shows a building before the station and a building under construction after it, followed by vacant land. Reviewing the 12 candidate stations one by one, a station near the village of Ras Hajjaj matches those structural features. Google Maps imagery confirms the match.

Outcome: The gas station is located approximately 250 kilometers from the Libyan-Egyptian border. While the vehicles face westward, all Egyptian army camps on the western border are in that region. The geolocation contradicts the claim that the equipment was in Libya or in Tobruk.

## Case Study 3: Advanced Level (Russian Military Equipment in Kherson, Ukraine)

A video dated March 4, 2022 circulated on Telegram (channel ukraina24tv) claiming Russian forces with vehicles marked with the letter Z were advancing into the center of Kherson, Ukraine, approximately 300 meters from the city's central administration building.

Collect: Military vehicles with the letter Z (associated with the Russian invasion of Ukraine). A perpendicular intersection of two secondary streets. Sidewalks with a walkway, then trees, then asphalt. Buildings with triangular roofs. Taller buildings visible behind the shorter triangular-roofed ones. The claim specifies Kherson city center, 300 meters from the central administration building. Process: There are no large distinctive store or building signs to use as search anchors. The method must rely on the street layout and building geometry.

Search: The approach is to convert the ground-level videographer perspective into an overhead (bird's-eye) view that matches what maps show. A large circle is drawn around the administration building on the map and the area inside is examined for intersections with: crossroads, sidewalks with green areas roughly as wide as the road itself, buildings with triangular roofs, and taller buildings beyond. This requires careful, patient review of candidate streets.

Check: A location matching all these features is found at coordinates 46.64468827846318, 32.61594308344351. Additional verification uses Google Maps photos of the area. A photo of a government building at the opposite intersection matches the scene in the video.

Outcome: The geolocation confirms that Russian military equipment had approached Kherson city center on or around March 4, 2022.

## Conclusions

Methods and tools vary case by case, but the four-phase way of thinking applies universally. Determining a location can take minutes or hours. Team collaboration helps confirm details and find solutions. Combining reverse image search, direct geolocation, and historical satellite image search not only verifies information but also helps construct a timeline of events and understand how a situation developed.

The guide was originally authored in Arabic by M_osint and translated into English.

---
title: Using Maps to See Beyond the Obvious
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

By Alison Killing.

## What This Chapter Covers

Maps, satellite imagery, and geographic data let investigators see connections that are hard or impossible to establish from ground level. From above, you can see how a series of factories line a railway, notice a pattern of illegal deforestation, identify the surroundings of a mine, or assess damage after a disaster. Maps and satellite images can also let you see over walls and into places that are restricted, unsafe, or physically distant.

This chapter covers maps of physical geography only, not abstract diagrams showing company or personal relationships. Any data that can be tied to a place on earth can be placed on a map. This includes natural features such as rivers, coastlines, and elevation. It also includes administrative data such as country and county boundaries, aerial photographs from satellites and drones and balloons and kites, and databases with location information such as hospital addresses or country population figures.

The term "geodata" means digital information directly linked to a geographic location. Large amounts of geodata are freely available online, often already assembled into maps. Investigators can also generate their own geographic data using drones, kites, balloons, tape measures, or a phone's GPS. The main software this chapter uses is a web browser, a spreadsheet application, and Google Earth Pro (free to download and install). All tools are free or low-cost and designed to be learned quickly.

Most investigations have at least one geographic component. The company or person being investigated has a physical location. Evidence from social media may carry location metadata. Deforestation has a clear link to a particular place. Creating maps, using geodata, and geolocating evidence can help verify or challenge other sources of information.

## Reference Map Platforms

**Google Maps** supports route planning, satellite view, Street View, and location photographs.

**Google Earth Pro** uses satellite imagery rather than a drawn map as its background. It adds historical satellite imagery, 3D terrain and building models, and a layer system that you can switch on and off. It must be downloaded and installed. The browser version does not have all the same features.

**Waze** is a community-driven navigation and traffic app developed between 2006 and 2009 and bought by Google in 2013. It operates independent maps with real-time traffic, accident data, and other information contributed by users. It runs on Android and iOS.

**Bing Maps** (owned by Microsoft) is a good alternative to Google Maps. It offers satellite view, bird's eye view, road view, and streetside imagery for some places. It is strong on traffic data and distance planning. Its map data is powered by HERE technology (originally developed by Nokia) plus postal data and other proprietary sources.

**HERE WeGo** (owned by HERE Technologies) is built on the same HERE technology as Bing Maps. It provides satellite view, terrain view, route planning, and traffic updates.

**OpenStreetMap (OSM)** is a free, crowdsourced map platform created through contributions from a large number of people and organisations. Coverage is incomplete in some parts of the world, so verify information by checking other maps. OSM is generally considered reliable, and many other platforms such as Mapbox and Ushahidi use its data. In some instances, OSM may have more information than proprietary maps. It includes specialist layers for cycling routes and a humanitarian layer showing locations of camps for displaced people. In 2009, OSM was used by a group of young Kenyans to create the first map of Kibera, a Nairobi neighbourhood that had been a blank space on all official maps (Map Kibera project: http://mapkibera.org/).

**OsmAnd** uses OSM data but is independent from OSM. Its mobile app (Android and iOS) works completely offline once maps are downloaded and includes foot, hiking, and bike paths. It provides satellite imagery from Bing. It is useful for off-road terrain.

**Open CPN** (Open Chart Plotter Navigator) is free, open-source software developed by sailors for water navigation. It provides navigation and route planning, weather conditions, tides, vessel tracking, and collision avoidance. Available for Linux, Mac, Windows, and Raspberry Pi. Installation guide: https://opencpn.org/OpenCPN/info/quickstart.html.

**Yandex Maps** is a Russian web mapping service available worldwide but with detailed maps only for Russia, Belarus, Ukraine, Turkey, and Kazakhstan. It is worth checking alongside other platforms for those regions, as it may provide additional detail.

**Baidu Maps** (owned by Baidu) provides more detailed coverage of China than Google Maps. It includes satellite imagery, street maps, street view, and route planners for walking, driving, and public transit. All Google services are blocked in China, making Baidu the primary mapping resource for work there. It works on mobile and desktop.

**CartoDB** (now Carto) is a location intelligence platform offering web mapping, GIS, and spatial data tools. The paid tier costs around $200 per month. Free options exist for students via the GitHub Student Developer Pack and for educators, startups, and nonprofits. Free Carto Basemaps are available. Carto is known for its SQL database support and strong visualisation tools.

**Mapbox** lets you plot data points on custom map tiles and create symbol, heat map, and choropleth maps. A free tier is available.

**TileMill** is an open-source map design studio that uses CartoCSS, a map design language. It can produce symbol maps, choropleths, and pseudo heat maps.

Most mapping platforms obscure certain areas, such as military bases, which may be blurred or covered with clouds. If an area is obscured on one platform, check others.

**Wikimapia** is an open-source map platform that incorporates imagery from multiple providers including Google, Bing, and Yahoo, and lets you switch between them with a single button. This is useful when a feature is obscured or low-resolution on one provider and visible on another.

## Finding Images of a Place

**Google Images advanced search** lets you filter results by the country from which an image was uploaded. This does not mean the images are of that country. It means they were uploaded from an IP address there. Still, searching for "street art" with country set to Brazil will return more Brazilian street art than a general search. Access this under Settings > Advanced search at https://images.google.com/, then use the "region" field.

**Street View** provides 360-degree ground-level imagery stitched together from photographs. It is useful for planning a research trip, confirming a company's physical presence, or identifying fictitious addresses (a registered address that does not exist on the map, or a derelict building with no activity).

Google Street View is accessible inside Google Maps (not Google Earth). It was originally limited to roads but now includes paths in national parks and other areas. The capture date appears in a grey box at the top left of the screen. Verify information from multiple platforms before drawing conclusions, because imagery can be out of date.

Coverage gaps in Google Street View: it is restricted to major cities in Germany and Austria by local privacy regulations, with additional blurring of faces and licence plates. Coverage is limited or absent in Belarus, Moldova, Paraguay, Venezuela, DR Congo, Sierra Leone, and many other regions for political or accessibility reasons.

**Historical Street View** is available for some locations. Click the clock icon in the top-left grey box to open a slider and navigate earlier images. This shows how an area has changed, when a company moved in or out, or the progress of construction. Historical imagery is not maintained consistently and may be removed without notice. If historical imagery is relevant to your investigation, take screenshots immediately.

**Yandex Street View** covers Russia, Ukraine, Belarus, Kazakhstan, Armenia, and Turkey, often with more detail than Google in those regions. Historical imagery is available but mostly restricted to the same countries.

**Baidu Street View** covers major Chinese cities but not rural areas.

**YouTube dashcam videos** can substitute for street view in countries with little coverage. Drivers in some countries film their journeys and share the footage online. Search for "dashcam [city name]" and filter results by location or date.

## User Photos in Google Maps and Google Earth

Users have uploaded thousands of photographs to both platforms, including images of places excluded from Street View.

In **Google Maps**, click "Photos" in the left sidebar to browse. Navigate with the double-arrow icons. Click and hold the Street View person icon to reveal locations covered by Street View and small circles showing 360-degree photo locations. Drop the person icon on a circle to open that photo. The date and photographer appear in the top-left box. Clicking the photographer's profile photo takes you to their Google Maps photo page, where you can see all their photos by date and location.

In **Google Earth Pro**, enable the "Photos" layer in the sidebar to see photo icons on the map. Clicking a photo icon shows the image and the photographer's profile photo. To find the date, click the profile photo to open their Google Maps page, select "sort by date" in the sidebar, scroll down until the relevant location appears on the map, click the pin, and the date appears in the status bar and the top-left box.

For 360-degree photos in Google Earth Pro (shown as red icons), click the icon, then click "view this image on 360 cities" to open it on https://360cities.net, where you can view it as a spherical image and find the date it was taken and uploaded.

## Thematic Maps: Already-Mapped Data

Thematic maps show information related to a specific subject such as air pollution, forest cover, or election results.

Many organisations publish their data as interactive maps. The following are examples by category.

**Shipping traffic:**
- Marine Traffic: a live map of vessel positions using Automatic Identification System (AIS) data. Ships that do not carry AIS transponders, including those below a certain size and most military and coastguard vessels, do not appear. Satellite AIS data often requires a paid subscription.
- Global Fishing Watch: positions and historical data for approximately 300,000 of the largest commercial fishing vessels. Access is free but requires a free account. The chapter recommends using a dedicated email address rather than signing in via social media, for privacy reasons.

**Flight traffic:**
- Flight Radar: a live map of commercial aircraft positions with flight numbers and route information.
- FlightAware: real-time flight status for most commercial flights worldwide, plus charter and private planes in the US and Canada. Free service.

**Forest cover:**
- Global Forest Watch: a map of changing tree cover worldwide from 2010 to the present.

**Air pollution:**
- European Environmental Agency: a live map of air quality across Europe covering particulate matter, carbon monoxide, ozone, nitrogen dioxide, and sulphur dioxide. Updated hourly.
- World's Air Pollution (https://waqi.info): a live global air quality map with links to individual countries' monitoring agencies.

**Mining and resources:**
- USGS Worldwide Mineral Resources Online Spatial Data: historical data on global mineral resources including mine ownership, provided by the US Geological Survey. Some information is outdated. Raw data downloadable at https://mrdata.usgs.gov/mrds/.

**Humanitarian:**
- UN Cartographic Division: maps related to humanitarian and peacekeeping operations.
- UNHCR maps portal: maps of current refugee situations and displacement areas, typically updated weekly. Available at https://data2.unhcr.org/en/situations.

**Economic and development:**
- World Bank data portal: an online visualisation tool at http://databank.worldbank.org/data/source/world-development-indicators/preview/on lets you view datasets as maps. Select a dataset, then click the map button at the top right.

**Corruption and financial:**
- Transparency International: Global Corruption Index and Corruption Perception Index available as interactive maps and downloadable data.
- Tax Justice Network Financial Secrecy Index: map and downloadable data at https://fsi.taxjustice.net/download-data/.

## Making Your Own Thematic Maps

To create a map from data, the data must be geo-referenced, meaning linked to a place through a country name, region, street address, postcode, or GPS coordinate.

**Types of thematic maps:**
- Choropleth: regions are coloured to show a statistical difference, such as voting percentages or life expectancy.
- Symbol map: symbols of different sizes and colours are placed on locations, useful for showing two or more datasets together (for example, earthquake locations and magnitudes).
- Heat map: shows variation in intensity, such as how air pollution differs across a city.

**Visualisation tools:**

Datawrapper makes choropleth and symbol maps. It has a wide range of built-in base maps and accepts uploaded maps if the one you need is not included. To keep a map private, stop at the "visualise" step and do not publish. The map then stays under "my charts." Once published, it can be viewed up to 10,000 times before payment is required. Datawrapper also includes bar charts, scatter plots, area diagrams, pie charts, and tables. It is an online tool and requires an internet connection.

Tableau Public makes choropleths, symbol maps, heat maps, origin/destination maps, and flow maps. It requires desktop installation. Both the data you use and the maps you create are public on the free tier, so do not use it for sensitive or embargoed data.

QGIS is free, open-source, and more complex than the other two tools. Data and maps remain private. It is powerful and can be used offline. Basic functions can be learned in about a day. Resources include the QGIS user guide, the Gentle GIS Introduction, and the QGIS curriculum from the Spatial Query Lab. Maps created in QGIS are typically exported to graphic design software for final colour and text adjustments before publication.

**Questions to ask before choosing a tool:** Will the maps be public or private? Will the underlying data be made public? Does the tool include the base data you need (electoral boundaries, country outlines)? Is there a limit on the number of maps you can create? Can you style the map to match a publication's style guide?

**Data sources for building your own maps:**
- United Nations Data: health, environment, finance, food, agriculture, energy, trade, education, and more, all linked to countries and in some cases spanning decades.
- World Bank, World Trade Organisation, International Monetary Fund.
- Eurostat: data from EU member states, candidates, and other countries, harmonised for comparability.
- National government statistical departments: most countries publish datasets. Brazil's IBGE and Moldova's Statistica Moldovei are examples. Wikipedia lists national and international statistics services.
- Transparency International and Tax Justice Network: see above.
- Global Fishing Watch raw data: available at https://globalfishingwatch.org/datasets-and-code/.

## Drawing, Measuring, and Analysing in Google Earth Pro

Google Earth Pro lets you overlay data on satellite imagery, draw on the map, and measure features. It is free and keeps all imported data private.

**Placemarks** mark specific locations for your investigation. To add one: Add > Placemark, or click the drawing-pin icon in the toolbar. Drag the pin to the correct location while the dialogue box is open. You can add a name, lat-long coordinates, descriptive text, photographs, and links. Searching for a place name or lat-long in the search bar also creates a placemark that can then be saved.

**Drawing and measuring tools** open via Tools > Ruler or the ruler icon in the toolbar. Units can be changed between metric and imperial.

- Lines: measure the straight-line distance between two points.
- Paths: a series of connected lines forming a route. The "show elevation profile" option adds a cross-section showing terrain changes along the route, with a slider that moves a red arrow along the path to show elevation and incline at any point.
- Polygons: closed shapes that report area and perimeter. Use this to measure the size of a forest clearing or a building footprint.
- Circles: drawn from a centre point with a specified radius. Useful for finding everything within a certain distance of a point (all villages within 30 km of a hospital, or all public transport stops within a 5-minute walk, using a 400 m radius).

Anything drawn can be saved to the Places panel for future reference.

**Average travel speeds for rough estimates:** walking is typically taken as 5 km/h (3 mph). In Copenhagen, where a wide range of people commute by bike, the average cycling speed is 15.5 km/h (9.6 mph). A reasonably fit cyclist on a flat road with a racing bike averages around 25 km/h.

**Route planning tools:**
- Google Maps Directions: covers walking, cycling, driving, and public transport. You can set a departure or arrival time to check journeys in the recent past (a few days reliably) or plan future ones. More detail is available on the desktop version than in the mobile app.
- Rome2Rio (https://www.rome2rio.com/): covers all transport modes including flights. It breaks each trip into stages and gives transport companies, journey times, and indicative prices for each leg.

**3D terrain and buildings** can be enabled in the sidebar under "Terrain" and "3D Buildings." These layers use significant processing power and can slow image loading, so keep them off when not in use. To reach a ground-level view, zoom in until the altitude in the status bar drops to around 20 m or lower. Google Earth then shifts to a ground-level perspective from which you can pan and move around.

3D models are useful not only for familiarising yourself with a place before visiting, but also for geolocating photographs by confirming the view from a specific position.

**Saving high-resolution images from Google Earth Pro:** File > Save > Save image. Maximum resolution is 4800 x 4800 pixels. To stitch multiple images together without distortion, first go to Tools > Options > "3D view" tab and set the elevation exaggeration to 0.01. This flattens the projection and prevents edge distortion when tiling.

## File Formats for Geographic Data

**KML/KMZ:** KML (Keyhole Markup Language) is the main format used in Google Earth for points, lines, and polygons. Open via File > Open. KMZ is a compressed version of KML. A free tool converts Excel files to KML format for Google Earth.

**SHP (shapefile):** one of the most common map formats, used by a wide range of applications. It stores geometric data (points, lines, polygons) together with a database of attributes describing each feature. A shapefile is actually a collection of files. The essential ones are .shp, .shx, and .dbf, and they must stay in the same folder. Shapefiles are typically downloaded as a .zip archive and can often be imported directly as a .zip. In Google Earth: File > Import.

**CSV (comma-separated values):** a simple database format that can be opened in most spreadsheet applications. To place CSV data on a map, it must contain location information such as lat-long coordinates or addresses. In Google Earth: File > Import, then specify the delimiter and whether location data is coordinates or addresses. If only addresses are available, Google Earth geocodes them using Google Maps data, but the results may need verification. Multiple entries with identical coordinates do not necessarily mean events happened at the same location. This pattern can indicate where the information was logged (a police station, for example) rather than where each event actually occurred.

**GeoTIFF:** an image format that contains embedded georeferencing information. Import it into GIS software such as QGIS and it places itself at the correct location automatically. An accompanying .tfw file stores scale and location information and must be kept in the same folder.

**JPEG:** a common format for photographs, satellite imagery, and scanned maps. Does not contain embedded georeferencing.

**DWG/DXF:** technical drawing formats used by architects, engineers, and graphic designers. They contain geometric information but are not always georeferenced. Importable into most map applications.

**Geoconverter** converts between common map data formats.

## Collecting Your Own Location Data

Latitude and longitude (lat-long) coordinates divide the earth into a grid. Latitude measures how far a place is north or south of the equator (0 degrees, with the north pole at 90 degrees N and the south pole at 90 degrees S). Longitude measures how far east or west a place is from the prime meridian (0 degrees), up to 180 degrees in either direction.

Coordinates appear in three formats:
- Degrees/minutes: 52 degrees 31.86797 minutes N, 013 degrees 24.03009 minutes W
- Degrees/minutes/seconds: 52 degrees 31 minutes 52.0784 seconds N, 013 degrees 24 minutes 01.8054 seconds W
- Decimal: 52.5311329 lat, -13.4005015 long (north and east are positive, south and west are negative)

Conversion tools include Earthpoint, latlong.net, Calculator Soup, and Google Maps (which converts automatically when you search).

**Marking a location on Google Maps on your phone:** press and hold a point on the map to drop a pin. The lat-long appears at the bottom of the screen. Copy it or take a screenshot immediately, as Google may not save it in a way you can easily retrieve. Google provides six decimal places of precision, which theoretically resolves to 11 cm. In practice, satellite imagery resolution makes this accuracy hard to achieve. For detailed surveys of small areas, use a tape measure, pen, and paper.

**Safety note:** Several common apps including Google Maps and WhatsApp allow real-time location sharing. This can be useful as a safety check so a colleague can monitor your position during fieldwork. It also creates risk if others with an interest in your whereabouts can access the data. Only share your location with people you trust. For sensitive investigations, disable location tracking under "Location Settings" on your device and consider using a printed map and written notes instead.

**Route tracking:**
- Google Maps Timeline (Menu > Timeline): shows your movements throughout the day. The calendar in the top-right corner lets you review previous days. Routes are rough but arrival and departure times for specific places are accurate.
- OsmAnd Trip Recording plug-in: records your full route via the phone's GPS and measures distance covered. Works completely offline.
- Fitness apps: take frequent, precise location readings and record elevation. Nike Running Club is given as an example. These apps use a lot of battery.
- External GPS receivers such as the Bad Elf GPS for Lightning connector (iOS) and the Globalstat Micro USB for Android provide more consistent data than a phone alone.

**Importing GPS tracks into Google Earth:** Tools > GPS, or File > Import. Supported formats include .gpx, .loc, and .mps from devices such as Garmin and Magellan.

**Low-tech survey of a small area:** materials are pen, paper, and a tape measure. Sketch the area in plan view (2D from above). Measure wall lengths, the distances between features, and diagonals. Diagonals confirm whether shapes are truly rectangular. Mark which way is north. Photograph the area panoramically from multiple positions and take close-ups of key features such as damage to a window or graffiti on a wall. This method is used by architects and engineers and is the most accurate approach for small-area detail.

**Larger area survey:** record lat-long coordinates at each corner of the feature (for example, a forest clearing), then draw a polygon in Google Earth to join the points and calculate area. Compare the polygon with other data layers, such as a national park boundary, to confirm or refute a hypothesis.

## Satellite Imagery

Satellite images often show features that standard reference maps do not, such as pipes running from a port to a factory, or the internal layout of a prison compound. Imagery may be more current than maps for tracking construction progress, deforestation, or conflict damage. Comparing images from different dates reveals change over time.

Most mapping platforms offer a satellite view option, including Google Maps, Google Earth, Bing, Baidu, HERE WeGo, OsmAnd, and Yandex. Images differ between platforms in resolution and date. Areas obscured on one platform may be visible on another.

**Historical satellite imagery in Google Earth** typically goes back 10 to 15 years for most places, with some areas going further. Updates occur every one to three years for most locations, and more frequently in areas that have experienced events such as earthquakes (where humanitarian organisations and governments may request new imagery for emergency response). To access historical imagery, click the clock icon in the toolbar. A time slider appears. Click the Zoom button to focus on a specific date range. Use the arrows at either end of the slider to advance through images sequentially.

**Adding imagery from other sources:** GeoTIFF files with embedded georeferencing can be imported into QGIS and placed automatically. Non-georeferenced images can be added to Google Earth via Add > Image Overlay (or the Image Overlay button in the toolbar). After selecting the file, use the corner and side handles to position, scale, and rotate it. Make the image semi-transparent and enable road layers to help align it with the underlying map. To skew the image, go to the Location tab and click "Convert to LatLongQuad," then input lat-long values for each corner or adjust manually until the image fits.

The process of positioning aerial or satellite images accurately in geographic space on a map is called georectification. Mapknitter (https://publiclab.org/wiki/mapknitter) is a free, open-source tool for georectification that exports results as GeoTIFFs.

Historical aerial images can be found through local government offices, archives, libraries, and the public image libraries of NASA and the European Space Agency (ESA).

## Interpreting Satellite Images

**Size and scale:** knowing the scale of the image is necessary to estimate object sizes. Interactive online maps let you zoom in and out and measure objects directly in Google Earth Pro.

**Pattern:** agricultural fields may be rigidly rectangular or, where rotating irrigation booms are used, circular. Natural-growth forest has an irregular pattern. Plantations are typically arranged in a grid.

**Shape:** bodies of water such as lakes and rivers have distinctive organic shapes and are usually easy to identify. Straight lines in a landscape almost always indicate human-made features such as roads, canals, or land boundaries.

**Texture:** how smooth or rough a surface appears. Concrete or tarmac appears smooth. Vegetation appears rough.

**Tone and colour:** visible-light satellite images are fairly intuitive. Vegetation is green (though colour changes seasonally). Water absorbs light and typically appears black or dark blue. Sediment makes water appear brown. Shallow water can be lighter. Sunlight reflections appear white or grey. Infrared images (used to monitor vegetation) show vegetation in shades of red.

**Shadow:** shadows indicate the height of objects and can help establish the time and date the image was taken. The sun's direction (azimuth) and height (altitude) change throughout the day and throughout the year. Shadows change accordingly in direction and length.

**Site and association:** what surrounds a feature helps identify it. A large supermarket on the edge of town will likely have a large car park and be close to a major road. A major goods port will be near the sea with storage land and road connections.

**Your own knowledge:** knowing that a large fire occurred in an area in recent months helps you recognise a large brown area surrounded by forest as a burn scar.

Conclusions drawn from satellite imagery should be corroborated through other means, such as a site visit or verification by local partners.

## Shadow Analysis

Shadows in satellite images can be used to estimate object heights or to verify the time and date an image was taken.

The tool SunCalc (https://suncalc.org) shows the sun's path, height, and direction minute by minute on any day of the year, for any location between 85 degrees N and 85 degrees S. It covers dates from 1900 to 2099. You can input an object's height and calculate the expected shadow length at a specific time and place, or reverse the process.

**Example from the chapter (Eiffel Tower, 9 June 2017 image in Google Earth):**

1. Navigate to the Eiffel Tower in Google Earth and use the historical imagery slider to select the 9 June 2017 image.
2. Find the tower's centre at ground level by drawing a line from the outer corner of the bottom-left leg to the outer corner of the top-right leg, then a second line from the bottom-right leg to the top-left leg. Their intersection is the centre.
3. Draw a line from the tip of the shadow to that intersection. The ruler info panel gives the length and the "heading" (azimuth) of the line.
4. Open SunCalc at https://suncalc.org. Navigate to the Eiffel Tower. Set the date to 9 June 2017. Move the sun/time slider until the azimuth in the SunCalc sidebar matches the azimuth from Google Earth.
5. Adjust the value in the "at an object level" box until the calculated shadow length matches the measured length. The result is the approximate height of the tower.

The chapter notes that this gives only an approximate height because image resolution limits measurement accuracy. Higher-resolution imagery produces more accurate results.

## Hypothetical Case: Tracking Illegal Logging by Supply Chain

The chapter walks through a hypothetical scenario to illustrate how maps and satellite data work together in a supply chain investigation. The scenario: timber is being illegally logged inside a National Park in Malaysia and shipped to China for furniture manufacturing.

1. Download shapefiles of the National Park boundary from the local government GIS website and import them into Google Earth.
2. Use historical satellite imagery to identify new clearings that have appeared inside the park boundary over the past year.
3. Draw polygons around the clearings in Google Earth to calculate how much area has been deforested.
4. Import a CSV database of sawmill locations (with lat-long) into Google Earth to create a pin layer. The sawmills closest to the cleared area are prioritised for further investigation.
5. Use a map search to find sea ports near the deforested area. Check those ports in satellite imagery and Google Street View to identify timber storage areas. Timber is stored in the open and is often visible in satellite images.
6. Use Marine Traffic ship-tracking data to find which vessels have docked at the relevant quay, then track those same vessels to the port where they unload in China.
7. Use company databases to identify furniture companies near the destination port. Infrastructure visible in satellite images, such as a railway line from the port to specific towns, helps narrow down the most likely companies.

## Weather Data

Weather data can support or challenge claims about events and locations.

**Corroboration technique:** if a photograph is said to have been taken at a specific place on a specific day, but historical weather data shows conditions that contradict what the photograph shows (for example, the ground is dry in the photo but it rained heavily that day), there is reason to doubt the claim. Weather data alone is unlikely to prove or disprove information, but it can provide strong grounds for further investigation.

**Current and forecast:**
- Windy.com: current conditions and a 10-day forecast for temperature, air pressure, precipitation, wind, cloud cover, CO2, ozone, SO2, wave height and swell, sea currents, and water temperature.

**Historical weather:**
- Weather Underground: one reading per day from weather stations worldwide. Includes maximum and minimum temperature, precipitation, and sunrise and sunset data.
- Dark Sky Time Machine: an API that provides downloadable historical data covering temperature, precipitation, humidity, dew point, wind, atmospheric pressure, UV index, and visibility.
- ECMWF (European Centre for Medium-Range Weather Forecasts): a global historical archive. Some datasets go back to 1900. From 2008, monthly downloadable reports with measurements every three hours, covering temperature, precipitation, cloud cover, and air pressure. The data uses specialist formats. The public datasets service stopped updating from June 2023.

**Sunrise and sunset:** the Time and Date website gives sunrise, sunset, and twilight data for major cities worldwide, adjusted for seasons. It also shows dates when clocks change.

**Time zones:** the Time and Date world time zone map shows current times, including summer and winter adjustments.

## Land Use, Ownership, and Planning Data

**Large-scale land cover:**
- European Environmental Agency Global Land Cover dataset: raster images covering European territories and more. Used as a baseline for climate conventions including the Convention to Combat Desertification, the Ramsar Convention, and the Kyoto Protocol. Also used for the Millennium Ecosystems Assessment. Downloadable at https://www.eea.europa.eu/data-and-maps/data/global-land-cover-250m.
- OSM Landuse Landcover: a web application using OSM data to map land use globally. Coverage varies by region. Verify with other sources.
- GIS Geography: lists further free land use resources.

**Cadaster (land ownership):** a cadaster is an official register of land ownership showing who owns what land and where. Some countries have digitised and published their cadastral maps online as PDFs or shapefiles. Not all land in every country is under cadaster. Switzerland and the Czech Republic have interactive online cadastral maps. In most cases, access to cadastral data is not free.

**Mining and resource maps:** some resource-rich countries publish mining licenses and exploitation contracts to increase transparency. Mozambique's Mining Cadastre Portal is one example: a government database that is regularly updated with licenses and contracts for resource exploitation and exploratory works.

**Zoning maps:** describe what land uses (housing, commercial buildings, light industry, and so on) are permitted in each area. Some countries have digitised these maps. Chicago's interactive zoning map shows codes and permit applications for each area.

**Building permits:** applications submitted to local governments typically contain drawings showing the proposed development on its site, detailed plans, sections and elevations of buildings, proposed materials, the building's intended use, and whether the permit was approved and under what conditions. Searchable by keyword, address, or postcode.

## Key Terms

**Administrative boundary:** the boundary of a country, region, or municipality.

**AIS (Automatic Identification System):** a transponder-based system used to track vessel positions. Ships below a certain size, and most military and coastguard vessels, do not carry AIS transponders.

**Choropleth:** a map where regions are coloured to show differences in a statistic such as voting percentages or life expectancy.

**CSV (comma-separated values):** a simple database format organised in rows and columns.

**GIS (geographic information system):** software used to collect, store, process, analyse, and represent geographic information.

**Geocoding:** converting location data such as a street address into precise lat-long coordinates.

**Geodata:** information about geographic locations, usually stored in digital format.

**Geolocation:** finding the real-world location of an object, such as the place where a photograph was taken.

**Georectification:** the process of positioning images accurately in geographic space on a map.

**GeoTIFF:** a raster image format with embedded georeferencing information.

**GPS (Global Positioning System):** a US system of navigational satellites that allows users to determine their position on earth.

**Heat map:** a map showing variation in intensity, such as how air pollution differs across a city.

**KML/KMZ:** file formats used in Google Earth to store points, lines, and polygons.

**Land cover:** classification of what covers the earth's surface (grass, trees, water, buildings, crops).

**Land use:** classification of how people use the land (agriculture, transport, recreation, residential, conservation).

**Location metadata:** lat-long coordinates embedded in a photograph or video file showing where it was captured.

**Raster data:** geographic data stored as a grid of pixels. Common formats are JPEG and TIFF.

**Shapefile:** a common GIS vector file format storing geometric data together with a database of attributes. It consists of multiple files (.shp, .shx, .dbf) that must be kept together.

**Symbol map:** a map where symbols of different sizes and colours are placed at locations to represent data.

**Thematic map:** a map showing information related to a specific subject.

**Vector data:** geographic data stored as points, lines, and polygons.

**Zoning map:** a map describing what land uses are permitted in each area.

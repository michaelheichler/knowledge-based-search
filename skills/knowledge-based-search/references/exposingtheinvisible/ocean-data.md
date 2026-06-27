---
title: Ocean Datasets for Investigations
source: Exposing the Invisible, The Kit (kit.exposingtheinvisible.org)
---

Written by Mae Lubetkin and Kevin Rosa, this chapter teaches journalists, activists, and investigators how to find, access, and use publicly available ocean datasets to support evidence-based stories about climate change, environmental justice, and marine ecosystems.

## 1. Context: Ocean Science, Data, and Storytelling

The ocean covers 71% of Earth's surface, acts as the planet's largest carbon sink, and is a primary indicator of climate change. Despite this, it is largely invisible to most people's lived experience. Ocean datasets can make that invisible world visible, supporting investigations into climate, pollution, overfishing, extractivism, and coastal justice. Investigative organizations that use ocean data include Forensic Architecture, LIMINAL, Forensis, Earshot, and Border Forensics.

### History and Colonial Legacy

"Contemporary" ocean science has deep roots in European colonialism. Indigenous and coastal communities across Oceania and the Atlantic and Indian Oceans developed sophisticated ocean knowledge systems long before European contact, using embodied understanding of stars, swells, winds, and currents to navigate vast distances with high precision. Stick charts made by Marshall Islander navigators are one documented example.

European explorers dismissed or erased these systems. The Challenger Expedition (1872-1876), the first systematic European scientific exploration of the global oceans, was also embedded in colonial mapping and resource extraction. Today, contemporary Western ocean science still operates largely within those traditions, often in the context of economic or territorial expansion and military-supported science projects.

Ocean science is now beginning a process of decolonization. This involves acknowledging the harms of colonization, shifting who holds agency over ocean waters, and co-designing research with ocean knowledge holders from diverse communities. The Spilhaus Projection, developed by oceanographer Athelstan Spilhaus in 1942, is cited as an example of decolonial cartography: it centers the ocean rather than land masses.

### Ocean Defenders

Ocean defenders are individuals, groups, and organizations that protect marine environments and advocate for communities most affected by climate change and pollution. Many are fisherpeople or coastal communities. Like land defenders, they face significant political resistance and funding barriers. A 2022 court case in South Africa in which the Makhanda High Court set aside Shell's permit to conduct a seismic survey on the Wild Coast is cited as an example of successful advocacy.

### Data Access and Gaps

Most ocean datasets highlighted in this chapter are publicly funded by governments via taxpayer contributions and freely accessible. However, many require specialized software or programming knowledge to use. Deep ocean research is resource-intensive and dominated by wealthy nations: it requires a ship, deep-water vehicles, computing systems, and technical personnel. Satellite data covers the entire Earth surface and is accessible regardless of nationality. Near-shore monitoring is more affordable, especially where lower-cost technologies merge with local knowledge systems.

## 2. Data Types

Ocean data falls into four broad categories: in situ sensors, deep ocean observation, mapping, and satellite remote sensing.

### 2.1 In Situ Sensors

In situ sensing means instruments are physically inside the water, directly measuring ocean properties. Sensors measure temperature, salinity, pressure, currents, and biochemical concentrations. Temperature measurement from ships dates to Captain James Cook's 1772 Antarctic voyage. The Nansen bottle (1896) and Niskin bottle (1966) captured water samples at specific depths. The first bathythermograph (1938) recorded temperature profiles on a wire lowered into the water. The US Navy used it in World War II to improve sonar accuracy, because temperature layers alter how sound travels through water. Today, thousands of sensors transmit readings in real time by satellite.

Trade-offs: in situ sensors measure only their exact location, face power constraints that limit sampling frequency, and are expensive to maintain in remote or harsh conditions, leading to undersampling in less-accessible areas. Extreme pressure in the deep ocean also limits the operating depth of some sensors.

**Moorings and Fixed Platforms (2.1.1)**

Anchored platforms that collect time-series data at a fixed location. They range from deep-ocean arrays (such as the TAO array across the Pacific) to continental shelf buoys (NOAA's National Data Buoy Network) and coastal tide gauges. Uses include long-term climate monitoring of ocean heat content and circulation, inputs for ocean and weather forecast models, early warning systems for tsunamis and hurricane storm surge, tracking tidal heights and local sea level rise, and water quality monitoring for pollutants, algal blooms, and hypoxia. Most transmit near-real time, but some platforms require physical retrieval before data is downloaded. Spatial coverage is limited and concentrated around a small set of nations.

Key data sources: US NOAA National Data Buoy Center (NDBC), EU Copernicus Marine Service In Situ dashboard, Global Tropical Moored Buoy Array.

**Drifters and Floats (2.1.2)**

Unanchored instruments that drift with currents. Surface drifters track ocean surface conditions and near-surface currents from GPS trajectories. Floats profile the water column by adjusting their buoyancy to move up and down. The Argo program is the largest and most significant float program, with over 4,000 floats globally. Each Argo float profiles to 2,000 m every 10 days and transmits data by satellite. Some Argo floats carry biochemical sensors. Drifters map near-surface currents and track pollutant or debris transport. Because they move, they cannot provide a clean time series for a single location the way moorings can. Argo floats do not generally operate near coasts on continental shelves.

Key data sources: Global Drifter Program, Argo Program, Copernicus Marine Service drifters, SOCCOM Biogeochemical Floats.

**Autonomous Vehicles: ASVs and Gliders (2.1.4)**

Autonomous Surface Vehicles (ASVs) and gliders are robotic platforms for long-duration, energy-efficient monitoring over large areas. They bridge the gap between expensive ship-based measurements and uncontrolled drifters. ASVs use solar, wind, or wave energy to supplement batteries. Gliders are underwater vehicles that create propulsion by adjusting buoyancy and gliding horizontally while sinking or rising, similar to an airplane, which extends battery range beyond what propellers allow. They can operate in dangerous conditions such as hurricanes. Their data availability is lower than moorings or floats because they are typically used in targeted studies.

Key data sources: NOAA Glider Data Assembly Center, OceanGliders.

### 2.2 Deep Ocean Observation, Exploration, and Research

Deep ocean science observes long-term changes at specific seafloor sites, explores unknown marine habitats, and conducts applied research. Tools include platforms and landers, cabled observatories, and deep submergence systems.

The field has developed in stages. The HMS Challenger expedition (1872-1876) was the first milestone. Cold War military priorities then led to Trieste's 1960 dive into the Mariana Trench. HOVs expanded access from 1964 onward (Alvin in the US, Nautile in France, Shinkai in Japan, Mir in Russia). ROVs and AUVs were developed in parallel by industry and scientific institutions from the 1980s through the 2000s. Cabled observatories followed from the 2000s onward, including Ocean Networks Canada and DONET in Japan. Today, wealthy nations increasingly use AI, autonomous systems, and 4K and 3-D imaging, while many nations still face funding and access barriers.

Trade-offs: these systems provide direct access to environments that surface vessels or satellites cannot reach, and high spatial and contextual resolution. Operations are resource-intensive (requiring ships, launch and recovery teams, and specialized personnel). Data collection is episodic and site-specific. Colonial legacies persist in who sets research agendas, who makes funding decisions, and who benefits from collected data.

**Deep Submergence Systems: HOVs, ROVs, and AUVs (2.2.1)**

Human-occupied vehicles (HOVs) carry 1-3 scientists plus a pilot. Remotely operated vehicles (ROVs) are tethered and piloted from a surface vessel. Autonomous underwater vehicles (AUVs) are untethered and pre-programmed. Most are depth-rated to 4,000-6,000 m, and some reach full ocean depth (11 km). Uses include high-resolution visual surveys, targeted sampling at hydrothermal vents, methane seeps, and cold-water coral habitats, biogeographic habitat mapping, wreck exploration, infrastructure inspection, and visual storytelling. ROV data streams to the surface vessel in real time. HOV and AUV data is retrieved when the vehicle is recovered. AUV missions require detailed planning because mission failure can mean losing the vehicle.

Key data sources: SeaDataNet (EU research vessel data, including cruise summary reports), EuroFleets (EU research cruise data), Rolling Deck to Repository (US research vessel data including expedition summary, shiptrack navigation, and sampling event log), JAMSTEC Databases (Japan, including HOV Shinkai 6500 and ROV Kaiko mission data, cruise reports, and dive logs).

**Landers and Elevators (2.2.2)**

Relatively simple systems that descend to the seafloor and remain stationary. Sometimes called "elevators" because they descend then ascend. They carry sensors, cameras, and samplers but no people. They can stay on the seafloor for hours to months depending on power supply. Uses include collecting environmental data (conductivity, temperature, pH, oxygen), baited camera studies of biodiversity, and transporting instruments that deep submergence vehicles cannot carry due to space limits. Data is usually retrieved when the lander is recovered to the deck, though some transmit acoustically from the seafloor. Currents can push the lander off its intended landing site. Lander data is stored in the same repositories as deep submergence systems.

**Cabled Observatories (2.2.3)**

Mostly permanent wired infrastructure on the seafloor transmitting real-time power and data via fiber optic cables to shore stations. They support temperature, pressure, seismometer, hydrophone, camera, and sampler instruments. They connect diverse environments from hydrothermal vent regions to abyssal plains and continental shelves. Designed for continuous high-frequency monitoring over years or decades. They can integrate with ROV or AUV docking stations and are typically serviced by ROVs. Uses include monitoring earthquakes and hydrothermal vents, providing tsunami and gas-release early warnings, studying currents and biogeochemical fluxes and ecosystem change, and supporting public engagement through livestreams. costly with high maintenance needs.

Key data sources: Ocean Networks Canada Oceans 3.0 Data Portal, US Ocean Observatories Initiative (OOI) Data Portal (East and West coast and deep Pacific arrays), EU EMSO ERIC Data Portal (real-time and archived data, European seafloor margins).

### 2.3 Mapping

Marine hydrographic mapping creates high-resolution representations of the seafloor, water column, and associated features using vessel-based sonar, autonomous vehicles, or acoustic and optical tools. Unlike satellite remote sensing (which observes the ocean surface from space), hydrographic mapping is conducted from platforms within or on the ocean. Early bathymetric charts used lead lines during colonial-era navigation in the 1870s-1900s. Echo sounding was developed in the 1920s-1940s for military and commercial use. Multibeam sonar in the 1950s-1970s enabled wider swath coverage of seafloor bathymetry. Today autonomous vehicles and 3-D photogrammetry advance mapping capabilities, but coverage remains uneven globally, with under-resourced nations lacking detailed seafloor maps of their own waters.

Trade-offs: high-resolution, fine-scale maps of seafloor and water column features, enabling geologic, biologic, and habitat-based spatial analysis, but requiring significant ship time, technical expertise, and post-processing. Most of the seafloor remains unmapped. High cost and national interests impact where mapping occurs and who benefits.

**Bathymetric Mapping (2.3.1)**

Measurement and charting of seafloor depth and shape using sonar systems (single-beam or multibeam echosounders) mounted on ships, AUVs, or towed platforms. Short-range systems mounted on ROVs achieve centimeter-level resolution over small areas. Hull-mounted multibeam systems cover wider swaths at lower resolution. Uses include mapping underwater topography and geological features, planning submersible dives and identifying hazards, supporting infrastructure projects such as cables and offshore wind farms, and creating base maps for habitat or biogeographic studies. Key instrument manufacturers include Kongsberg, Teledyne, R2Sonic, and Edgetech. Data is processed using specialized hydrographic software such as QPS Qimera, CARIS, or MB-System. Calibration for sound speed profiles and correction for vessel motion are required. Interpretation of raw bathymetry data requires trained analysts and geospatial tools.

Key data sources: EMODnet Bathymetry (EU, multibeam datasets with built-in visualizer), NOAA NCEI (US and global bathymetric surveys with visualizer), GEBCO Gridded Bathymetry Data (global compiled map interface), Global Multi-Resolution Topography (GMRT, with graphical map tool), GeoMapApp (free application for browsing and analyzing global geoscience datasets). The Seabed 2030 initiative is a global effort to map the entire seafloor by 2030.

**Water Column Mapping (2.3.2)**

Acoustic systems, usually multibeam echosounders or specialized water column sonars, detect and visualize features suspended between the surface and the seafloor. Used to observe biological migration layers (schools of fish or midwater migrations in the twilight zone), detect hydrothermal plumes, and track methane seep gas bubbles. Sound waves reflect strongly off gas bubbles, making seeps visible in the data. Most multibeam systems include a water column data mode, so this data is often collected alongside bathymetry. Data must be interpreted alongside oceanographic profiles (CTD casts) and often requires manual cleaning to reduce noise. Processing is not yet standardized.

Key data sources: EMODnet Physics (some water column data layers), NOAA NCEI water column sonar data.

**Seafloor Backscatter (2.3.3)**

Analysis of the intensity of sound reflected or "scattered back" from the seafloor when sonar systems are in use. Provides information about seafloor texture, hardness, and composition (sand, rock, mud). Often collected simultaneously with bathymetric mapping using the same sonar systems. Used for seafloor habitat classification, detecting anthropogenic objects such as cables and wrecks, and complementing bathymetry for geologic or habitat models. Calibration and post-processing are required to produce usable mosaics. Interpretation of sediment type from backscatter should be verified by ground-truth sampling such as grabs or cores.

Key data source: NOAA NCEI.

**Sub-bottom Profiling (2.3.4)**

Low-frequency acoustic pulses penetrate below the seabed to image sediment layers and buried geologic features, revealing vertical structures beneath the seafloor. Deployed from research vessels or towed systems. Used to study sedimentation and geological processes, locate subseafloor gas pockets or archaeological sites, and support infrastructure planning or hazard assessment for submarine landslides. Chirp profilers offer high resolution with shallow penetration. Boomer and sparker systems reach greater depth with less detail. Resolution and penetration depth are inversely related. Interpretation can be difficult without ground-truth sampling such as sediment cores.

Key data sources: NOAA NCEI, EMODnet Geology (sub-bottom and other seafloor geological data).

**Photogrammetry and 3-D Reconstruction (2.3.5)**

Overlapping images or video frames from subsea cameras (mounted on ROVs or AUVs) are stitched together to create detailed mosaics or 3-D models of seafloor features. Uses optical data, providing true-color high-resolution imagery unlike acoustic mapping techniques. Used to map hydrothermal vent fields, coral reefs, and archaeological sites, and to detect change in dynamic environments such as volcanic or vent habitats. Software such as Agisoft Metashape or custom photogrammetry pipelines are used for processing. Requires good lighting and water clarity. Processing is computationally intensive, and vehicle navigation data helps plot 3-D reconstructions onto broader bathymetric maps. Typically limited to small survey areas due to time and battery constraints.

Key data source: MBARI Sketchfab (Monterey Bay Aquarium Research Institute 3-D models). Additional models can be found in academic papers and individual institution or government agency repositories.

### 2.4 Satellite Remote Sensing

Satellites provide the most spatially complete picture of the ocean. NASA launched Seasat, the first satellite designed for ocean research, in 1978. The 1990s brought significant expansion with TOPEX/Poseidon (ocean altimetry), AVHRR (high-resolution sea surface temperature), and SeaWiFS (ocean biology). Modern constellations are operated by NASA, NOAA, ESA, EUMETSAT, CNES, ISRO, and others. Unlike satellite imagery on land, most ocean satellite data does not come from the visible spectrum. Trade-offs: excellent spatial coverage that is impossible to achieve with ships or buoys, but only the ocean surface is observed (no subsurface data), limited horizontal resolution, and limited temporal resolution (orbital repeat time). Costs are high. Platforms are operated by government agencies.

**Sea Surface Temperature (SST) (2.4.1)**

The oldest and most extensive application of satellite oceanography. Sensors measure the temperature of the top approximately 1 mm of the ocean. Two separate sensor types are used. Infrared (IR) sensors have higher spatial resolution (1-4 km) and finer temporal coverage but cannot see through clouds, which block over 70% of the ocean at any given time. Microwave sensors can see through most non-precipitating clouds but have lower spatial resolution (about 25 km) and do not work near coastlines. Blended products such as GHRSST L4 combine multiple sensors for better coverage. SST data comes in processing levels: L2 is data along the original orbital track, L3 is gridded and sometimes time-averaged, and L4 is cloud-free with gaps filled by interpolation methods depending on the source. L4 is easiest to use but may not be fully accurate. Uses include tracking climate change, El Nino events, and marine heat waves, hurricane forecasting, and mapping ocean eddies, currents, and upwelling, which are critical to fisheries.

Key data sources: EU Copernicus Marine Service, US NASA Physical Oceanography DAAC (PO.DAAC), NOAA CoastWatch (graphical interface).

**Sea Surface Height (SSH) / Radar Altimetry (2.4.2)**

Radar altimeters send radio pulses and measure return time to calculate ocean surface height. The slope of the sea surface is used to calculate "geostrophic currents," revealing the strength of large-scale circulation such as the Gulf Stream. Key for understanding ocean circulation and long-term sea level rise. Instruments include Jason-3 and Sentinel-6. Spatial resolution is significantly worse than SST (25+ km). The SWOT satellite offers a new type of altimeter with much higher resolution but has limited coverage as only one is currently in orbit. SSH is useful for large-scale ocean currents but not coastal tidal currents. Radar generally sees through clouds so data gaps are not a significant issue.

Key data sources: EU Copernicus Marine Service, Aviso, US NASA PO.DAAC, Copernicus MyOcean Pro (graphical interface), Aviso SeeWater (graphical interface).

**Ocean Color (2.4.3)**

Optical sensors measure the reflectance of sunlight from the ocean surface to infer biological and chemical properties such as algal concentration, suspended sediments, and water clarity. Sensors measure light at different wavelengths (MODIS, VIIRS, Sentinel-3 OLCI) and apply algorithms to calculate variables such as Chlorophyll-a concentration. Used to track phytoplankton blooms and changes in marine ecosystems, and to monitor water quality including coastal sediment and oil spills. Significantly affected by cloud cover, aerosols, and atmospheric correction errors.

Key data sources: EU Copernicus Marine Service, US NASA Ocean Color Web, NASA Worldview (graphical interface).

### 2.5 Additional Databases and Scientific Support

Additional databases include PANGAEA (data publisher for earth and environmental science across disciplines), the International Seabed Authority DeepData (database for all data related to international deep-seabed activities, particularly exploration contractor data, with a dashboard and map), the Marine Geoscience Data System (geology and geophysical research data), the USGS Earthquake Hazards Program (interactive map covering ocean and land earthquakes), WoRMS (World Register of Marine Species, comprehensive taxonomic list), OBIS (Ocean Biodiversity Information System, global open-access marine biodiversity data), and Windy (animated weather maps, radar, waves, and spot forecasts).

When data proves difficult to work with, the guide recommends contacting an ocean scientist at a nearby university or research institute. The chapter lists specialist types by area: physical oceanographers (currents, tides, waves, sea level rise, ocean-atmosphere interaction), chemical oceanographers (ocean acidification, pollution, nutrient cycling, chemical runoff), biological oceanographers and marine biologists (biodiversity, fisheries, invasive species, ecosystem health), geological oceanographers and marine geologists (earthquakes, tsunamis, deep-sea mining, underwater features), climate scientists with ocean expertise (ocean heat content, carbon storage, long-term trends), marine ecologists (overfishing, coral bleaching, marine protected areas), fisheries scientists (fish populations, stock assessments, fishing policy), ocean data scientists (satellite data, ocean models, large datasets), marine policy experts and ocean economists (marine regulations, governance, the "blue economy"), and marine technologists and ocean engineers (data collection tools and sensor limitations).

## 3. Case Study: Gulf of Maine Ocean Warming

The Gulf of Maine is warming faster than 99% of the global ocean, making it a key site to investigate local impacts of climate change on marine environments and coastal livelihoods.

### Historical and Ecological Context

Indigenous Wabanaki peoples, including the Abenaki, Mi'kmaq, Maliseet, Passamaquoddy, and Penobscot nations, relied on Gulf of Maine waters for food, cultural practices, and trade for generations. European colonization brought intensive cod fishing that fueled transatlantic trade and early settlements. Europeans treated the cod fisheries as effectively endless. Overfishing caused a massive collapse in cod stocks by the 1950s. Today the American lobster fishery is under stress from the combination of ocean warming and historic overfishing. Harmful algal blooms have increased in frequency, indicating broader ecosystem stress.

### Data Acquisition

The investigation uses two datasets in parallel to determine how much faster the Gulf of Maine is warming compared to the global average.

**Gulf of Maine buoy data (3.2.1).** NOAA's National Data Buoy Center (NDBC) Station 44007 holds annual temperature records back to 1982. The chapter describes a Python script using the pandas data analysis library that loops through years 1982-2024, constructs the URL for each year's text file from the NDBC URL structure, loads the text data via `pandas.read_csv()`, converts year/month/day/hour columns to a single pandas datetime column, combines all years into one dataframe, and saves to CSV.

**Global mean SST (3.2.2).** The Climate Reanalyzer website offers a download of globally averaged SST derived from the NOAA 1/4-degree Daily Optimum Interpolation Sea Surface Temperature (OISST), a long-term Climate Data Record combining satellite, ship, buoy, and Argo float observations into a regular global grid. The 1/4-degree resolution corresponds to approximately 25 km. The data downloads as a JSON file in which each year contains 366 temperature values in "day of year" format, with the last value null for non-leap years. The processing step must ignore that null before continuing.

### Climatological Anomaly Analysis

The standard method for analyzing climate change anomalies is to first remove the seasonal signal, then show how much warmer or colder each day was compared to the historical average for that day of year. The chapter uses 1991-2020 as the baseline period, matching the Climate Reanalyzer convention. The steps in Python are:

1. Filter the dataframe to the 1991-2020 period.
2. Assign a day-of-year value (1-366) to each data point.
3. Take the mean temperature for each day of year to get the climatological average.
4. Map that climatological value back to each point in the full time series.
5. Subtract climatological temperature from observed temperature to get the anomaly.

```python
df_clim = df[(df.index.year >= 1991) & (df.index.year <= 2020)].copy()
df_clim["day_of_year"] = df_clim.index.dayofyear
df_clim = df_clim.groupby("day_of_year")["temp"].mean()
df["day_of_year"] = df.index.dayofyear
df["climatology_value"] = df["day_of_year"].map(df_clim)
df["anomaly"] = df["temp"] - df["climatology_value"]
```

Plotting raw Gulf of Maine temperature data obscures the long-term trend because the seasonal signal spans more than 15 degrees C per year. Plotting anomalies removes that noise. A simple linear regression using numpy's `polyfit` quantifies the warming rate per decade. Monthly averages are plotted rather than daily values to reduce visual clutter, and both datasets use the same y-axis range for direct comparison.

Results validated against published literature:

- Gulf of Maine warming rate: 0.496 degrees C per decade. Within 5% of the 0.47 degrees C per decade reported by the Gulf of Maine Research Institute (the small difference is attributable to using a single buoy vs. OISST data averaged across the entire Gulf).
- Global SST warming rate: 0.188 degrees C per decade. Within 5% of the 0.18 degrees C per decade over the past 50 years published by Samset et al. (2023).

The Maine Climate Science Dashboard combines historical water temperature measurements with different climate scenario forecasts and shows how future human emissions could accelerate or slow the warming.

## 4. Conclusion and Investigative Template

The chapter presents the Gulf of Maine case as a template for investigating similar ocean and climate stories anywhere. The suggested process is:

1. Start with a local observation or community concern: what are people witnessing or experiencing in the local environment?
2. Explore the scientific context: consult scientists, read relevant research, and understand the underlying environmental drivers.
3. Seek out publicly available data as detailed in section 2.
4. Connect the data back to human issues: how do the environmental changes revealed by the data affect local cultures, livelihoods, health, and economies?

The chapter closes by noting that ocean datasets provide one lens on climate and environmental change, but these stories are also political and social. Just as ocean science has begun to decolonize, investigations should reflect diverse experiences and amplify the voices of those most affected. Ocean data can help illuminate intersecting issues such as deep seabed mining, marine health, and colonial continuums with evidence-based information and compelling visualizations.

## Appendix: Getting Started with Python

For readers new to coding, the chapter recommends three tools:

- Visual Studio Code as the code editor, citing its extensive ecosystem of third-party plug-ins and help resources.
- conda for package management, using separate conda environments for different projects to avoid interfering with the system Python installation. Example: `conda create -n ocean-study`, `conda activate ocean-study`, `conda install matplotlib`.
- Jupyter Notebooks (.ipynb files) for exploratory data work, allowing code to run in independent cells with output displayed inline and Markdown cells for notes.

## Authors

Mae Lubetkin is an ocean scientist, transmedia artist, and writer with a background in marine geology and subsea imaging, working within queer, intersectional, anti-extractivist, and decolonial frameworks.

Dr. Kevin Rosa is an oceanographer and founder of Current Lab, a startup specializing in computational ocean forecasting. He holds a PhD in Physical Oceanography from the University of Rhode Island.

Published June 2025.

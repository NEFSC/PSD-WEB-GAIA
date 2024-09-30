# GAIA's WHALE TCPED
---

### Description
The Geospatial Artificial Intelligence for Animals (GAIA) program brings together an extraordinary coalition of organizations to tackle the challenge of designing a large-scale operational platform to detect marine mammals from space-orbiting satellites. These organizations include government agencies (National Oceanic and Atmospheric Administration (NOAA), U.S. Naval Research Laboratory (NRL), the Bureau of Ocean Energy Management (BOEM), the U.S. Geological Survey (USGS), independent research organizations (British Antarctic Survey), academia (University of Edinburgh, University of Minnesota), and the private sector (Microsoft AI for Good Research Lab, Maxar Technologies).

GAIA's WHale Active Learning Environment (WHALE) Tasking, Collection, Processing, Exploitation, and Dissimination (TCPED) Application is a port of the original [WHALE](https://github.com/microsoft/whales), created by Microsoft AI for Good in collaboration with NOAA, to GeoDjango and expanded to handle satellite imagery collection and dissimination needs of the GAIA team.

### Contents
- dba
     - build - Jupyter Notebooks for building tables, logs, and triggers withint the SpatiaLite database.
     - migration - Jupyter Notebook for migrating tables
     - qaqc - Jupyter Notebooks for carrying out database quality assurance and control (i.e., validating that tables are built and populated properly)
- logs - A location to store log files
- gaia - GeoDjango project directory 
- whale - GeoDjango application directory
     - management - Files for managing the application (e.g., creating logs)
     - migrations - Migration files
     - templates - HTML templates, or webpages, for the application.

### Development Environment Set-up
Create a virtual enviornment within Anaconda using the requirements.txt file and issuing the following command: `conda create --name gaia --file requirements.txt`

Download and unzip [SpatiaLite](https://www.gaia-gis.it/gaia-sins/libspatialite-sources/libspatialite-5.1.0.zip) to this dorectory.

Download a copy of the SpatiaLite database (TO BE SET-UP)

Configure Django's Security (REACH OUT TO JOHN)

Configure Azure (REACH OUT TO JOHN)

### Disclosure Statement
This repository is a scientific product and is not official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.

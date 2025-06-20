# DBA
Database Administration for GAIA's WHALE Application.

Portions of this work were migrated from [SDB](https://github.com/JWall5/SDB) and adapted for work specifically here.

### Contents

**Analyze**
     - _Review_ - A Jupyter Notebook to review data within the SpatiaLite database showing some basic selection capabilities such as selecting Catalog and Entity ID based on Area of Interest. Also shows some capability of comparing two different tables, USGS EarthExplorer and Maxar Geospatial Platform.
     - _Schema (Mermaid)_ - A Mermaid markdown version of the schema.
     - _Schema_ - A notebook which shows the tables and allows those tables to be shown easily. Intended to support easy review and updating of code throughout this section.

**Build**
     **WARNING 1: MANY OF THESE NOTEBOOKS WILL DROP TABLES IN THEIR WORKFLOW!!!**
	 
	 **WARNING 2: MANY OF THESE NOTEBOOKS ARE DIVERGENT FROM WHAT IS ACTUALLY USED IN THE DATABASE AND WILL NEED TO BE UPDATED!!!**
	 
	 **WARNING 3: THE _BUILD.PY_ FUNCTIONS HAVE NOT NECESSAIRLY BEEN UPDATED FOR THE CURRENT SCHEMA**
	 
	 - _**lib**_
	      - **build.py** - Python functions to build tables and triggers within the database. 
	 - _AOIs_ - Should be seen as the primary, or initializing, notebook for building the spatially enabled SQLite database, better known as SpatiaLite, supporting the WHALE application or system. The notebook identifies downloaded KML files, denoting Areas of Interest, converts them to GeoJSON files, builds a GeoPandas GeoDataFrame, then commits them to the SpatiaLite database.
	 - _Build ELT_ - Builds the Extract, Transform, and Load (ETL) table, a denormaized table, from the USGS EarthExplorer, Global Enhanced GEOINT Delivery, and Maxar Geospatial Platform tables. Further adds columns for sea state quality, sea state quantity, and shareability of imagery. This notebook does not add the trigger function for updating this table. Instead, that can be found in the Triggers notebook.
	 - _EE_ - Using an Area of Interest, from the AOIs table mentioned above, queries USGS EarthExplorer's API for data over a given time period, builds the `EE` table from these results, and then populates the table with these values. Other notebooks are intended to be used for adding further records.
	 - _ETL_ - Similar to the _Build ELT_ notebook, but with some additional notes on how to consider down stream processing of imagery.
	 - _Exploit_ - Builds the _Exploit_ table using results from Microsoft AI for Good's Generate Interesting Points.
	 - _GEGD_ - Using an Area of Interest, from the AOIs table mentioned above, queries NGA's Global Enhanced GEOINT Delivery API for data over a given time period, builds the `GEGD` table from these results, and then populates the table with these values. Other notebooks are intended to be used for adding further records.
	 - _Initializer_ - Likely should be removed.
	 - _Log_ - Creates a table for logging every time the ETL trigger fires supporting troubleshooting.
	 - _MGP_ - Using an Area of Interest, from the AOIs table mentioned above, queries Maxar's Geospatial Platform API for data over a given time period, builds the `MGP` table from these results, and then populates the table with these values. Other notebooks are intended to be used for adding further records.
	 - _People_ - Builds the `people` table from a flat file database, i.e. CSV, using names as the primary key which are assumed to be unique strings for this project. Other notebooks are intended to be used for adding further records.
	 - _Target_ - Builds the `target` table from a flat file database using names (i.e., scientific and common names) as the primary key which are assumed to be unique strings for this project. Other notebooks are intended to be used for adding further records.
	 - _Tasking_ - Builds the `tasking` table from a flat file database of CIDR requests using the CIDR identifier as the primary key opposed to DAR and AOI.
	 - _Triggers_ - Updates the `ETL` table to be updated with a trigger by updates to the `EE`, `GEGD`, and `MGP` tables.

**Migration**
Migrate SpatiaLite records to a GeoDjango SpatiaLite database ensuring the objects are registed correctly.
     - _AOI2Django_
	 - _EE2Django_
	 - _GEGD2Django_
	 - _MGP2Django_
	 - _People2Django_
	 - _Target2Django_
	 - _Taskings2Django_

**QA/QC**
     - _00 QA/QC Objects_ - Helps in assuring that SQLite tables are spatially enabled, i.e. SpatiaLite, and are properly modeled by GeoDjango. This notebook also documents a lot of the validation needed to configure GeoDjango components.
	 - _ee review_ - Helps reviewing that objects are correctly stored and modeled within `animal_earthexplorer`
	 - _etl review_ - Similar to the above _ee review_, but for `ETL`.
	 - _etl scratch_ - Experiments using the `ETL` table.
	 - _interesting points_ - Experimental code to generate and load interesting points through the back door.
	 - _validation_ - Some additional functions to apply migrations, run checks, and query the database to ensure objects are stored correctly.

**Update**
Notebooks for running insert statements on the database.
     - _ee_
	 - _gegd_
	 - _mgp_
	 - _triggers_
	 
**Tasks**
	Tasks to be completed to ensure the database supports WHALE.
		- _requirements_ - The foundational tasks consisting of data modeling, user roles and permissions, data population, and data maintenance.
		- _permissions_ - A permission matrix to show which users can access the data and in what way.
		- _roles_ - Role-based access control (RBAC) for each user with specific permissions.
		- _models_ - Django models representing the data structure for each table.

### Troubleshooting
Some basic quality assurance and control via troubleshooting can be done by simply accessing the SpatiaLite database via a SQLite3 terminal. This can be done by navigating to the database's location, via an Anaconda prompt, and entering `sqlite3 db.sqlite3`. 
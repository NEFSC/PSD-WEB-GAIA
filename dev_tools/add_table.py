# ------------------------------------------------------------------------------
# ----- add_table.py -----------------------------------------------------------
# ------------------------------------------------------------------------------
#
#    authors:  John Wall (john.wall@noaa.gov)
#              
#    purpose:  Hot add a table to the SpatiaLite database
#
# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
# Import libraries
# ------------------------------------------------------------------------------
import os
import sqlite3


# ------------------------------------------------------------------------------
# Connect to database, add table
# ------------------------------------------------------------------------------
db = "../../../gis/PSD-WEB-GAIA/db.sqlite3"
db = os.path.abspath(db)

def create_poitnsofinterest(db):
    """ When provided with a path to a SpatiaLite database, create the
            ANIMAL POINTSOFINTEREST table.

        FIELDS: ID and Vendor ID
            
        DB - Path to database
    """

    try:
        conn = sqlite3.connect(db)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('mod_spatialite')")
        
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS animal_fishnet(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id VARCHAR(39)
            )
        ''')
        
        c.execute('''SELECT AddGeometryColumn('animal_fishnet', 'polygon', 3857, 'POLYGON')''')

        conn.commit()
        conn.close()

        print("Successfully created table ANIMAL FISHNET")
    
    except Exception as e:
        print(f"Failed to create table with exception: {e}")

create_poitnsofinterest(db)
#!/usr/bin/env python
# coding: utf-8

# # ETL Trigger Logging
# Creates a logging table for triggers updating the `etl` table.
# 
# ### Import libraries

# In[1]:


import sqlite3

# ### User defined variables

# In[2]:


db = "../../db.sqlite3"

# ### Drop triggers if they exist

# In[3]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")
c = conn.cursor()

c.execute('''DROP TABLE IF EXISTS trigger_log''')

conn.commit()
conn.close()

# ### Create Table

# In[4]:


conn = sqlite3.connect(db)
conn.enable_load_extension(True)
conn.execute("SELECT load_extension('mod_spatialite')")

c = conn.cursor()

c.execute('''
    CREATE TABLE trigger_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trigger_name TEXT,
        action TEXT,
        log_message TEXT,
        log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')

conn.commit()
conn.close()

# # End

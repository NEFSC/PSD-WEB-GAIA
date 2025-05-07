#!/usr/bin/env python
# coding: utf-8

# # Target Species
# Builds the `targets` table from a locally stored Excel spreadsheet.

import sqlite3
import pandas as pd

db = "../../db.sqlite3"
targets = "../../data/databases/targets.xlsx"

# Read Excel file into DataFrame and write to SQLite
conn = sqlite3.connect(db)
df = pd.read_excel(targets)
# Drop id column if it exists in DataFrame to let SQLite handle auto-increment
if 'id' in df.columns:
    df = df.drop('id', axis=1)
df.to_sql('targets', conn, if_exists='replace', index=True, index_label='id')
conn.close()
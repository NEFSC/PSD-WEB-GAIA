import sqlite3
import pandas as pd

db = "../../db.sqlite3"
people = "../../data/databases/people.xlsx"

# Read Excel file into DataFrame and write to SQLite
df = pd.read_excel(people)
conn = sqlite3.connect(db)
df.to_sql('people', conn, if_exists='replace', index=True, index_label='id')
conn.close()
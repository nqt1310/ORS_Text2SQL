import pandas as pd
import psycopg2
import os
from env import *

# Connect to PostgreSQL using environment variables
conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST")
)
cursor = conn.cursor()

# Read the Excel file
t1 = pd.read_excel('bank.xlsx',sheet_name='AGG_LOAN_TXN_ACM_MTH')
t2 = pd.read_excel('bank.xlsx',sheet_name='SMY_LOAN_BAL_MTH')
t3 = pd.read_excel('bank.xlsx',sheet_name='SMY_BRANCH_MTH')
for x in [t1,t2,t3]:
    x.columns = [i.upper().strip() for i in x.columns ]

meta_ = pd.concat([t1,t2,t3])

meta_.columns = [x.upper() for x in meta_.columns]

cursor.execute("""
    CREATE TABLE IF NOT EXISTS metadata_ (
        NO_ VARCHAR(400)	,
        COLUMN_NAME VARCHAR(400)	,
        DATA_TYPE	VARCHAR(400),
        DOMAIN	 VARCHAR(400), 
        PK	VARCHAR(400), 
        NULLABLE	VARCHAR(400), 
        COLUMN_DESCRIPTION	VARCHAR(400), 
        NOTE	VARCHAR(400), 
        ORS_MAP	VARCHAR(400), 
        GB_TABLE_DESCRIPTION	VARCHAR(400), 
        TABLE_DESCRIPTION	VARCHAR(400), 
        TABLE_NAME	VARCHAR(400),
        SCHEMA_NAME VARCHAR(400)
    );
""")



# Insert data into the table
for index, row in meta_.iterrows():
    cursor.execute("""
        INSERT INTO metadata_ ( NO_	, COLUMN_NAME ,DATA_TYPE	,DOMAIN	 ,  PK	, NULLABLE	, COLUMN_DESCRIPTION	, NOTE	, ORS_MAP	, GB_TABLE_DESCRIPTION	, TABLE_DESCRIPTION	, TABLE_NAME,SCHEMA_NAME )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,  %s, %s, %s)
    """, (
        row['NO.'],
        row['COLUMN NAME'],
        row['DATA TYPE'],
        row['DOMAIN'],
        row['PK'],
        row['NULL(Y/N)'],
        row['COLUMN DESCRIPTION'],
        row['NOTE'],
        row['ORS MAP'],
        row['GB_TABLE_DESCRIPTION'],
        row['TABLE_DESCRIPTION'],
        row['TABLE_NAME'],
        row['SCHEMA_NAME']
    ))




# Commit the transaction
conn.commit()

# Close the connection
cursor.close()
conn.close()
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openai
import psycopg2
import os
import re
import env  # Import env.py

app = FastAPI()

# Set up OpenAI API key
openai.api_key = env.API_KEY

# Connect to PostgreSQL using environment variables
conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST")
)
cursor = conn.cursor()

# Allow CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

def get_table_metadata(cursor):
    cursor.execute("""
    SELECT  NO_, 
            COLUMN_NAME,
            DATA_TYPE,
            DOMAIN,  
            PK, 
            NULLABLE, 
            COLUMN_DESCRIPTION,
            NOTE, 
            ORS_MAP, 
            GB_TABLE_DESCRIPTION,
            TABLE_DESCRIPTION,
            TABLE_NAME,
            SCHEMA_NAME
    FROM public.metadata_
    """)
    metadata = cursor.fetchall()
    return metadata

with open("diagram.mmd", "r") as file:
    mermaid_diagram = file.read()

def text_to_sql(query_text, metadata):
    try:
        metadata_str = "\n".join([f"Column: {COLUMN_NAME}, Data Type: {DATA_TYPE}, Domain: {DOMAIN}, PK:{PK}, NULLABLE: {NULLABLE}, COLUMN_DESCRIPTION: {COLUMN_DESCRIPTION}, NOTE: {NOTE}, ORS_MAP: {ORS_MAP}, English table description: {GB_TABLE_DESCRIPTION}, Vietnamese table description: {TABLE_DESCRIPTION}, Table_name = {TABLE_NAME}, SCHEMA_NAME ={SCHEMA_NAME} " for NO_, COLUMN_NAME, DATA_TYPE, DOMAIN, PK, NULLABLE, COLUMN_DESCRIPTION, NOTE, ORS_MAP, GB_TABLE_DESCRIPTION, TABLE_DESCRIPTION, TABLE_NAME, SCHEMA_NAME in metadata])
        prompt = f"Retrieve the data from DB and write me an SQL to access it based on metadata:\n{metadata_str}\n\nQuery: {query_text}\n\nMermaid Diagram:\n```mermaid\n{mermaid_diagram}\n```"
        
        # Send the query to OpenAI to generate SQL
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        response_text = response.choices[0].message['content'].strip()
        sql_query_match = re.search(r"```sql\n(.*?)\n```", response_text, re.DOTALL)
        if sql_query_match:
            sql_query = sql_query_match.group(1).strip()
        else:
            raise ValueError("No valid SQL query found in the response.")
        
        # Print the generated SQL query for debugging
        print(f"Generated SQL Query: {sql_query}")
        
        return sql_query.upper()
    
    except Exception as e:
        print(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def query(request: QueryRequest):
    query_text = request.query
    metadata = get_table_metadata(cursor)
    sql_query = text_to_sql(query_text, metadata)
    
    # Get column names
    column_names = [desc[0] for desc in cursor.description]
    
    return {"sql_query": sql_query, "column_names": column_names}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Text-to-SQL API"}

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=80)

import os
import psycopg2
from psycopg2 import pool, extras
from hashlib import sha256
import boto3
import numpy as np
import pandas as pd
from io import BytesIO
from contextlib import contextmanager

# Function to fetch database configuration from environment variables
def get_db_config():
    return {
        "user": os.getenv("DB_USER", "default_user"),
        "password": os.getenv("DB_PASSWORD", "default_pass"),
        "host": os.getenv("DB_HOST", "default_host"),
        "port": os.getenv("DB_PORT", "5432"),
        "database": os.getenv("DB_NAME", "default_db")
    }

# Fetch database configuration
db_config = get_db_config()

# Initialize the connection pool with the fetched configuration
connection_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    **db_config
)

@contextmanager
def get_database_connection():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def with_connection(func):
    def wrapper(*args, **kwargs):
        with get_database_connection() as conn:
            return func(*args, **kwargs, conn=conn)
    return wrapper

class DBops:
    def __init__(self):
        pass

    def calculate_file_hash(self, file_content):
        return sha256(file_content).hexdigest()

    def process_file_from_s3(self, bucket_name, file_key):
        s3_client = boto3.client('s3')
        obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        file_content = obj['Body'].read()
        file_hash = self.calculate_file_hash(file_content)
        if not self.check_data_hash(file_hash):
            print("Data hash mismatch found. Updating database...")
            
            csv_data = pd.read_csv(BytesIO(file_content))
            if 'questions' in csv_data.columns and 'answers' in csv_data.columns:
                questions = csv_data['questions'].tolist()
                answers = csv_data['answers'].tolist()
                self.insert_data(questions, answers)
                self.delete_all_data_hashes()
                self.update_data_hash(file_hash)
                print("Database updated with new data and data hash")
            else:
                raise ValueError("CSV does not contain the required 'questions' and 'answers' columns")
        else:
            print("Data is up to date")

    @with_connection
    def insert_data(self, questions, answers, conn):
        print("Inserting data using pgai for embedding generation")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM Unified_OphthalFAQs")
            args = [(q, a, q) for q, a in zip(questions, answers)]
            sql_query = (
                "INSERT INTO Unified_OphthalFAQs (question, answer, embedding) "
                "VALUES (%s, %s, ai_generate_embedding('openai_embedding', %s))"
            )
            extras.execute_batch(cur, sql_query, args)
            conn.commit()

    @with_connection
    def check_data_hash(self, file_hash, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM data_hash WHERE file_hash = %s)", (file_hash,))
            return cur.fetchone()[0]

    @with_connection
    def update_data_hash(self, file_hash, conn):
        with conn.cursor() as cur:
            cur.execute("INSERT INTO data_hash (file_hash) VALUES (%s) ON CONFLICT (file_hash) DO NOTHING", (file_hash,))
            conn.commit()

    @with_connection
    def delete_all_data_hashes(self, conn):
        with conn.cursor() as cur:
            cur.execute("DELETE FROM data_hash")  
            conn.commit()
            print("Deleted all data hashes from the database.")

    @with_connection
    def setup_database(self, conn):
        try:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    CREATE EXTENSION IF NOT EXISTS pgvector;
                    CREATE EXTENSION IF NOT EXISTS pgvectorscale;
                    CREATE EXTENSION IF NOT EXISTS pgai;

                    CREATE TABLE IF NOT EXISTS Unified_OphthalFAQs (
                        id SERIAL PRIMARY KEY,
                        question TEXT,
                        answer TEXT,
                        embedding VECTOR(1024)
                    );

                    DROP INDEX IF EXISTS Unified_OphthalFAQs_embedding_idx;

                    CREATE INDEX IF NOT EXISTS question_embedding_idx ON Unified_OphthalFAQs
                    USING diskann (embedding);

                    CREATE TABLE IF NOT EXISTS data_hash (
                        id SERIAL PRIMARY KEY,
                        file_hash TEXT UNIQUE
                    );
                    '''
                )
                conn.commit()
                print("Database tables and indexes created or verified with pgai integration.")
        except Exception as e:
            print(f"Error setting up database: {e}")

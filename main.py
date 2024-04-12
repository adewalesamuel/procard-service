from os import environ
from dotenv import load_dotenv
import psycopg2
import pymongo

load_dotenv()

client = pymongo.MongoClient(environ.get('MONGO_URI'))
mongo_db = client.procard
conn = psycopg2.connect(f"""dbname={environ.get('PSQL_DATABASE')} 
                        user={environ.get('PSQL_USERNAME')}
                        host={environ.get('PSQL_HOSTNAME')} 
                        password={environ.get('PSQL_PASSWORD')} 
                        port={environ.get('PSQL_PORT')}""")

def pg_get_all_registration():
    registrations = []

    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT datas FROM registrations")
            registrations = cur.fetchall()
    
    conn.close()
    return registrations

def pg_get_all_citizen():
    citizens = []

    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id from citizens")
            citizens = cur.fetchall()
    
    conn.close()
    return citizens

def mongo_get_dbs():
    return client.list_database_names()

def mongo_get_collections():
    return mongo_db.list_collection_names()

def mongo_get_all_enrolment():
    return mongo_db.enrolments.find()

def mongo_count_collection(collection_name: str):
    return mongo_db[collection_name].count_documents({})

print(pg_get_all_citizen())
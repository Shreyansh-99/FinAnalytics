import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="fintech_analytics",
        user="postgres",
        password="Shreyansh@2983",
        port="5432"
    )
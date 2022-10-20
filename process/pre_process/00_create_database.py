"""

Database creation
~~~~~~~~~~~~~~~~~

::

    Script:  00_create_database.py
    Purpose: Facilitate creation of a PostgreSQL database 
    Context: Used to create database and related settings for creation of liveability indicators

"""


import psycopg2
import time
# import getpass
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Import project configuration file
from _project_setup import *

def main():
    
    # simple timer for log file
    start = time.time()
    script = os.path.basename(sys.argv[0])
    task = 'Create region-specific liveability indicator database and user'
    
    # Create study region folder
    if not os.path.exists(f'{folderPath}/study_region'):
        os.makedirs(f'{folderPath}/study_region')
    if not os.path.exists(locale_dir):
        os.makedirs(locale_dir)    
    
    print("Connecting to default database to action queries.")
    conn = psycopg2.connect(dbname=admin_db, user=admin_db, password=db_pwd, host = db_host, port = db_port)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    curs = conn.cursor()
    
    # SQL queries
    create_database = f'''
    -- Create database
    CREATE DATABASE {db}
    WITH OWNER = {admin_db} 
    ENCODING = 'UTF8' 
    TABLESPACE = pg_default 
    CONNECTION LIMIT = -1
    TEMPLATE template0;
    '''
    
    print(f'Creating database if not exists {db}... '),
    curs.execute(f"SELECT COUNT(*) = 0 FROM pg_catalog.pg_database WHERE datname = '{db}'")
    not_exists_row = curs.fetchone()
    not_exists = not_exists_row[0]
    if not_exists:
      curs.execute(create_database) 
    print('Done.')
    
    comment_database = f'''
    COMMENT ON DATABASE {db} IS '{dbComment}';
    '''
    print(f'Adding comment "{dbComment}"... '),
    curs.execute(comment_database)
    print('Done.')
    
    create_user = f'''
    DO
    $do$
    BEGIN
       IF NOT EXISTS (
          SELECT   
          FROM   pg_catalog.pg_roles
          WHERE  rolname = '{db_user}') THEN
          
          CREATE ROLE {db_user} LOGIN PASSWORD '{db_pwd}';
       END IF;
    END
    $do$;
    ''' 
               
    print(f'Creating user {db_user}  if not exists... '),
    curs.execute(create_user)
    print('Done.')
              
    print(f"Connecting to {db}.")
    conn = psycopg2.connect(dbname=db, user=admin_db, password=db_pwd, host = db_host,  port = db_port)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    curs = conn.cursor()
     
    print('Creating required extensions ... '), 
    create_extensions = '''
    CREATE EXTENSION IF NOT EXISTS postgis; 
    CREATE EXTENSION IF NOT EXISTS postgis_sfcgal;
    CREATE EXTENSION IF NOT EXISTS pgrouting;
    SELECT postgis_full_version(); 
    CREATE EXTENSION IF NOT EXISTS hstore; 
    CREATE EXTENSION IF NOT EXISTS tablefunc;
    '''
    curs.execute(create_extensions)
    print('Done.')
    
    print('Creating threshold functions ... '),
    create_threshold_functions = '''
    CREATE OR REPLACE FUNCTION threshold_hard(in int, in int, out int) 
    RETURNS NULL ON NULL INPUT
    AS $$ SELECT ($1 < $2)::int $$
    LANGUAGE SQL;
    
    CREATE OR REPLACE FUNCTION threshold_soft(in int, in int, out double precision) 
    RETURNS NULL ON NULL INPUT
    AS $$ SELECT 1 - 1/(1+exp(-{slope}*($1-$2)/($2::float))) $$
    LANGUAGE SQL;    
    '''.format(slope = soft_threshold_slope)
    curs.execute(create_threshold_functions)
    print('Done.')
    
    curs.execute(grant_query)
    
    # output to completion log		
    from script_running_log import script_running_log			
    script_running_log(script, task, start, locale)
    conn.close()

if __name__ == '__main__':
    main()

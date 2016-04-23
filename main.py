import json
import sys


#check if database config set up
try:
    with open('config/database_setup.json') as jsonFile:
        database_info = json.load(jsonFile)
except ValueError:
    from config import setup_db_config
    setup_db_config.main()

    #test connection
    try:
        from library import database
        db_test = database.database("Thesis")
    except Exception as e:
        print e
        print "\n looks like something in the database is wrong.  :/"
        sys.exit()


#run experiments
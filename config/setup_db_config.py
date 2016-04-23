import json

def main():
    final_dict = {"database name": None, "host": None, "user": None, "password": None}

    for item in final_dict.keys():
        print "please insert the database's " + item + " and press enter when finished"
        item_answer = raw_input()
        final_dict[item] = item_answer

    print "okay cool saving info"

    with open('config/database_setup.json', 'w') as outFile:
        json.dump(final_dict, outFile)


from library import database, classification, my_time, normilisation, feature_helper
import json
import datetime
import sys
'''
purpose: test to see if random forest can make predictions for

features to put in to random forest:
day of week, month, week number, city demand level/duration of demand, listing_cluster number, enquiry #, cancellaton #, (#days_in advance)

price? Transformed???? (price / location average)
#instead of listing_cluster, can we also just put in the listing_cluster data straight into the random forest?

#going to have to first test just with Barcelona, 2015

ALSO keep in mind that all data from jsons are strings.
'''

json_files = {"day_features": {}, "day_features_normalised": {}, "occupancy_dict": {}}

#general data
testing_listings = []
all_data = {}

#listing id : {"deleted_at", "active", Updated_at, created at}
listing_important_dates = {}

#dates + some market intelligence
#feature_data_space = [{"listing_cluster": False}, {"days_active": False}, {"day_features": "day_number"}, {"day_features": "weekday_number"}, {"day_features": "week_number"}, {"day_features": "quarter_in_year"}]

#just dates feature_space
#feature_data_space = [{"day_features_normalised": "weekday_number"}, {"day_features_normalised": "week_number"}, {"day_features_normalised": "quarter_in_year"}]
feature_data_space = [{"day_features": "weekday_number"}, {"day_features": "week_number"}, {"day_features": "quarter_in_year"}, {"day_features": "day_number"}, {"day_features": "month_number"}, {"listing_cluster": True}, {"days_active": True}]
point_of_view = None
training_history = None
#training and testing data
current_location = None

listing_cluster_normalisation = {}

#need to get listing data where it's at least one year of data. Just using Barcelona 2014 as default. Predict into 2015
def get_testing_listings(list_of_location_ids = [1]):
    #return listings that have at least one year of occupancy data
    #And restricted to barcelona
    global testing_listings, json_files
    testing_listings = []
    thesis_data = database.database("Thesis")
    query_entries = ""
    for x in list_of_location_ids:
        query_entries += str(x) + ","

    #pop off final coma
    query_entries = query_entries[:(len(query_entries) - 1)]

    query = "SELECT `listing_locations_DBSCAN_final`.`listing_id`, `listing_clusters_plain`.`cluster_id`, `listing_locations_DBSCAN_final`.`label_id` FROM `listing_locations_DBSCAN_final` INNER JOIN `listing_clusters_plain` ON `listing_locations_DBSCAN_final`.`listing_id` = `listing_clusters_plain`.`listing_id` WHERE `label_id` IN(" + query_entries + ");"

    initial_data = thesis_data.get_data(query)

    for listing_data in initial_data:
        try:
            sample = json_files["occupancy_dict"][str(listing_data[0])]
            testing_listings.append(listing_data)
        except KeyError:
            pass

    thesis_data.destroy_connection()


def fill_global_data(inclusive = True):
    global listing_important_dates, json_files, feature_data_space, listing_cluster_normalisation
    #json_files loading: occupancy_dict, date_dict

    for filename in json_files.keys():
        json_files[filename] = _load_json(filename, inclusive)

    #earliest dates
    worldhomes_data = database.database("worldhomes")
    listing_important_dates_list = worldhomes_data.get_data("SELECT `id`, `created_at`, `updated_at`, `deleted_at`, `active` FROM `listings`")
    listing_important_dates = {entry[0]: {"created_at": entry[1], "updated_at": entry[2], "deleted_at": entry[3], "active": entry[4]} for entry in listing_important_dates_list}

    worldhomes_data.destroy_connection()

    #listing_cluster_normalisation, to make automatic so we don't have to deal with cluster changing issues.


'''
all dates need to be in dictionary format with:
end_date
start_date
DOes this per listing

default take all data
'''
def fill_training_and_testing_data(listing_id, testing_dates, training_dates = None):
    global all_data

    '''
    if listing_ids:
        training_with = listing_ids
    else:
        training_with = [entry[0] for entry in testing_listings]
    '''

    training_data = {"features": [], "classification" : []}
    testing_data = {"features": [], "classification" : []}


    #does listing have occupancy data to begin with
    try:
        occupancy_test = json_files["occupancy_dict"][str(listing_id)]

        if training_dates:
            #force it to take only listings that have at least started by the start date
            start = training_dates["start_date"]

            #dis-allowing majority of dataset
            '''
            if listing_important_dates[listing_id]["created_at"].date() > start:
                print "not enough training data for listing: ", listing_id

                #can put in training?
                return None
            '''
        else:
            start = datetime.date(2008, 01, 01)
        for day in my_time._daterange(start, testing_dates["end_date"]):
            try:
                if day < testing_dates["start_date"]:
                    training_data["features"].append(all_data[listing_id][day]["feature_data"])
                    training_data["classification"].append(all_data[listing_id][day]["classification"])
                else:
                    testing_data["features"].append(all_data[listing_id][day]["feature_data"])
                    testing_data["classification"].append(all_data[listing_id][day]["classification"])
                    testing_data["days"].append(day.strftime("%Y-%m-%d"))
                        #print "putting data in testing_data"
            except KeyError as e: #this day didn't have data, but listing might have data
            #shouldn't be an issue anymore because we deleted the day structure if it has no data in all_data
                pass

    except KeyError as e:
        print e
        print "in 122"
        return None

    return (training_data, testing_data)


'''
All data holds :
listings : year: day: feature_data: [feature_space], classification: 0/1
automatically filters for listings that have full data

normalisation says wehter or not to normalise all the features to betwee 0 and 1
'''
def fill_all_data(start_date, end_date, normalised = True):
    global all_data, testing_listings, json_files, point_of_view

    #clear
    all_data = {}

    for listing_data in testing_listings:
        #setup basic structure
        listing_id = listing_data[0]

        #if earliest_dates[listing_id] <= start_date:
        all_data[listing_id] = my_time.compact_default_date_structure(start_date, end_date)

        for day in all_data[listing_id].keys():

            #this is a valid, active day for the listing, can be 0 or 1
            if json_files["occupancy_dict"][str(listing_id)][day.strftime("%Y")][day.strftime("%Y-%m-%d")] is not None:
                #day is datetime object
                if point_of_view:
                    all_data[listing_id][day] = {"feature_data" : _get_feature_data_with_pointofview(listing_data, day, normalised), "classification" : json_files["occupancy_dict"][str(listing_id)][day.strftime("%Y")][day.strftime("%Y-%m-%d")]}
                else:
                    feature_data = _get_feature_data(listing_data, day, normalised)
                    if feature_data is not False:
                        all_data[listing_id][day] = {"feature_data" : _get_feature_data(listing_data, day, normalised), "classification" : json_files["occupancy_dict"][str(listing_id)][day.strftime("%Y")][day.strftime("%Y-%m-%d")]}
                    else:
                        print "deleting ", listing_id, "from all_data"
                        del all_data[listing_id]
                        break
            else:
                    #there is no occupancy data for this day
                del all_data[listing_id][day]
        #else:
        #    print "this listing_id doens't have enough data %s " % (listing_id)
        #    pass



#listing_cluster, day of month, day of week, week number,historical demand level_for_day (default to kmeans = 3),
##days active, months active, #of this type of demand level active
#day is a datetime
#listing_data: id, listing_cluster, location_cluster
def _get_feature_data(listing_data, day):
    global feature_data_space, listing_important_dates, json_files, current_location

    final = []

    for this_dict in feature_data_space:

        for dict_name, specification in this_dict.iteritems():

            #load json if it doesn't exist in json_files:
            if dict_name in ["price_dict", "k-means_season_clusters", 'cluster_averages', 'cluster_averages_year'] and dict_name not in json_files.keys():
                with open("data/" + dict_name + ".json") as jsonFile:
                    json_files[dict_name] = json.load(jsonFile)

            #check if there's a point of view requirement
            global point_of_view
            try:
                view_date = day + datetime.timedelta(point_of_view)
            except TypeError: #point of view is still none
                view_date = day

            #the real stuff of feature addition
            if dict_name in ["listing_cluster", "days_active", "day_features", "day_features_normalised"]:
                if dict_name == "listing_cluster":
                    if normalised:
                        #FIX THIS
                        normalised_listing_cluster = {1:float(1)/11, 2:float(2)/11, 3:float(3)/11, 4: float(4)/11, 5: float(5)/11, 7: float(6)/11, 13: float(7)/11, 14: float(8)/11, 15: float(9)/11, 26: float(10)/11, 27: float(11)/11}
                        final.append(normalised_listing_cluster[listing_data[1]])
                    else:
                        final.append(listing_data[1])
                elif dict_name == "days_active":
                    days_diff = int( (day - listing_important_dates[listing_data[0]]["created_at"].date()).days)
                    if normalised:
                        possible_normalised = my_time.get_listing_activity_span(listing_important_dates[listing_data[0]])

                        if days_diff:
                            days_diff = possible_normalised
                        else:
                            #last confirmed dates of known occupancies
                            days_diff = float(days_diff)/(int((datetime.date(2016, 1, 29) - day).days ) )
                    else:
                        final.append(days_diff)

                elif dict_name in ["day_features", "day_features_normalised"]:
                    final.append(json_files[dict_name][day.strftime("%Y-%m-%d")][specification])

            elif dict_name in ["k-means_season_clusters", "cluster_averages", 'cluster_averages_year']:

                #specification in this case is just going to be the amount of data around the week to include around the view_date, which is a year ago.

                #k-Means_cluster
                #year: {location_id: k_means_type: day: cluster_designation}
                #
                #cluster_averages_year
                #full_year structure is by year for the primary key, then location_cluster, then listing_cluster: day: average
                #
                #for now just take the 3 clusters
                #
                #HAVE TO USE CURRENT YEAR CLUSTERS
                #last_year = datetime.date((day.year - 1), day.month, day.day)
                if specification:
                    if specification == "one_week":

                        #reverse input for the week.  Shouldn't be a problem
                        for x in range(0,7):
                            this_day = view_date - datetime.timedelta(-1 * x)
                            if dict_name == "k-means_season_clusters":
                                #need to cast to int
                                final.append(int (json_files[dict_name][this_day.strftime("%Y")][str(current_location)]["3"][this_day.strftime("%Y-%m-%d")]) )
                            else:
                                #append all averages
                                for listing_cluster in json_files[dict_name][str(current_location)].keys():
                                    final.append(int(json_files[dict_name][this_day.strftime("%Y")][str(current_location)][listing_cluster][this_day]))
                else:
                    #HAVE TO USE THIS YEAR'S DATE
                    if dict_name == "k-means_season_clusters":
                        to_add = int(json_files[dict_name][view_date.strftime("%Y")][str(current_location)]["3"][view_date.strftime("%Y-%m-%d")])
                        final.append(to_add)
                    else:
                        for listing_cluster in json_files[dict_name][str(current_location)].keys():
                            final.append(json_files[dict_name][view_date.strtime("%Y")][str(current_location)][listing_cluster][view_date])


            elif not specification and dict_name not in ["listing_cluster", "days_active"]: #for dicts that just have dates
                try:
                    to_add = json_files[dict_name][str(listing_data[0])][view_date.strftime("%Y")][view_date.strftime("%Y-%m-%d")]
                except KeyError:
                    #delete this entry from consideration
                    #hopefully only returns false when the listing id is not in the dictionary we are looking at (looking at you Price_dict)
                    if dict_name == "price_dict":
                        return False
                    else:
                        #for other dictionaries, it just means that this listing has none of these types of data
                        to_add = 0

                #for enquiries: item = {"id": value}
                if isinstance(to_add, list):
                    for item in to_add:
                        if item is None:
                            final.append(0)
                        elif isinstance(item, dict):
                            final.append(item.values()[0]) #should only be one value
                        else:
                            final.append(item)
                else:
                    #make none's 0 for learning algorithms
                    if to_add is None:
                        final.append(0)
                    elif isinstance(to_add, dict):
                        final.append(to_add.values()[0])
                    else:
                        final.append(to_add)

    return final

        #else:
            #this is a day specific entry, need to check if there's a "time ahead"
            #time_ahead will tell us to add known data known the number of days in time_ahead ahead of the current day.

            #if "time_ahead" in feature_data_space.keys():
'''
The features that we can put in point of view are: #of enquiries known for that day, #of cancellations for that day, %booking for the day that we are looking at.
'''
def _get_feature_data_with_pointofview(listing_data, day):
    global feature_data_space, listing_important_dates, json_files

    pass

def _load_json(filename, inclusive):

    if inclusive and filename in ["k-means_season_clusters", "cluster_averages", "occupancy_dict", "cluster_averages_year"]:
        filepath = "data/inclusive_occupancy_jsons/" + filename + ".json"
    else:
        filepath = "data/" + filename + ".json"

    #there is a json file for this
    with open(filepath) as jsonFile:
        this_json = json.load(jsonFile)

    '''
    elif filename == "day_features": #need to pull this data from database
        thesis_data = database.database("Thesis")

        #week_number, day_number, month_number, weekday, year, null, null
        day_features_list = thesis_data.get_data("SELECT * FROM `date_to_day`")
        this_json = {datetime.date(entry[4], entry[2], entry[1]).strftime("%Y-%m-%d"): {"weekday_number": float(entry[3] + 1)/7, "day_number": float(entry[1])/7, "week_number": float(entry[0])/5, "month_number": float(entry[2])/12, "quarter_in_year": float((entry[2]-1)/3 + 1)/4, "year": float(entry[4] - 2008)/(2016 - 2008)} for entry in day_features_list}
    '''
    return this_json

'''
time ahead up to one year
time ahead should be passed as an INT for days
new_feature_specifications must be dictionary with:
key: json file name
specification: special specification if any
'''
def add_feature_to_feature_space(feature_dict, inclusive = True):
    #if there is a time_ahead, then
    global json_files, feature_data_space, point_of_view

    if isinstance(feature_dict, list):
        for ind_feature_dict in feature_dict:
            feature_data_space.append(ind_feature_dict)

            #load json
            dict_filename = ind_feature_dict.keys()[0]
            if dict_filename not in json_files.keys():
                json_files[dict_filename] = _load_json(dict_filename, inclusive)

    elif isinstance(feature_dict, list):
        feature_data_space.append(feature_dict)

        #load json
        dict_filename = ind_feature_dict.keys()[0]
        if dict_filename not in json_files.keys():
            json_files[dict_filename] = _load_json(dict_filename, inclusive)

    #load feature_dict if necessary


'''
Classification part of code
'''
def make_classification_model(model_name, training_dict):
    prediction_class = classification.classification(model_name)
    prediction_class.train_with(training_dict["features"], training_dict["classification"])
    return prediction_class

def test_classification(classification_model, testing_data_dict):
    testing_features = testing_data_dict["features"]
    answers = testing_data_dict["classification"]

    predictions = classification_model.predict(testing_features)
    if predictions is not False:
        return classification.results(predictions, answers).get_results()
    else:
        return False

'''
other things
'''

def save_to_file(folder, filename, to_save):
    with open(folder + filename + ".json", "w") as output:
        json.dump(to_save, output)

'''
expecting dicts to be like:
listing_id{ value1: , value2: ...}

or for average:
value: , value:
'''

def save_to_database(table_name, experiment_name, city_name, full_dict):
    thesis_data = database.database("Thesis")

    #delete similar entries
    query = "DELETE FROM `" + table_name + "` WHERE `city` = '" + city_name + "' AND `experiment` = '" + experiment_name + "';"
    #print query
    thesis_data.execute(query)

    print "saving to database " + table_name + " experiment results: " + experiment_name

    #put entries in, then the keys are lists and what I want to store are the true_true,
    if full_dict and isinstance(full_dict.keys()[0], long):
        insert_query = "INSERT INTO " + table_name + "  VALUES('%s','%s',%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for listing_id, full_records in full_dict.iteritems():
            #experiment ,  city , listing_id, method, true_true, true_false, false_true, false_false, occupancy_precision, occupancy_recall, empty_precision, empty_recall, occupancy_fOne, empty_fOne, correct_overall
            for method, method_results in full_records.iteritems():
                to_insert = [experiment_name, city_name, listing_id, method]
                for this_thing in ["true_true", "true_false", "false_true", "false_false", "occupancy_precision", "occupancy_recall", "empty_precision", "empty_recall", "occupancy_fOne", "empty_fOne", "correct_overall"]:
                    if method_results[this_thing]:
                        to_insert.append(method_results[this_thing])
                    else:
                        to_insert.append("null")
                #print (insert_query % to_insert)
                thesis_data.execute(insert_query % tuple(to_insert))
    elif full_dict:
        insert_query = "INSERT INTO " + table_name + " VALUES('%s','%s','%s',%s,%s,%s,%s,%s, %s)"
        #experiment ,  city ,  method, occupancy_precision, occupancy_recall, empty_precision, empty_recall, occupancy_fOne, empty_fOne,
        for method, method_results in full_dict.iteritems():
            to_insert = [experiment_name, city_name, method]
            for this_thing in ["occupancy_precision", "occupancy_recall", "empty_precision", "empty_recall", "occupancy_fOne", "empty_fOne"]:
                if method_results[this_thing]:
                    to_insert.append(method_results[this_thing])
                else:
                    to_insert.append("null")

            thesis_data.execute(insert_query % tuple(to_insert))

    thesis_data.destroy_connection()



def instructions():
    print "set up global data have fun!  Here's what you need to do to finish setup:"

    print "def get_testing_listings(list_of_location_ids = [1]), defaults to just barcelona"


    print "if you want to change the point of view, use change_point_of_view(days_in_advance), enter a positive number to indicate how many days in the future you are predicting."
    #point_of_view(7)

    print "you can play with the feature space too with:\n"
    print "add_feature_to_feature_space(new_feature_specifications, time_ahead = None) where time_ahead is an int, new_feature_specifications is either a dict {feature_space_dict: specific feature name or None to indicate day} "
    print "and the feature space dic codes are: "
    print '{"occupancy": occupancy, "enquiry" : enquiry, "cancellation": cancellation, "doublebooked": doublebooked, "confirmed_advanced": confirmed_advanced, "enquiry_advanced": enquiry_advanced, "cluster_designations": cluster_designations, "day_features" : day_features, "unavailable": unavailable, "unconfirmed": unconfirmed} \n'

    print "fill_all_data(start_date, end_date, point_of_view = False) [start and end date should should include both testing and training data times], datetime objects please!"

    print "fill_training_and_testing_data(training_dates, testing_dates, listing_ids = None), \nreturns a list with two dictionaries: \ntesting_data{ features: [testing_data_features], classifications: []; \ntraining_data{ features: [], classifications : []}}"
    print "where testing_dates and training dates are a dict with these values: {start_date: datetimeObject; end_date: datetimeObject}"
    print "returns a tuple with (training_data, testing_data)\n"

    print "for classification tests use the classification class:"
    print "classification.classification(model_name).train_with(training_data_list, answers).predict(testing_data), returns list of predictions"
    print "model_names: random_forest, centroid_prediction, linearSVC, nearest_neighbor, decision_tree, svc"

    print "for getting results, use classification's result's class"
    print "classification.results(prediction, classification).get_results(), returns dict"


'''
expecting structure to be:
method: listing_ids: full results
'''
def results_averaging(final_results_dict):
    '''
    "true_true", "true_false":, false_false": , "false_true":, "occupancy_precision", "empty_precision", "correct_overall",  "occupancy_recall", "empty_recall", "occupancy_fOne", "empty_fOne", }
    '''
    #method: occupancy_precision_count, occupancy_tot, ...
    results_store = {}
    for listing_ids, full_data in final_results_dict.iteritems():
        if full_data:
            for method, full_results in full_data.iteritems():
                if method not in results_store.keys():
                    results_store[method] = {}
                for result_type in ["occupancy_precision", "empty_precision", "occupancy_recall", "empty_recall", "occupancy_fOne", "empty_fOne"]:
                    if result_type not in results_store[method].keys():
                        results_store[method][result_type] = []

                    if full_results[result_type]:
                        results_store[method][result_type].append(full_results[result_type])
                    else: #if the result was None or 0
                    #often because there weren't many occupancies or falses in a test set
                        print "didn't have good data here"
                        print listing_ids, ", ", method
                        pass

    #get the average
    final = {}
    for method, result_type_data in results_store.iteritems():
        final[method] = {}
        for result_type, tot_in_list in result_type_data.iteritems():
            if len(tot_in_list) > 0:
                final[method][result_type] = float(sum(tot_in_list))/len(tot_in_list)
            else:
                final[method][result_type] = None

    return final

'''
Full experiments record
'''
def single_listing_oneyr_history_training():
    global current_location
    #barcelona, varenna, rotterdam, majorca
    fill_global_data()
    start_date = datetime.date(2014, 1, 1)
    end_date = datetime.date(2016, 1, 1)

    training_dates = {"start_date": datetime.date(2014, 1, 1), "end_date": datetime.date(2015, 1, 1)}
    testing_dates = {"start_date": datetime.date(2015, 1, 1), "end_date": datetime.date(2016, 1, 1)}

    get_testing_listings([1])



    fill_all_data(start_date, end_date, normalised = False) #good

    #classification_data = fill_training_and_testing_data(training_dates, testing_dates)
    all_results = {}
    for listing in testing_listings:
        all_results[listing[0]] = {}

        classification_data = fill_training_and_testing_data(listing[0], testing_dates, training_dates)

        if not classification_data:
            print "not enough data for listing ", listing[0]
            del all_results[listing[0]]
        else:
            training_dict = classification_data[0]
            testing_dict = classification_data[1] #good

            for model_name in ["random_forest", "centroid_prediction", "linearSVC", "nearest_neighbor", "decision_tree", "svc"]:
                try:
                    prediction_model = make_classification_model(model_name, training_dict)
                except ValueError: #there isn't enough training material sorry
                    break

                results = test_classification(prediction_model, testing_dict)

                if results is not False:
                    all_results[listing[0]][model_name] = results
                else:
                    del all_results[listing[0]]
                    break

    print "number of records we predicted for, " , len(all_results)
    analysis = results_averaging(all_results)
    location_dict = {1: "Barcelona", 0: "Rome", 6: "Varenna", 11: "Mallorca", 19: "Rotterdam"}

    save_to_database("machine_learning_average_results", "single_listing_date_only_added", "Barcelona", analysis)

    save_to_database("machine_learning_individual_results", "single_listing_date_only_added", "Barcelona", all_results)

    print "finished!"

def fullLocation_training(experiment_name, normalised = False):
    global current_location
    fill_global_data()
    start_date = datetime.date(2014, 1, 1)
    end_date = datetime.date(2016, 1, 1)

    training_dates = {"start_date": datetime.date(2014, 1, 1), "end_date": datetime.date(2015, 1, 1)}
    testing_dates = {"start_date": datetime.date(2015, 1, 1), "end_date": datetime.date(2016, 1, 1)}

    #three city, single listing training and prediction test
    #take out 6
    #for location_id in [1, 6, 11, 19]:
    for location_id in [0, 1, 19]:
        current_location = location_id

        print "on location: ", location_id
        get_testing_listings([location_id])
        print "number of listings for this location: ", len(testing_listings)


        fill_all_data(start_date, end_date, normalised) #good

        #classification_data = fill_training_and_testing_data(training_dates, testing_dates)
        all_results = {}
        all_training = {"features": [], "classification": []}
        all_testing = {}

        #set up trianing and testing
        for listing in testing_listings:

            classification_data = fill_training_and_testing_data(listing[0], testing_dates, training_dates)

            if classification_data:
                temp_training = classification_data[0]
                all_training["features"] += temp_training["features"]
                all_training["classification"] += temp_training["classification"]

                all_testing[listing[0]] = classification_data[1] #good

        #train please
        for model_name in ["random_forest", "centroid_prediction", "linearSVC", "nearest_neighbor", "decision_tree", "svc"]:
            try:
                prediction_model = make_classification_model(model_name, all_training)
            except ValueError: #there isn't enough training material sorry
                break

            for listing_id, testing_dict in all_testing.iteritems():

                results = test_classification(prediction_model, testing_dict)

                if results is not False:
                    if listing_id not in all_results.keys():
                        all_results[listing_id] = {}
                    all_results[listing_id][model_name] = results


        #save all_results
        location_dict = {1: "Barcelona", 0: "Rome", 6: "Varenna", 11: "Mallorca", 19: "Rotterdam"}
        save_to_database("machine_learning_individual_results", experiment_name, location_dict[location_id], all_results)
        print "saved individual results"

        analysis = results_averaging(all_results)
        save_to_database("machine_learning_average_results", experiment_name, location_dict[location_id], analysis)
        print "saved average results"

        print analysis
        print "analyzed ", len(all_results), " records"

        '''
        folder = "data/prediction_results/machine_learning/"

        filename = location_dict[location_id] + "_fullLocation_ListingInfo_training"

        save_to_file(folder, filename, analysis)
        '''

    print "finished!"

def listingCluster_training(experiment_name, normalised = False):
    #listing type training
    global current_location

    fill_global_data()
    start_date = datetime.date(2014, 1, 1)
    end_date = datetime.date(2016, 1, 1)

    training_dates = {"start_date": datetime.date(2014, 1, 1), "end_date": datetime.date(2015, 1, 1)}
    testing_dates = {"start_date": datetime.date(2015, 1, 1), "end_date": datetime.date(2016, 1, 1)}

    #three city, single listing training and prediction test
    for location_id in [0, 1, 19]:
        current_location = location_id
        print "on location: ", location_id
        get_testing_listings([location_id])
        print "number of listings for this location: ", len(testing_listings)

        #make listing_clusters: listing_cluster [ids]
        global testing_listings

        listing_clusters = {entry[1]: [] for entry in testing_listings}
        fill_all_data(start_date, end_date, normalised) #good

        #fill listing_clusters
        for entry in testing_listings:
            listing_clusters[entry[1]].append(entry[0])

        #classification_data = fill_training_and_testing_data(training_dates, testing_dates)
        all_results = {}

        #set up trianing and testing
        for listing_cluster, listing_id_list in listing_clusters.iteritems():
            all_training = {"features": [], "classification": []}
            all_testing = {}

            if len(listing_id_list) > 2:
                for listing in listing_id_list:

                    classification_data = fill_training_and_testing_data(listing, testing_dates, training_dates)

                    if classification_data:
                        temp_training = classification_data[0]
                        all_training["features"] += temp_training["features"]
                        all_training["classification"] += temp_training["classification"]

                        all_testing[listing] = classification_data[1] #good

            #train please
                for model_name in ["random_forest", "centroid_prediction", "linearSVC", "nearest_neighbor", "decision_tree", "svc"]:
                    try:
                        prediction_model = make_classification_model(model_name, all_training)
                    except ValueError: #there isn't enough training material sorry
                        break

                    for listing_id, testing_dict in all_testing.iteritems():

                        results = test_classification(prediction_model, testing_dict)

                        if results:
                            if listing_id not in all_results.keys():
                                all_results[listing_id] = {}
                            all_results[listing_id][model_name] = results

        print "analyzed ", len(all_results), " records"
        analysis = results_averaging(all_results)

        location_dict = {1: "Barcelona", 0: "Rome", 6: "Varenna", 11: "Mallorca", 19: "Rotterdam"}

        save_to_database("machine_learning_individual_results", experiment_name, location_dict[location_id], all_results)
        save_to_database("machine_learning_average_results", experiment_name, location_dict[location_id], analysis)


    print "finished!"    #sys.exit()

def date_only_experiments():
    global feature_data_space, point_of_view


    ##SIMPLE SOPHISTICATION
    #date only testing
    feature_data_space = [{"day_features": "weekday_number"}, {"day_features": "week_number"}, {"day_features": "quarter_in_year"}, {"day_features": "day_number"}, {"day_features": "month_number"}]
    single_listing_oneyr_history_training()
    listingCluster_training("listing_cluster_date_only")
    fullLocation_training("full_location_date_only_added")

    #date + listing_cluster
    feature_data_space = [{"day_features": "weekday_number"}, {"day_features": "week_number"}, {"day_features": "quarter_in_year"}, {"day_features": "day_number"}, {"day_features": "month_number"}, {"listing_cluster": True}]

    fullLocation_training("full_location_listing_cluster_added")

    #date + listing_cluste + days active
    feature_data_space = [{"day_features": "weekday_number"}, {"day_features": "week_number"}, {"day_features": "quarter_in_year"}, {"day_features": "day_number"}, {"day_features": "month_number"}, {"listing_cluster": True}, {"days_active": True}]

    #not normalised leads to bad results, many nulls
    fullLocation_training("full_location_date_listingC_daysActive", False)
    listingCluster_training("listing_cluster_date_listingC_daysActive", False)

    #fullLocation_training("full_location_date_listingC_daysActiveNormalised", True)
    #listingCluster_training("listing_cluster_date_listingC_daysActiveNormalised", True)

def price_experiments():
    #date + listing_cluste + days active, sold_for
    feature_data_space = [{"price_dict": None}]
    #
    fullLocation_training("full_location_date_price_alone", False)

    #listingCluster_training("listing_cluster_price_alone", False) Not enough data

    feature_data_space = [{"day_features": "weekday_number"}, {"day_features": "week_number"}, {"day_features": "quarter_in_year"}, {"day_features": "day_number"}, {"day_features": "month_number"}, {"listing_cluster": True}, {"days_active": True}, {"price_dict": None}]
    #
    fullLocation_training("full_location_date_price_fullListingF", False)
    listingCluster_training("listing_cluster_price_fullListingF", False)

#where the magic happens
if __name__ == '__main__':
    global feature_data_space

    #with market intelligence

    #same year k-means
    feature_data_space = [{"k-means_season_clusters": None}]

    fullLocation_training("full_location_lastYearSeason", False)


    #

    #MID SOPHISTICATION
    #with "additional features", since it seams that
    #feature_data_space = [{"day_features": "weekday_number"}, {"day_features": "week_number"}, {"day_features": "quarter_in_year"}, {"day_features": "day_number"}, {"day_features": "month_number"}, {"listing_cluster": True}]
    #piont of view
    '''
    feature_data_space = [{'CANCELLED':None}, {'CANCELLED':'occupancy_advanced'}, {'ENQUIRY': None}, {'ENQUIRY': 'occupancy_advanced'}, {'confirmed_advanced': None}, {'occupancy_advanced': 'percent_of_occupation'}]
    point_of_view = 7

    fullLocation_training("full_location_point_view_alone", False)
    listingCluster_training("listing_cluster_price_alone", False)
    '''




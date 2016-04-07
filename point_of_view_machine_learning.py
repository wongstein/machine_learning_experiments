from library import database, my_time, normilisation, feature_helper, common_database_functions, classification
import json
import datetime
import sys
import PCA_features

'''
purpose: test to see if random forest can make predictions for

features to put in to random forest:
day of week, month, week number, city demand level/duration of demand, listing_cluster number, enquiry #, cancellaton #, (#days_in advance)

price? Transformed???? (price / location average)
#instead of listing_cluster, can we also just put in the listing_cluster data straight into the random forest?

#going to have to first test just with Barcelona, 2015

ALSO keep in mind that all data from jsons are strings.
'''

#general data
all_data = {}

training_history = None
#training and testing data

listing_cluster_normalisation = {}

my_features = feature_helper.Features()

feature_header = None

#a positive int, that reflext the number of days we go back in time
point_of_view = 0

feature_data_space = []
#need to get listing data where it's at least one year of data. Just using Barcelona 2014 as default. Predict into 2015
def get_testing_listings(list_of_location_ids = [1]):
    #return listings that have at least one year of occupancy data
    #And restricted to barcelona
    global my_features
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
            sample = my_features.json_files["occupancy_dict"][str(listing_data[0])]
            testing_listings.append(listing_data)
        except KeyError:
            pass

    thesis_data.destroy_connection()

    return testing_listings


'''
All data holds :
listings : year: day: feature_data: [feature_space], classification: 0/1
automatically filters for listings that have full data

normalisation says wehter or not to normalise all the features to betwee 0 and 1
'''
def fill_experiment_data(testing_listings, start_date, end_date):
    global all_data, point_of_view, my_features
    #clear
    all_data = {}
    for listing_data in testing_listings:
        #setup basic structure
        listing_id = listing_data[0]

        '''
        if you want to reduce just to the listings that have previous data that trained with
        however, it's useful to be able to predict new listings with no data
        '''
        if my_features.listing_important_dates[listing_id]['created_at'].date() < start_date or str(listing_id) not in my_features.json_files['occupancy_dict'].keys():
            continue
        #TEST
        print "this listing id should have full data, ", listing_id
        all_data[listing_id] = {}

        for day in my_time.compact_default_date_structure(start_date, end_date):

            if day.year == 2013: #never hits this
                sys.exit()
            #this is a valid, active day for the listing, can be 0 or 1
            if my_features.json_files["occupancy_dict"][str(listing_id)][day.strftime("%Y")][day.strftime("%Y-%m-%d")] is None:
                #day is datetime object
                classification_to_add = 0
            else:
                classification_to_add = my_features.json_files['occupancy_dict'][str(listing_id)][str(day.year)][str(day)]

            features_to_add = _get_feature_data(listing_data, day)


            if features_to_add and (day >= my_features.listing_important_dates[listing_id]['created_at'].date()):
                all_data[listing_id][day] = {'features' : features_to_add, 'classification': classification_to_add}


#listing_cluster, day of month, day of week, week number,historical demand level_for_day (default to kmeans = 3),
##days active, months active, #of this type of demand level active
#day is a datetime
#listing_data: id, listing_cluster, location_cluster
def _get_feature_data(listing_data, day):
    global my_features, feature_data_space, point_of_view

    final = []
    listing_id = listing_data[0]
    listing_cluster = listing_data[1]

    for this_dict in feature_data_space:

        for dict_name, specification in this_dict.iteritems():
            #add dict if needed
            my_features.add_new_feature_json(dict_name)

            #check if there's a point of view requirement
            global point_of_view
            try:
                view_date = day - datetime.timedelta(point_of_view)
            except TypeError: #point of view is still none
                view_date = day

            #the real stuff of feature addition, switch statement
            if dict_name == 'listing_cluster':
                final.append(listing_cluster)

            #feature helper features
            elif dict_name in ["days_active"]:
                to_add = my_features.days_active_feature(listing_id, view_date)
                if not to_add:
                    return None
                final.append(to_add)
            #day features
            elif dict_name in ["weekday_number", "week_number", "quarter_in_year", "day_number", "month_number"]:
                final.append(my_features.date_features(dict_name, day))

            #elif dict_name in ["k-means_season_clusters", "cluster_averages", 'cluster_averages_year', 'occupancy_dict', 'CANCELLED', 'ENQUIRY']:
            else:

                #specification in this case is just going to be the amount of data around the week to include around the view_date,
                #which is a year ago.
                #Need to make extra consideration
                to_add = my_features.history_features(listing_id, dict_name, day, specification, point_of_view)

                if to_add is not None:
                    if isinstance(to_add, list):
                        final += to_add
                    else:
                        final.append(to_add)
                else: #to add is None
                    return None

    return final

#expecting transformation_model to be a dict where the keys are "min_max", or "z-standard"
def transform_data(data_list, transformation_model):
    global feature_header

    #selected transformations, min_max for categorical data

    #categorical data min_max
    transformed_data = transformation_model['min_max'].transform_data(data_list, feature_header)

    #discrete data
    transformed_data = transformation_model['z-standard'].transform_data(data_list, feature_header)

    return transformed_data

def fill_training_and_testing_data(testing_dates, training_dates = None):
    global all_data, my_features

    '''
    if listing_ids:
        training_with = listing_ids
    else:
        training_with = [entry[0] for entry in testing_listings]
    '''

    training_data = {"features": [], "classification" : []}
    testing_data = {}
    {"features": [], "classification" : []}

    for listing_id in all_data.keys():
        if not all_data[listing_id]: #if there is no data in the listing_id
            continue

        testing_data[listing_id] = {"features": [], "classification" : []}
        for day in all_data[listing_id].keys():
            if day < testing_dates['start_date'] and day >= training_dates['start_date']:
                training_data['features'].append(all_data[listing_id][day]['features'])
                training_data['classification'].append(all_data[listing_id][day]['classification'])
            elif day <= testing_dates['end_date']:
                testing_data[listing_id]['features'].append(all_data[listing_id][day]['features'])
                testing_data[listing_id]['classification'].append(all_data[listing_id][day]['classification'])

    return (training_data, testing_data)

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

#normalisation for point of view, because the data used is different
def make_normalisation_model(all_features, normalisation_type = None):
    transformation_model = {}

    transformation_model['min_max'] = normilisation.normalisation(all_features, feature_header, 'min_max')
    transformation_model['z-standard'] = normilisation.normalisation(all_features, feature_header, "z-standard")

    return transformation_model

'''
experiment_name = string that will be the name of the experiment saved to database

normalisation_type = text that can be either 'z-standard' or 'min_max'.  IF None, then the frankenstein normilisation scheme is used

with_PCA = an int that holds the final number of components in PCA

'''
def fullLocation(experiment_name, normalisation_type = None, with_PCA = None):
    global feature_header

    #add a buffer to prevent hitting key error with year 2013 for average_cluster_year
    start_date = datetime.date(2014, 1, 20)
    end_date = datetime.date(2016, 1, 30)

    training_dates = {"start_date": datetime.date(2014, 1, 20), "end_date": datetime.date(2015, 1, 29)}
    testing_dates = {"start_date": datetime.date(2015, 1, 30), "end_date": datetime.date(2016, 1, 30)}

    #three city, single listing training and prediction test
    #take out 6
    #for location_id in [1, 6, 11, 19]:
    for location_id in [0, 1, 19]:
    #for location_id in [1]:
        print "On location ", location_id

        testing_listings = get_testing_listings([location_id])
        print "number of listings for this location: ", len(testing_listings)


        fill_experiment_data(testing_listings, start_date, end_date)
        #dict: listing_id: day:

        #make transformation_model
        all_features = [all_data[entry][day]['features'] for entry in all_data.keys() for day in all_data[entry].keys()]
        transformation_model = make_normalisation_model(all_features)

        #if normalisation type, we hack the existing function to return transformation with the original 2 keys, but they hold the same model type trained to different types of data.

        transformed_data = transform_data(all_features, transformation_model)
        #set up trianing and testing
        classification_data = fill_training_and_testing_data(testing_dates, training_dates)

        if not classification_data[0]['features']: #if there's no feature data...
            continue

        training_data = classification_data[0]
        testing_data = classification_data[1]


        #transform data
        #training_data['features'] = transformation_model.transform_data(training_data['features'], feature_header, columns_to_normalise)
        #transform_data(data_list, transformation_model)
        training_data['features'] = transform_data(training_data['features'], transformation_model)

        ''''PCA_analysis for fun
        '''
        if with_PCA:
            training_data['features'] = PCA_features.do_PCA_analysis(experiment_name, training_data['features'], feature_header, location_id, number_components = with_PCA)

        '''
        Training Section
        '''

        all_results = {}
        for model_name in ["random_forest", "centroid_prediction", "linearSVC", "nearest_neighbor", "decision_tree", "svc"]:
            try:
                prediction_model = make_classification_model(model_name, training_data)
            except Exception as e: #there isn't enough training material sorry
                print e
                break

            for listing_id, testing_dict in testing_data.iteritems():
                testing_dict['features'] = transform_data(testing_dict['features'], transformation_model)

                if with_PCA:
                    testing_dict['features'] = PCA_features.do_PCA_analysis(experiment_name, testing_dict['features'], feature_header, location_id, number_components = with_PCA)
                results = test_classification(prediction_model, testing_dict)

                if results is not False:
                    if listing_id not in all_results.keys():
                        all_results[listing_id] = {}
                    all_results[listing_id][model_name] = results


        #save all_results
        location_dict = {1: "Barcelona", 0: "Rome", 6: "Varenna", 11: "Mallorca", 19: "Rotterdam"}
        classification.save_to_database("machine_learning_individual_results", experiment_name, location_dict[location_id], all_results)
        print "saved individual results"

        analysis = results_averaging(all_results)
        classification.save_to_database("machine_learning_average_results", experiment_name, location_dict[location_id], analysis)
        print "saved average results"

        print analysis
        print "analyzed ", len(all_results), " records"
    print "finished!"

def point_of_view_experiments():
    global point_of_view
    #defaulting to full location now just to see
    for this_point in [1, 3, 7, 30, 60, 90]: #one week, one month, 2 months, 3 months
        point_of_view = this_point
        experiment = "full_location_point_of_view_" + str(this_point) + "_min_max"

        fullLocation(experiment, "min_max", with_PCA = None)

#where the magic happens
if __name__ == '__main__':
    global feature_data_space, feature_header, my_features, point_of_view

    #update my features
    my_features = feature_helper.Features(feature_data_space)

    '''
    def fullLocation(experiment_name, normalisation_type = None, with_PCA = None)    '''
    #fullLocation("full_location_normalised_min_max", "min_max")
    #fullLocation("full_location_normalised_z_standard_no_occupation_normalisation", "z-standard")

    #only PCA
    #fullLocation("min_max", "min_max")

    #frankenstein standardisation, no PCA
    #fullLocation("full_location_frankenstein_normilisation")

    #with point of view
     #categorical features

    feature_data_space = [{"weekday_number": None}, {"week_number": None}, {"quarter_in_year": None}, {"day_number": None}, {"month_number": None}, {"listing_cluster": None}]

    #features that are continuous ints
    feature_data_space += [{"days_active": None}, {"price_dict": None}, {'CANCELLED': point_of_view}, {'ENQUIRY': point_of_view}, {'k-means_season_clusters': None}]
    #history data
    feature_data_space += [{"k-means_season_clusters": 7}]

    #best match features
    feature_data_space += [{'occupancy_dict': 'best_match_7'}, {'cluster_averages_year': 'best_match_7'}, {'ENQUIRY': 'best_match_day'}, {'CANCELLED': 'best_match_day'}, {'occupancy_dict': 'best_match_day'}]

    feature_header = ["weekday_number", "week_number", 'quarter_in_year', "day_number", "month_number",'listing_cluster',  "days_active", "price_dict", "cancellation count", "enquiry count",'k_means_season_day']

    feature_header += ['k means season history day -1', 'k means season history day  -2', 'k means season history day -3', 'k means history day -4', 'k means history day -5', 'k means history day -6', 'k means history day -7']

    #for best match
    feature_header += ['occupancy_match_-1', 'occupancy_match_-2', 'occupancy_match_-3', 'occupancy_match_-4', 'occupancy_match_-5', 'occupancy_match_-6', 'occupancy_match_-7', 'cluster_average_match_-1', 'cluster_average_match_-2', 'cluster_average_match_-3', 'cluster_average_match_-4', 'cluster_average_match_-5', 'cluster_average_match_-6', 'cluster_average_match_-7', 'ENQUIRY_match_day', 'CANCELLED_match_day', 'occupancy_match_day']


    point_of_view_experiments()








from library import database, my_time, normilisation, classification
#from library import my_time, normilisation
import json
import datetime
import sys
#import PCA_features
import time
import pandas as pd
from multiprocessing import Process, Queue

'''
purpose: test to see if random forest can make predictions for

features to put in to random forest:
day of week, month, week number, city demand level/duration of demand, listing_cluster number, enquiry #, cancellaton #, (#days_in advance)

price? Transformed???? (price / location average)
#instead of listing_cluster, can we also just put in the listing_cluster data straight into the random forest?

#going to have to first test just with Barcelona, 2015

ALSO keep in mind that all data from jsons are strings.
'''
point_of_view = None

#expecting transformation_model to be a dict where the keys are "min_max", or "z-standard"
def transform_data(data_list, transformation_model):
    global feature_header

    #selected transformations, min_max for categorical data

    #categorical data min_max
    transformed_data = transformation_model['min_max'].transform_data(data_list)

    #discrete data
    transformed_data = transformation_model['z-standard'].transform_data(data_list)

    return transformed_data

def shape_listing_data(listing_id, listing_all_data, features_to_use, testing_dates, training_dates, q):

    all_days = listing_all_data['day'].values.tolist()

    testing_data = {listing_id: {"features": [], "classification" : []}}
    training_data = {"features": [], "classification" : []}

    for string_day in all_days:
        day = datetime.datetime.strptime(string_day, "%Y-%m-%d").date()
        day_features = listing_all_data.loc[(listing_all_data['day'] == string_day)][features_to_use].values.tolist()[0]
        classification = listing_all_data.loc[(listing_all_data['day'] == string_day)]["classification"].values.tolist()[0]

        if day < testing_dates['start_date'] and day >= training_dates['start_date']:
            training_data['features'].append(day_features)
            training_data['classification'].append(classification)
        elif day <= testing_dates['end_date']:
            testing_data[listing_id]['features'].append(day_features)
            testing_data[listing_id]['classification'].append(classification)

    q.put((training_data, testing_data))


def fill_training_and_testing_data(features_to_use, testing_dates, training_dates):
    global all_data
    testing_listings = list(set(all_data['listing_id'].tolist()))

    training_data = {"features": [], "classification" : []}
    testing_data = {}

    thread_number = 5
    listing_chunks = []

    #listing_id will be a string
    import time

    start_time = time.time()

    for x in xrange(0, len(testing_listings), thread_number):
        small_chunk = []
        for y in xrange(0, thread_number, 1):
            try:
                small_chunk.append(testing_listings[x + y])
            except IndexError: #then it's finished
                listing_chunks.append(small_chunk)
                continue
        listing_chunks.append(small_chunk)

    for id_chunk in listing_chunks:
        q = Queue()
        process_list = []

        for listing_id in id_chunk:
            p = Process(target = shape_listing_data, args = (listing_id, all_data.loc[(all_data['listing_id']==listing_id)], features_to_use, testing_dates, training_dates, q))
            process_list.append(p)
            p.start()

        process_list[0].join #ensure we wait at least for the first thread to finish before getting results

        for process_tuple in process_list:
            #training dict then testing_dict
            return_tuple = q.get()
            training_data['features'] += return_tuple[0]['features']
            training_data['classification'] += return_tuple[0]['classification']

            testing_data = _merge_dicts(testing_data, return_tuple[1])

            process_tuple.join


    print "time took: ", (time.time() - start_time)

    return (training_data, testing_data)

def _merge_dicts(dict_1, dict_2):
    z = dict_1.copy()
    z.update(dict_2)
    return z

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

    transformation_model['min_max'] = normilisation.normalisation(all_features, "min_max")
    transformation_model['z-standard'] = normilisation.normalisation(all_features, "z-standard")

    return transformation_model

'''
experiment_name = string that will be the name of the experiment saved to database

normalisation_type = text that can be either 'z-standard' or 'min_max'.  IF None, then the frankenstein normilisation scheme is used
features_to_use is a list

'''
def fullLocation(experiment_name, features_to_use = None, normalisation_type = None):
    global feature_header, point_of_view, all_data

    #add a buffer to prevent hitting key error with year 2013 for average_cluster_year
    start_date = datetime.date(2014, 1, 20)
    end_date = datetime.date(2016, 1, 29)

    for location_id in [0]:
        print "On location ", location_id
        start_time = time.time()

        #get data
        file_path = "data/feature_data/" + str(location_id) + "_" + str(point_of_view) + "_all_features"
        all_data = pd.read_csv(file_path)

        #default to using the full feature_header
        if not features_to_use:
            features_to_use = feature_header

        training_dates = {"start_date": datetime.date(2014, 1, 1), "end_date": datetime.date(2015, 5, 29)}
        testing_dates = {"start_date": datetime.date(2015, 5, 29), "end_date": datetime.date(2016, 1, 29)}

        #set up trianing and testing
        classification_data = fill_training_and_testing_data(features_to_use, testing_dates, training_dates)

        if not classification_data[0]['features']: #if there's no feature data...
            continue

        training_data = classification_data[0]
        testing_data = classification_data[1]

        #transform data
        #
        #try making normalisation just on the training data (most realistic)
        #all_features = all_data[features_to_use]
        print "normalising data now"
        transformation_model = make_normalisation_model(training_data['features'])

        transformed_data = transform_data(training_data['features'], transformation_model)

        training_data['features'] = transform_data(training_data['features'], transformation_model)

        ''''PCA_analysis for fun

        if with_PCA:
            training_data['features'] = PCA_features.do_PCA_analysis(experiment_name, training_data['features'], feature_header, location_id, number_components = with_PCA)

        tranform training data here
        '''
        for listing_id, testing_dict in testing_data.iteritems():
            testing_dict['features'] = transform_data(testing_dict['features'], transformation_model)
            '''
            if with_PCA:
                testing_dict['features'] = PCA_features.do_PCA_analysis(experiment_name, testing_dict['features'], feature_header, location_id, number_components = with_PCA)

        Training Section
        '''

        all_results = {}
        print "starting classification experiments"
        for model_name in ["random_forest", "centroid_prediction", "linearSVC", "nearest_neighbor", "decision_tree", "svc"]:
        #for model_name in ['random_forest']:
            try:
                prediction_model = make_classification_model(model_name, training_data)
            except Exception as e: #there isn't enough training material sorry
                print e
                break

            for listing_id, testing_dict in testing_data.iteritems():
                results = test_classification(prediction_model, testing_dict)

                if results is not False:
                    if listing_id not in all_results.keys():
                        all_results[listing_id] = {}
                    all_results[listing_id][model_name] = results


        #save all_results
        location_dict = {1: "Barcelona", 0: "Rome", 6: "Varenna", 11: "Mallorca", 19: "Rotterdam"}
        classification.save_to_database("machine_learning_individual_results", experiment_name, location_dict[location_id], all_results)

        analysis = results_averaging(all_results)
        classification.save_to_database("machine_learning_average_results", experiment_name, location_dict[location_id], analysis)
        print "saved average results"

        print analysis
        print "\nanalyzed ", len(all_results), " records"
        print "time taken: ", (time.time() - start_time)
    print "finished!"

def point_of_view_experiments(experiment, features_to_use):
    global point_of_view
    #defaulting to full location now just to see
    for this_point in [0, 1, 3, 7, 30, 60, 90]: #one week, one month, 2 months, 3 months
        point_of_view = this_point
        #experiment = "full_location_point_of_view_" + str(this_point) + "_min_max"
        experiment += str(point_of_view)
        fullLocation(experiment, features_to_use)

if __name__ == '__main__':

    experiment = "full_location_point_of_view_optimised_"
    features_to_use = ["weekday_number","week_number","quarter_in_year","day_number","month_number","listing_cluster","days_active","price_dict","cancellation count","enquiry count","k_means_season_day","season_-1","season_-2","season_-3","season_-4","season_-5","season_-6","season_-7","listing_cluster_avg_occupancy_best_match_day_-1","listing_cluster_avg_occupancy_best_match_day_-2","listing_cluster_avg_occupancy_best_match_day_-3","listing_cluster_avg_occupancy_best_match_day_-4","listing_cluster_avg_occupancy_best_match_day_-5","listing_cluster_avg_occupancy_best_match_day_-6","listing_cluster_avg_occupancy_best_match_day_-7","occupancy_match_average","enquiry_match_average","cancelled_match_average","occupancy_match_avg_-1","occupancy_match_avg_-2","occupancy_match_avg_-3","occupancy_match_avg_-4","occupancy_match_avg_-5","enquiry_match_avg_-1","enquiry_match_avg_-2","enquiry_match_avg_-3","enquiry_match_avg_-4","enquiry_match_avg_-5","cancelled_match_avg_-1","cancelled_match_avg_-2","cancelled_match_avg_-3","cancelled_match_avg_-4","cancelled_match_avg_-5","occupancy_match_avg_+1","occupancy_match_avg_+2","occupancy_match_avg_+3","occupancy_match_avg_+4","occupancy_match_avg_+5","enquiry_match_avg_+1","enquiry_match_avg_+2","enquiry_match_avg_+3","enquiry_match_avg_+4","enquiry_match_avg_+5","cancelled_match_avg_+1","cancelled_match_avg_+2","cancelled_match_avg_+3","cancelled_match_avg_+4","cancelled_match_avg_+5"]
    point_of_view_experiments(experiment, features_to_use)






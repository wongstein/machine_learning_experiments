from library import database, my_time, normilisation, feature_helper, common_database_functions, classification
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
        if my_features.listing_important_dates[listing_id]['created_at'].date() > start_date or str(listing_id) not in my_features.json_files['occupancy_dict'].keys():
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
                all_data[listing_id][str(day)] = {'features' : features_to_add, 'classification': classification_to_add}


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
            elif dict_name == 'day_week_historical_encoding':
                to_add = my_features.historical_encoded(listing_id, day, season, point_of_view)
                if to_add is not None:
                    final.append(to_add)
                else:
                    return None
            else:

                #specification in this case is just going to be the amount of data around the week to include around the view_date,
                #which is a year ago.
                #Need to make extra consideration

                #DEBUG
                try:
                    to_add = my_features.history_features(listing_id, dict_name, day, specification, point_of_view)
                except OverflowError:
                    print "hello"

                if to_add is not None:
                    if isinstance(to_add, list):
                        final += to_add
                    else:
                        final.append(to_add)
                else: #to add is None
                    return None

    return final


def fullLocation_data(file_name, normalisation_type = None, with_PCA = None):
    global feature_header, all_data

    #add a buffer to prevent hitting key error with year 2013 for average_cluster_year
    start_date = datetime.date(2014, 1, 20)
    end_date = datetime.date(2016, 1, 29)

    #three city, single listing training and prediction test
    for location_id in [0, 1, 19]:
        print "On location ", location_id

        testing_listings = get_testing_listings([location_id])
        print "number of listings for this location: ", len(testing_listings)


        fill_experiment_data(testing_listings, start_date, end_date)

        with open('data/feature_data/' + str(location_id) + "_" + file_name, 'w') as outFile:
            json.dump(all_data, outFile)

def point_of_view_experiments():
    global point_of_view
    #defaulting to full location now just to see
    for this_point in [0, 1, 3, 7, 30, 60, 90]: #one week, one month, 2 months, 3 months
    #for this_point in [7, 30, 60, 90]:
    #for this_point in [1, 3, 7]:
        point_of_view = this_point
        #experiment = "full_location_point_of_view_" + str(this_point) + "_min_max"

        file_name =  str(point_of_view) + "_all_features"
        fullLocation_data(file_name)

#where the magic happens
def full_experiment():
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
    feature_data_space += [{'occupancy_dict': 'best_match_7'}, {'cluster_averages_year': 'best_match_7'}, {'ENQUIRY': 'best_match_day'}, {'CANCELLED': 'best_match_day'}, {'occupancy_dict': 'best_match_day'}, {'occupancy_dict': 'best_match_average'}, {'ENQUIRY': 'best_match_average'}, {'CANCELLED': 'best_match_average'}]

    #testing features
    feature_data_space += [{'occupancy_dict': 'best_match_average_-2'}, {'ENQUIRY': 'best_match_average_-2'}, {'CANCELLED': 'best_match_average_-2'}]

    #feature_header
    feature_header = ["weekday_number", "week_number", 'quarter_in_year', "day_number", "month_number",'listing_cluster',  "days_active", "price_dict", "cancellation count", "enquiry count",'k_means_season_day']

    feature_header += ['k means season history day -1', 'k means season history day  -2', 'k means season history day -3', 'k means history day -4', 'k means history day -5', 'k means history day -6', 'k means history day -7']

    #for best match
    feature_header += ['occupancy_match_-1', 'occupancy_match_-2', 'occupancy_match_-3', 'occupancy_match_-4', 'occupancy_match_-5', 'occupancy_match_-6', 'occupancy_match_-7', 'cluster_average_match_-1', 'cluster_average_match_-2', 'cluster_average_match_-3', 'cluster_average_match_-4', 'cluster_average_match_-5', 'cluster_average_match_-6', 'cluster_average_match_-7', 'ENQUIRY_match_day', 'CANCELLED_match_day', 'occupancy_match_day']

    #new features
    feature_header += ['occupancy_match_average', 'enquiry_match_average', 'cancelled_match_average']

    point_of_view_experiments()

    print "finished"

if __name__ == '__main__':
    full_experiment()








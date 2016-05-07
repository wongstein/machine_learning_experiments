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
'''
#monte carlo experiments
import monte_carlo_prediction
monte_carlo_prediction.main()

#run other experiments
import point_of_view_machine_learning
import point_of_view_neural

#date base

experiment = "date_base_"
features_to_use = ["weekday_number","week_number","quarter_in_year","day_number","month_number","listing_cluster","days_active","price_dict","cancellation count","enquiry count","k_means_season_day","season_-1","season_-2","season_-3","season_-4","season_-5","season_-6","season_-7"]
#point_of_view_machine_learning.point_of_view_experiments(experiment, features_to_use)
#point_of_view_neural.point_of_view_experiments(experiment, features_to_use, "simple_network")

#Increment
experiment = "date_base_best_match_average"
features_to_use = ["weekday_number","week_number","quarter_in_year","day_number","month_number","listing_cluster","days_active","price_dict","cancellation count","enquiry count","k_means_season_day","season_-1","season_-2","season_-3","season_-4","season_-5","season_-6","season_-7", "occupancy_match_average","enquiry_match_average","cancelled_match_average"]
point_of_view_machine_learning.point_of_view_experiments(experiment, features_to_use)
#point_of_view_neural.point_of_view_experiments(experiment, features_to_use, "simple_network")

#what I think will do best right now
experiment = "full_location_point_of_view_optimised_"
features_to_use = ["weekday_number","week_number","quarter_in_year","day_number","month_number","listing_cluster","days_active","price_dict","cancellation count","enquiry count","k_means_season_day","season_-1","season_-2","season_-3","season_-4","season_-5","season_-6","season_-7","occupancy_match_average","enquiry_match_average","cancelled_match_average","occupancy_match_avg_-1","occupancy_match_avg_-2","occupancy_match_avg_-3","occupancy_match_avg_-4","occupancy_match_avg_-5","enquiry_match_avg_-1","enquiry_match_avg_-2","enquiry_match_avg_-3","enquiry_match_avg_-4","enquiry_match_avg_-5","cancelled_match_avg_-1","cancelled_match_avg_-2","cancelled_match_avg_-3","cancelled_match_avg_-4","cancelled_match_avg_-5","occupancy_match_avg_+1","occupancy_match_avg_+2","occupancy_match_avg_+3","occupancy_match_avg_+4","occupancy_match_avg_+5","enquiry_match_avg_+1","enquiry_match_avg_+2","enquiry_match_avg_+3","enquiry_match_avg_+4","enquiry_match_avg_+5","cancelled_match_avg_+1","cancelled_match_avg_+2","cancelled_match_avg_+3","cancelled_match_avg_+4","cancelled_match_avg_+5"]
#point_of_view_machine_learning.point_of_view_experiments(experiment, features_to_use)
#point_of_view_neural.point_of_view_experiments(experiment, features_to_use, "simple_network")


experiment = "full_location_point_of_occupancy_match_avergae"
features_to_use = ["weekday_number","week_number","quarter_in_year","day_number","month_number","listing_cluster","days_active","price_dict","cancellation count","enquiry count","k_means_season_day","season_-1","season_-2","season_-3","season_-4","season_-5","season_-6","season_-7","occupancy_match_average","occupancy_match_avg_-1","occupancy_match_avg_-2","occupancy_match_avg_-3","occupancy_match_avg_-4","occupancy_match_avg_-5","enquiry_match_avg_-1","enquiry_match_avg_-2","enquiry_match_avg_-3","enquiry_match_avg_-4","enquiry_match_avg_-5"]
point_of_view_machine_learning.point_of_view_experiments(experiment, features_to_use)
point_of_view_neural.point_of_view_experiments(experiment, features_to_use, "simple_network")


experiment = "chance_with_price"
features_to_use = ["price_dict"]
point_of_view_machine_learning.point_of_view_experiments(experiment, features_to_use)
point_of_view_neural.point_of_view_experiments(experiment, features_to_use, "simple_network")


'''
import point_of_view_machine_learning
import point_of_view_neural

features_to_use = ["weekday_number","week_number","quarter_in_year","day_number","month_number","cancellation count", "listing_cluster", "enquiry count","k_means_season_day","occupancy_match_average","enquiry_match_average","cancelled_match_average","occupancy_match_avg_-1","occupancy_match_avg_-2","occupancy_match_avg_-3","occupancy_match_avg_-4","occupancy_match_avg_-5","enquiry_match_avg_-1","enquiry_match_avg_-2","enquiry_match_avg_-3","enquiry_match_avg_-4","enquiry_match_avg_-5","cancelled_match_avg_-1","cancelled_match_avg_-2","cancelled_match_avg_-3","cancelled_match_avg_-4","cancelled_match_avg_-5","occupancy_match_avg_+1","occupancy_match_avg_+2","occupancy_match_avg_+3","occupancy_match_avg_+4","occupancy_match_avg_+5","enquiry_match_avg_+1","enquiry_match_avg_+2","enquiry_match_avg_+3","enquiry_match_avg_+4","enquiry_match_avg_+5","cancelled_match_avg_+1","cancelled_match_avg_+2","cancelled_match_avg_+3","cancelled_match_avg_+4","cancelled_match_avg_+5"]

'''
point_of_view_machine_learning.singleListing("single_listing_optimised_90", features_to_use)
point_of_view_machine_learning.listingCluster("listing_cluster_optimised_90", features_to_use)
point_of_view_machine_learning.fullLocation("full_location_optimised_90", features_to_use)
'''
experiment = "fullLocation_matched_averages_optimized2"
point_of_view_machine_learning.point_of_view_experiments(experiment, features_to_use)
point_of_view_neural.point_of_view_experiments(experiment, features_to_use, "simple_network")

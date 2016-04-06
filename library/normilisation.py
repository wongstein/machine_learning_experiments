import numpy as np
import pandas as pd
from sklearn import preprocessing

'''
columns to normalise should be a list, where columns are assumed to begin with 0 (array indexing)
'''

class normalisation():
    def __init__(self, training_data, header_list, name_of_type, columns_to_normalise = None):
        #really only need the normalisation object, not the dataframe (plus would mean holding a lot more data in memory that I don't want to)
        #save self dataframe

        if name_of_type:
            if name_of_type == "min_max":
                self._make_min_max_object(training_data, header_list, columns_to_normalise)
            elif name_of_type == "z-standard":
                self._make_z_standardisation(training_data, header_list, columns_to_normalise)

    def _make_min_max_object(self, all_feature_data, header_list, columns_to_normalise = None):

        #turn into pandas table
        df = self._make_dataframe(all_feature_data, header_list)

        if columns_to_normalise:
            headers_to_normalise = columns_to_normalise
        else:
            #default to all
            headers_to_normalise = header_list

        self.normalisation_model = preprocessing.MinMaxScaler().fit(df[headers_to_normalise])

    def _make_z_standardisation(self, all_feature_data, header_list, columns_to_normalise = None):
        #turn into pandas table
        df = self._make_dataframe(all_feature_data, header_list)

        if columns_to_normalise:
            headers_to_normalise = columns_to_normalise
        else:
            #default to all
            headers_to_normalise = header_list

        self.normalisation_model = preprocessing.StandardScaler().fit(df[headers_to_normalise])


    def transform_data(self, training_data, header_list, columns_to_normalise = None):
        df = self._make_dataframe(training_data, header_list)

        if columns_to_normalise:
            headers_to_normalise = columns_to_normalise
        else:
            #default to all
            headers_to_normalise = header_list


        df[headers_to_normalise] = self.normalisation_model.fit_transform(df[headers_to_normalise])

        #more useful to return everythign as a list

        #returns list of list
        return df.values.tolist()

    def _make_dataframe(self, all_feature_data, header_list):
        #turn into pandas table
        if isinstance(all_feature_data, list) and header_list:
            df = pd.DataFrame(all_feature_data, columns = header_list)
        elif isinstance(all_feature_data, list) and not header_list:
            print "You need to provide a column list when making the data frame"
            sys.exit()
        else:
            #this is already a data frame
            df = all_feature_data

        return df

def test():
    feature_data = [[6, 4, 0.75, 26, 7, 1L, 6, 0, 0, 0, 0, 0.35294117647058826, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.47058823529411764, 0.35294117647058826, 0.35294117647058826, 0.35294117647058826, 0.35294117647058826, 0.29411764705882354, 0.35294117647058826], [0, 1, 0.5, 16, 6, 1L, -399, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1], [0, 5, 1.0, 24, 11, 1L, -238, 0, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1], [3, 1, 0.5, 2, 4, 1L, -109, 0, 0, 0, 2, 0.5555555555555556, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 2, 1, 1, 0.5555555555555556, 0.4444444444444444, 0.4444444444444444, 0.4444444444444444, 0.5555555555555556, 0.5555555555555556, 0.5555555555555556], [3, 1, 0.25, 26, 3, 1L, -116, 0, 0, 0, 1, 0.5555555555555556, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 2, 2, 0, 0.5555555555555556, 0.4444444444444444, 0.4444444444444444, 0.2222222222222222, 0.5555555555555556, 0.4444444444444444, 0.4444444444444444], [0, 3, 0.5, 12, 5, 1L, -434, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
    feature_header = ["weekday_number", "week_number", 'quarter_in_year', "day_number", "month_number",'listing_cluster',  "days_active", "price_dict", "cancellation count", "enquiry count",'k_means_season_day', 'cluster_average', 'occupation history day -1', 'occupation history day -2', 'occupation history day - 3', 'occupation history day - 4', 'occupation history day -5', 'occupation history day -6', 'occupation history day -7',  'k means season history day -1', 'k means season history day  -2', 'k means season history day -3', 'k means history day -4', 'k means history day -5', 'k means history day -6', 'k means history day -7', 'cluster averages day -1', 'cluster averages day -2', 'cluster averages day -3', 'cluster averages day -4', 'cluster averages day -5', 'cluster averages day -6', 'cluster averages day -7']


    #model = normilisation.normalisation(feature_data, feature_header, "min_max")
    #model = normilisation.normalisation(feature_data, feature_header, "z-standard")

    transformed_data = model.transform_data(feature_data, feature_header)
    print "hello"


if __name__ == '__main__':
    test()










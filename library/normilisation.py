import numpy as np
import pandas as pd
from sklearn import preprocessing

'''
columns to normalise should be a list, where columns are assumed to begin with 0 (array indexing)
'''

class normalisation():
    def __init__(self, dataframe, name_of_type):
        #really only need the normalisation object, not the dataframe (plus would mean holding a lot more data in memory that I don't want to)
        #save self dataframe

        if name_of_type:
            if name_of_type == "min_max":
                self._make_min_max_object(dataframe)
            elif name_of_type == "z-standard":
                self._make_z_standardisation(dataframe)

    #will input just ddataframe with features needed
    def _make_min_max_object(self, dataframe):
        self.normalisation_model = preprocessing.MinMaxScaler().fit(dataframe)

    def _make_z_standardisation(self, dataframe):

        self.normalisation_model = preprocessing.StandardScaler().fit(dataframe)


    def transform_data(self, dataframe):

        transformed_list = self.normalisation_model.fit_transform(dataframe)

        return transformed_list


if __name__ == '__main__':
    test()










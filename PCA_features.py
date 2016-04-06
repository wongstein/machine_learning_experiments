from matplotlib.mlab import PCA as mlabPCA
from matplotlib import pyplot as plt
from sklearn import decomposition
from library import database

def do_PCA_analysis(experiment_name, transformed_data, feature_header, city_id, number_components = None, graph_classification_list = None):

    #PCA
    pca = decomposition.PCA(n_components = number_components)
    X = pca.fit_transform(transformed_data)

    #def save_to_database(city, feature_header, feature_varience, experiment_name)
    if not number_components:
        print "here is the number of components, ", pca.n_components
        print "Here is the number of components with maximum variance, and their number of features each,", pca.components_.shape
        print "here is the explained variance ratio for each component"
        print feature_header
        print '\n'
        print pca.explained_variance_ratio_
        save_to_database(city_id, feature_header, pca.explained_variance_ratio_.tolist(), experiment_name)

    #only really useful if transforming with n_components
    #graph that shit
    if graph_classification_list:
        _pca_graph(transformed_data, graph_classification_list, city_id, 2)

    return X.tolist()

'''
transformed data will be a list of lists
'''
def _pca_graph(transformed_data, graph_classification_list, city_id, number_components = 2):
    #need to solve occupancy problem
    pca = decomposition.PCA(n_components = number_components)
    sklearn_transf = pca.fit_transform(transformed_data).tolist()

    #sort data into occupancy and non occupancy groups
    occupancy = []
    non_occupancy = []
    for x, entry in enumerate(graph_classification_list):
        if int(entry) == 1:
            occupancy.append(sklearn_transf[x])
        elif int(entry) == 0:
            non_occupancy.append(sklearn_transf[x])


    plt.plot(occupancy[:][0], occupancy[:][1], 'o', markersize=7, color='blue', alpha=0.5, label='occupancy')
    plt.plot(non_occupancy[:][0], non_occupancy[:][1], '^', markersize=7, color='red', alpha=0.5, label='non occupancy')

    plt.legend()
    plt.title('Transformed samples with class labels from matplotlib.mlab.PCA()')

    plt.show()

def save_to_database(city, feature_header, feature_varience, experiment_name):
    thesis_data = database.database("Thesis")

    location_dict = {1: "Barcelona", 0: "Rome", 19: "Amsterdam"}
    #clear table
    query = "DELETE FROM `feature_varience` WHERE `city` = '" + location_dict[city] + "' AND `type_standardsiation` = '" + experiment_name + "';"
    thesis_data.execute(query)
    #table: feature_variance
    #city, feature_name, variance, type_standardsiation
    query = "INSERT INTO `feature_varience` VALUES ('%s', '%s', %s, '%s');"
    for x, entry in enumerate(feature_header):

        to_insert = (location_dict[city], entry, feature_varience[x], experiment_name)

        thesis_data.execute(query % to_insert)

    print "Finished saving to database"






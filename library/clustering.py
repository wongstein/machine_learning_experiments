from sklearn.cluster import DBSCAN, KMeans
from sklearn.mixture import DPGMM



'''
Meant to turn output from classification methods below into a dictionary where the key is the cluster, and the values are a list of the identification

output: key: [identifications belonging to key]
'''
def list_dict_by_cluster(list_list):
    final = {str(label): [] for label in [prediction[1] for prediction in list_list]}
    for entry in list_list:
        final[str(entry[1])].append(entry[0])

    return final

def _make_final_list(identification, labels):
    final = []
    for n in range(0,len(identification)):
        final.append([identification[n],labels[n]])
    return final

'''
The classification programs return a simple list of lists where the nested list has a structure like this: [identification, predicted label]
'''
def DBSCAN(cluster_data, identification):
        #try the dbscn
    dbscan = DBSCAN().fit(cluster_data)
    core_samples_mask = np.zeros_like(dbscan.labels_, dtype=bool)
    core_samples_mask[dbscan.core_sample_indices_] = True
    labels = dbscan.labels_
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

    print('Estimated number of clusters with DBSCAN: %d' % n_clusters_)
    return _make_final_list(identification, labels)



def Dirichlet(cluster_data, identification, iteration_number = 1):
    print "In Dirichlet"
    for i in range(0,iteration_number):
        print "On iteration number ", i
        dirichlet = DPGMM(n_components = len(cluster_data)).fit(cluster_data)
    #paremeters= dirichlet.get_params #returns parameters of the algorithm as a whole from the fit
        predict = dirichlet.predict(cluster_data)
        n_clusters_ = len(set(predict)) - (1 if -1 in predict else 0)
        print('Estimated number of clusters with Dirichlet: %d' % n_clusters_)

    return _make_final_list(identification, predict)


def K_Means(cluster_data, identification, number_clusters):
    print "Let's K-Means cluster this stuff with %s clusters" % number_clusters

    #do the clustering
    model = KMeans(n_clusters = number_clusters).fit(cluster_data)
    labels = model.labels_

    return _make_final_list(identification, labels)

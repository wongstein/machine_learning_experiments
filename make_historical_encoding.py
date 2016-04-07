from library import my_time
import json

'''
want to make historical encoding for every year, for every type of data
'''


with open("data/k-means_season_clusters.json") as jsonFile:
    k_means = json.load(jsonFile)

'''
#maybe can optimise by making one for each k-means-seasons

for day of the week: for whole year

for days of the month, for whole year
weeks of month: restricted to the specific month

for month, restricted to the year

for quarter of year, restricted to year

k-means_cluster = proportion in the year

output:

day_week_historical_encoding.json
day_month_historical_encoding.json
month_historical_encoding.json
quarter_year_historical_encoding.json
k_means_historical_encoding.json


#per listing
'''

quarters = {1: [1,2,3], 2:[4,5,6], 3:[7,8,9], 4: [10,11,12]}


final_dict = {'days_in_week': {}, 'days_of_month': {}, 'month': {}, 'quarter_in_year': {}, 'k-means': {}}



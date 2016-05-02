import json
import datetime
import database
import common_database_functions
import os

''''
These are the helper functions to make the machine learning features
'''

class Features():
	def __init__(self, feature_space = None):
		self.json_files = {"day_features": {}, "occupancy_dict": {}, 'cluster_averages_year': {}, 'k-means_season_clusters': {}}
		self.fill_global_data()

		if feature_space:
			self.feature_space = feature_space

	def add_new_feature_json(self, dict_name):
		#load json if it doesn't exist in json_files:
		if dict_name in ["price_dict", "k-means_season_clusters", 'cluster_averages', 'cluster_averages_year', 'day_week_historical_encoding'] and dict_name not in self.json_files.keys():
			try:
				with open("data/" + dict_name + ".json") as jsonFile:
					self.json_files[dict_name] = json.load(jsonFile)
			except IOError:
				os.chdir("..")
				with open("data/" + dict_name + ".json") as jsonFile:
					self.json_files[dict_name] = json.load(jsonFile)
				os.chdir("library")

		elif dict_name in ['CANCELLED', 'ENQUIRY'] and 'reservation_dict' not in self.json_files.keys():

			try:
				with open("data/reservation_dict.json") as jsonFile:
					self.json_files['reservation_dict'] = json.load(jsonFile)
			except IOError:
				os.chdir("..")
				with open("../data/reservation_dict.json") as jsonFile:
					self.json_files['reservation_dict'] = json.load(jsonFile)
				os.chdir('library')


	def fill_global_data(self):
		for filename in self.json_files.keys():
			self.json_files[filename] = self._load_json(filename)

		#earliest dates
		worldhomes_data = database.database("worldhomes")
		listing_important_dates_list = worldhomes_data.get_data("SELECT `id`, `created_at`, `updated_at`, `deleted_at`, `active` FROM `listings`")
		self.listing_important_dates = {entry[0]: {"created_at": entry[1], "updated_at": entry[2], "deleted_at": entry[3], "active": entry[4]} for entry in listing_important_dates_list}

		worldhomes_data.destroy_connection()


		self.listing_location_pair = common_database_functions.location_listing_pairings(True)
		self.listing_cluster_pair = common_database_functions.listing_cluster_type_pairings(return_dict = True)
	'''
	expecting input to be liek this: [ json_name: specification,]
	also expecting the whole, updated feature_space
	'''
	def update_feature_space(self, new_feature_space):
		self.feature_space = new_feature_space

		for this_dict in new_feature_space:
			self.add_new_feature_json(this_dict.keys())

	#The real feature crunching and returning
	def days_active_feature(self, listing_id, day):
		days_diff = int( (day - self.listing_important_dates[listing_id]['created_at'].date()).days)

		if days_diff < 0: #this listing hasn't become active yet
			return None

		return days_diff


	def date_features(self, feature_name, day):
		return self.json_files['day_features'][day.strftime("%Y-%m-%d")][feature_name]

	def season_cluster_feature(self, location, date):
		to_add = int(self.json_files[dict_name][view_date.strftime("%Y")][str(location)]["3"][date.strftime("%Y-%m-%d")])
		return to_add


	def make_best_match(self, listing_id, dict_name, date, point_of_view, return_final_date = False):
		#want to match the date with the most similar k-cluster (day of the week) value that is < point_of_view
		#only for enquiries, cancellations, occupancy, seasons averages
		date_season_designation = self.k_means_season_cluster_feature(listing_id, date)

		if date_season_designation is None:
			return None

		not_found = True
		go_back_week = 0

		while(not_found):
			test_date = date - datetime.timedelta(7 * go_back_week)
			if test_date > date - datetime.timedelta(point_of_view):
				#in case point of view was actually less than 7, then some of the immediate data is valid for consideration in best match
				#if point of view is negative, then this will make date higher, and the current test_date should suffice, because it'll be the current date
				go_back_week += 1
				continue
			if test_date < datetime.date(2014, 1, 1): #cutoff for most good data
				return None
			if self.k_means_season_cluster_feature(listing_id, test_date) == date_season_designation:
				if dict_name in ['ENQUIRY', 'CANCELLED', 'occupancy_dict']:
					to_add = self.reservation_history_feature(listing_id, dict_name, test_date, point_of_view = 0)
					if to_add:
						if return_final_date:
							return (to_add, test_date)
						else:
							return to_add
					else:
						if return_final_date:
							return (0, test_date)
						else:
							return 0
				else: #cluster_averages
					to_add = self.cluster_averages_feature(listing_id, test_date)
					if to_add is None:
						return None
					else:
						if return_final_date:
							return (to_add, test_date)
						else:
							return to_add
			else:
				go_back_week += 1

	def make_best_match_average(self, listing_id, dict_name, date, point_of_view, to_average_number):
		test_date = date - datetime.timedelta(point_of_view)

		final = []
		for x in xrange(0, to_average_number, 1):
			this_returned = self.make_best_match(listing_id, dict_name, test_date, 0, True)
			if this_returned is not None:
				final.append(this_returned[0])
				test_date = this_returned[1]
			else:
				x -= 1

		if final:
			return float(sum(final))/len(final)
		else:
			return None


	def history_features(self, listing_id, dict_name, date, specification = None, point_of_view = None):

	#specification in this case is just going to be the amount of data around the week to include around the view_date, which is a year ago.

		#reservation_history_feature(self, listing_id, dict_name, day, point_of_view = 0
		if specification == 'best_match_7' : #only for enquiry, cancelled, and cluster_averages and must have a point of view
			if point_of_view is None:
				print "you must put in a point of view for this to work"
				sys.exit()

			final = []
			for x in range(1, 8):
				this_date = date - datetime.timedelta(x)
				this_point_of_view = point_of_view - x
				to_add = self.make_best_match(listing_id, dict_name, this_date, this_point_of_view)
				if to_add is None:
					return None
				final.append(to_add)
			return final
		elif specification == "best_match_day":
			to_add = self.make_best_match(listing_id, dict_name, date, point_of_view)
			if to_add is not None:
				return to_add
			else:
				return None
		elif specification == "best_match_average":
			to_add = self.make_best_match_average(listing_id, dict_name, date, point_of_view, 10)

			if to_add is not None:
				return to_add
			else:
				return None
		elif specification in ["best_match_average_-2", "best_match_average_-2"]:
			final = []
			for delta_time in xrange(1, 3, 1):
				if specification == "best_match_average_-2":
					date_inspection = date - datetime.timedelta(delta_time)
				else:
					date_inspection = date + datetime.timedelta(delta_time)
				to_add = self.make_best_match_average(listing_id, dict_name, date_inspection, point_of_view, 10)
				if to_add is not None:
					final.append(to_add)
				else:
					return None
			return final
		else:
			if specification:
				if not isinstance(specification, int):
					print "The specification added to a history feature (occupancy, eqnruiy, cancelled, price, season designation, anything market intelligence) needs to be an int."
					sys.exit()

				final = []
				for x in range(1, specification + 1):
					this_day = date - datetime.timedelta(x)
					if dict_name in ['occupancy_dict', 'price_dict', 'ENQUIRY', 'CANCELLED']:
						to_add = self.reservation_history_feature(listing_id, dict_name, this_day, point_of_view)
						if to_add is not None:
							final.append(to_add)
						else:
							final.append(0) #for cancelled and enquiry.  occupancy earliest_date checks in PCA_feature codes
					elif dict_name == 'k-means_season_clusters':
						final.append(self.k_means_season_cluster_feature(listing_id, this_day))
					elif dict_name == 'cluster_averages_year':
						date_examination = this_day
						to_add = self.cluster_averages_feature(listing_id, date_examination)
						if to_add != None:
							final.append(to_add)
						elif to_add is None:
							return None
				if final is []:
					return None

				return final
			elif not specification:
				if dict_name in ['occupancy_dict', 'ENQUIRY', 'CANCELLED', 'price_dict']:
					to_add = self.reservation_history_feature(listing_id, dict_name, date, point_of_view)
					if to_add is not None:
						return to_add
					else:
						return 0
				elif dict_name == 'k-means_season_clusters':
					return self.k_means_season_cluster_feature(listing_id, date)
				elif dict_name == 'cluster_averages_year':
					date_examination = date - datetime.timedelta(point_of_view)
					return self.cluster_averages_feature(listing_id, date_examination)


	def k_means_season_cluster_feature(self, listing_id, day):
		#k-Means_cluster: {year: {location_id: k_means_type: day: cluster_designation} }
		#
		#get location_id
		location_id = self.listing_location_pair[listing_id]
		try:
			return int(self.json_files['k-means_season_clusters'][str(day.year)][str(location_id)]['3'][str(day)])
		except KeyError:
			#because the date is a bit too early, sometimes it happens with the point of view functionality
			return None

	#full_year structure is by thee primary key, then location_cluster, then listing_cluster: day: average
	#clustering for the whole location?
	def cluster_averages_feature(self, listing_id, day):
		location_id = self.listing_location_pair[listing_id]

		#will add all cluster averages in the location.  Let's put this on hold for a moment
		'''
		final = []
		for cluster_id in location_dict.keys():
			final.append(location_dict[cluster_id][day])
		'''

		cluster_id = self.listing_cluster_pair[listing_id]
		try:
			#already returns a float
			return self.json_files['cluster_averages_year'][str(day.year)][str(location_id)][str(cluster_id)][str(day)]
		except Exception as e: # Most likely a keyError, the listing cluster didn't have enough data to be included
			return None


	def reservation_history_feature(self, listing_id, dict_name, day, point_of_view = 0):

		if dict_name in ['occupancy_dict', 'price_dict']:
			to_add = self.json_files[dict_name][str(listing_id)][str(day.year)][str(day)]
			if to_add:
				return int(to_add)
			else:
				return 0
		else: #it's cancelled, or enquiries
			all_possible_reservations = self.json_files['reservation_dict'][str(listing_id)][str(day.year)][str(day)]

			if not all_possible_reservations:
				return 0

			tot_count = 0
			for reservation_id, reservation_data in all_possible_reservations.iteritems():
				created_at = datetime.datetime.strptime(reservation_data['created_at'], "%Y-%m-%d").date()
				if created_at <= (day - datetime.timedelta(point_of_view)):
					if dict_name == 'CANCELLED' and reservation_data['status'] == 'CANCELLED':
						tot_count += 1
					elif dict_name != 'CANCELLED': #always increment for enquiries
						tot_count += 1

			return tot_count

	def historical_encoded(self, listing_id, day, season, point_of_view):
		try:
			to_add = self.json_files['day_week_historical_encoding'][str(point_of_view)][str(listing_id)][str(day)][str(day.weekday())]
			return to_add
		except KeyError:
			return None

	def _load_json(self, filename):
		if filename == "day_features":
			thesis_data = database.database("Thesis")
			list_data = thesis_data.get_data("SELECT * FROM `date_to_day`;")
			thesis_data.destroy_connection()
			return {str(datetime.date(entry[4], entry[2], entry[1])): {"weekday_number": int(entry[3]), "day_number": int(entry[1]), "week_number": int(entry[0]), "month_number": int(entry[2]), "quarter_in_year": float((entry[2]-1)/3 + 1)/4, "year": int(entry[4])} for entry in list_data}
		else:
			try:
				with open("data/" + filename + ".json") as jsonFile:
					this_dict = json.load(jsonFile)
			except IOError:
				os.chdir("..")
				with open("data/" + filename + ".json") as jsonFile:
					this_dict = json.load(jsonFile)
				os.chdir("library")

		return this_dict

def test():
	listing_ids = [20, 1071]

	#feature_data_space = [{"weekday_number": None}, {"week_number": None}, {"quarter_in_year": None}, {"day_number": None}, {"month_number": None}, {"listing_cluster": None}]

	feature_data_space = [{'occupancy_dict': 'best_match_7'}, {"days_active": None}, {"price_dict": None}, {'CANCELLED': "best_match_day"}]

	my_features = Features(feature_data_space)
	point_of_view = 3
	day = datetime.date(2014, 4, 16)

	all_data = []
	for listing_id in listing_ids:
		final = []
		for dict_combo in feature_data_space:
			for dict_name, specification in dict_combo.iteritems():
 				#add dict if needed
 				my_features.add_new_feature_json(dict_name)

 				if dict_name not in ['CANCELLED', 'ENQUIRY']:
					my_features.add_new_feature_json(dict_name)
				else:
					my_features.add_new_feature_json('reservation_dict')

				#check if there's a point of view requirement
				try:
					view_date = day - datetime.timedelta(point_of_view)
				except TypeError: #point of view is still none
					view_date = day

				#the real stuff of feature addition, switch statement
				if dict_name == 'listing_cluster':
					final.append(listing_cluster)

				#feature helper features
				elif dict_name in ["days_active"]:
					to_add = my_features.days_active_feature(listing_id, day)
					if to_add is not None:
						final.append(to_add)
					else:
						return None
				#day features
				elif dict_name in ["weekday_number", "week_number", "quarter_in_year", "day_number", "month_number"]:
					final.append(my_features.date_features(dict_name, view_date))

				else:
					#specification in this case is just going to be the amount of data around the week to include around the view_date, which is a year ago.
					to_add = my_features.history_features(listing_id, dict_name, day, specification, point_of_view)

					if to_add and isinstance(to_add, list):
						final += to_add
					elif to_add != False:
						final.append(to_add)
					else: #to add is false
						return None

		all_data.append(final)

		print "hello"


if __name__ == '__main__':
	#test()
	listing_id = 7836L
	point_of_view = 7
	date = datetime.date(2015, 3, 26)
	feature_data_space = {'occupancy_dict': 'best_match_average'}
	my_features = Features(feature_data_space)

	for dict_name, specification in feature_data_space.iteritems():
		print my_features.history_features(listing_id, dict_name, date, specification, point_of_view)





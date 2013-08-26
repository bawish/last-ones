import json
import urllib
import urllib2
import csv
import re
from rdio import Rdio
from credentials import *
import sys
import time

ROOT_URL = 'http://ws.audioscrobbler.com/2.0/'

#query Last.fm API to get date ranges available
#returns a list of dictionaries with "to" and "from" keys
def get_dates():
	dates = []
	query = {'method': 'user.getweeklychartlist', 'user': LAST_FM_USER_NAME,
			 'api_key': LAST_FM_KEY, 'format': 'JSON'}
	URL = '?'.join([ROOT_URL, urllib.urlencode(query)])
	data = json.load(urllib2.urlopen(URL))['weeklychartlist']['chart']
	
	count = 0

	for record in data:
		date_range = {'from': record['from'], 'to': record['to'], 'index': count}
		count += 1
		dates.append(date_range)
		
	return dates

#accepts the array of dicts with "to" and "from" values returned by getDates
def get_tracks(date_ranges):
	charts = []	
	
	for date in date_ranges:
		tracks = []
		query = {'method': 'user.getweeklytrackchart', 'user': LAST_FM_USER_NAME,
				 'api_key': LAST_FM_KEY, 'format': 'JSON', 'from': date['from'],
				 'to': date['to']}
		url = '?'.join([ROOT_URL, urllib.urlencode(query)])
		response = json.load(urllib2.urlopen(url))

		if 'track' in response['weeklytrackchart']:
			try:
				for entry in response['weeklytrackchart']['track']:
					#playcount and url are extraneous
					track_record = {'name': entry['name'].encode('utf8'), #csv requires utf-8
									'artist': entry['artist']['#text'].encode('utf8'),
									'rank': entry['@attr']['rank'],
									'playcount': entry['playcount']} 
					tracks.append(track_record)
					print 'Adding %s by %s' % (entry['name'], entry['artist']['#text'])
			except TypeError, e:
				pass
		else:
			print 'No tracks'
	
		charts.append({'week': {'from': date['from'], 'to': date['to'], 'index': date['index']},
					   'tracks': tracks})
	
	return charts
	
#takes in a track dictionary and looks for it in rdio, returns track key if found
def find_track(track):
    query = track['artist']+' '+track['name']

    try:
        search = rdio.call('search', { 'query' : query, 'types' : 'Track' })
        search = search['result']['results'] #gets rid of extraneous matter from search query return
        for result in search:
            if re.search(track['artist'], result['artist'], flags=re.IGNORECASE) != None:
                if re.search(track['name'], result['name'], flags=re.IGNORECASE) != None:
                    if result['canStream']:
                        return result['key']
    except UnicodeDecodeError, UnicodeEncodeError:
        pass
	
def make_playlist(charts):
	track_keys = []
	
	for chart in charts:
		for track in chart['tracks']:
			if track['rank'] == '1':
				print "Searching for %s" % track['name']
				track_key = find_track(track)
				if track_key != None:
					print "Found %s" % track['name']
					track_keys.append(track_key)
				
	print "\nSorting track keys...\n"
	track_keys_de_duped = []
	
	#reverses list so that newest tracks appear at top of playlist
	for i in reversed(track_keys):
		if i not in track_keys_de_duped:
			track_keys_de_duped.append(i)
			
	#convert track list into single, comma-separated string (which is required for some silly reason)
	keys_string = ', '.join(track_keys_de_duped)
	
	print "Creating playlist...\n"
	return rdio.call('createPlaylist', {'name': sys.argv[1], 
								 'description': 'My weekly number ones from Last.fm', 
								 'tracks': keys_string})

def update_history():
	f = open('history.csv', 'rb')
	last_index = f.readlines()[-1].split(',')[2] #should access final week_count, may need to update number
	date_ranges = get_dates()
	new_weeks = date_ranges[(last_index+1):] #new_weeks includes ranges not yet searched
	charts = get_tracks(date_ranges)
	
	#initialize rdio object
	rdio = Rdio((RDIO_CONSUMER_KEY, RDIO_CONSUMER_SECRET), (RDIO_TOKEN, RDIO_TOKEN_SECRET))
	
	track_keys = []
	
	for chart in charts:
		for track in chart['tracks']:
			if track['rank'] == '1':
				print "Searching for %s" % track['name']
				track_key = find_track(track)
				if track_key != None:
					print "Found %s" % track['name']
					track_keys.append(track_key)
				
	print "\nSorting track keys...\n"
	track_keys_de_duped = []
	
	#reverses list so that newest tracks appear at top of playlist
	for i in reversed(track_keys):
		if i not in track_keys_de_duped:
			track_keys_de_duped.append(i)
			
	#convert track list into single, comma-separated string (which is required for some silly reason)
	keys_string = ', '.join(track_keys_de_duped)
	
	rdio.call('addToPlaylist', {'playlist': LAST_ONES_PLAYLIST_KEY, 'tracks': keys_string})
    	

if __name__ == '__main__':
	date_ranges = get_dates()
	charts = get_tracks(date_ranges)
	
	#write to csv
	f = open('history.csv', 'w')
	writer = csv.writer(f)
	writer.writerrow(['week_from', 'week_to', 'week_index', 'track_name', 'track_artist',
					  'track_rank', 'track_playcount'])
	for chart in charts:
		for track in chart['tracks']:
			writer.writerow([chart['week']['from'], chart['week']['to'], chart['week']['index'],
							 track['name'], track['artist'], track['rank'],
							 track['playcount']])
	f.close()
	
	print "\nFile created, now creating playlist"
	
	print "\nOpening Rdio connection...\n"
	rdio = Rdio((RDIO_CONSUMER_KEY, RDIO_CONSUMER_SECRET), (RDIO_TOKEN, RDIO_TOKEN_SECRET))
	
	print make_playlist(charts)
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

#initialize rdio object
rdio = Rdio((RDIO_CONSUMER_KEY, RDIO_CONSUMER_SECRET), 
		    (RDIO_TOKEN, RDIO_TOKEN_SECRET))

#puts last track of a playlist at start
def make_last_track_first(playlist_key = LAST_ONES_PLAYLIST_KEY):
	tracks_on_playlist = rdio.call('get', {'keys': playlist_key, 'extras': 'tracks'})
	tracks_on_playlist = tracks_on_playlist['result'][playlist_key]['tracks']

	track_keys = []

	for track in tracks_on_playlist:
		track_keys.append(track['key'])

	track_keys.insert(0, track_keys[-1])
	track_keys.pop()

	track_keys_string = ', '.join(track_keys)

	rdio.call('setPlaylistOrder', {'playlist': playlist_key, 'tracks': track_keys_string})

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

# accepts a DICTIONARY with 'to' and 'from' keys
def get_weekly_chart_data(date_range):	
	query = {'method': 'user.getweeklytrackchart', 'user': LAST_FM_USER_NAME,
			 'api_key': LAST_FM_KEY, 'format': 'JSON', 'from': date_range['from'],
			 'to': date_range['to']}
	url = '?'.join([ROOT_URL, urllib.urlencode(query)])
	response = json.load(urllib2.urlopen(url))
	return response

#accepts the array of dicts with "to" and "from" values returned by getDates
def get_tracks(date_ranges):
	charts = []	
	
	for date in date_ranges:
		track_list = []
		
		api_call = get_weekly_chart_data(date)['weeklytrackchart']

		time.sleep(1.0)

		if 'track' in api_call:
			
			try:
				tracks = api_call['track']
				
				play_count = '' # re-set this to the play-count of each week's #1
				
				for track in tracks:					
					if track['@attr']['rank'] == '1':
						play_count = track['playcount']
						track_record = {'name': track['name'].encode('utf8'), #csv requires utf-8
										'artist': track['artist']['#text'].encode('utf8'),
										'rank': track['@attr']['rank'],
										'playcount': track['playcount']} 
						track_list.append(track_record)
						print 'Adding %s by %s' % (track['name'], track['artist']['#text'])
					elif track['playcount'] == play_count:
						# should be identical to above, i'm too lazy to make it a new function
						track_record = {'name': track['name'].encode('utf8'), #csv requires utf-8
										'artist': track['artist']['#text'].encode('utf8'),
										'rank': track['@attr']['rank'],
										'playcount': track['playcount']} 
						track_list.append(track_record)
						print 'Adding %s by %s' % (track['name'], track['artist']['#text'])
			except TypeError, e:
				pass
		else:
			print 'No tracks'
	
		charts.append({'week': {'from': date['from'], 'to': date['to'], 'index': date['index']},
					   'tracks': track_list})
	
	return charts
	
# takes in a track dictionary and looks for it in rdio, returns track key if found
# update this to include smarter seatgeek-style thresholds?
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
		time.sleep(1.0)
    except (UnicodeDecodeError, UnicodeEncodeError, urllib2.HTTPError):
        pass
	
def make_playlist():
	date_ranges = get_dates()
	charts = get_tracks(date_ranges)
	
	track_keys = [] # for creating the playlist
	track_list = [] # for writing to csv
	
	for chart in charts:
		for track in chart['tracks']:
			current_track = {'from': chart['week']['from'], 
							 'to': chart['week']['to'], 
							 'index': chart['week']['index'], 
							 'name': track['name'], 
							 'artist': track['artist'], 
							 'rank': track['rank'], 
							 'playcount': track['playcount']}
			track_list.append(current_track) # for writing clean to csv
			
			print "Searching for %s" % track['name']
			track_key = find_track(track)
			if track_key != None:
				print "Found %s" % track['name']
				track_keys.append(track_key)
	
	print "\nWriting history to CSV...\n"
	write_history(track_list)
				
	print "\nSorting track keys to create playlist...\n"
	track_keys_de_duped = []
	
	#reverses list so that newest tracks appear at top of playlist
	for i in reversed(track_keys):
		if i not in track_keys_de_duped:
			track_keys_de_duped.append(i)
			
	#convert track list into single, comma-separated string (which is required for some silly reason)
	keys_string = ', '.join(track_keys_de_duped)
	
	print "Creating playlist...\n"
	return rdio.call('createPlaylist', {'name': 'Last Ones', 
								 'description': 'My weekly number ones from Last.fm', 
								 'tracks': keys_string})

# get all the track keys for a given playlist
# returns a list of track keys
def get_playlist_tracks(playlist_key):
	track_keys = (rdio.call('get', {'keys': playlist_key, 
									'extras': 'trackKeys'})
				  ['result'][playlist_key]['trackKeys'])
	return track_keys

def update_playlist(history_file = 'history.csv', 
				   playlist_key = LAST_ONES_PLAYLIST_KEY):
	
	#hacky way access index of last row of csv
	with open(history_file, 'rb') as f:
		print "Opening history.csv" # FOR DEBUG
		index_holder = []
		reader = csv.reader(f)
		for row in reader:
			index_holder.append(row[2])
		last_index = int(index_holder[-1])
		print "\nIndex is %s\n" % last_index #for de-bugging
	
	date_ranges = get_dates()
	
	#new_weeks includes ranges not yet searched
	new_weeks = date_ranges[(last_index+1):]
	print "New weeks are:\n%s" % new_weeks # for de-bugging
	new_charts = get_tracks(new_weeks)
		
	existing_track_keys = get_playlist_tracks(playlist_key) 
	new_track_keys = [] #for updating playlist
	track_list = load_history(history_file) #for re-writing history
	
	for chart in new_charts:
		for track in chart['tracks']:
			
			#update csv list
			current_track = {'from': chart['week']['from'], 
							 'to': chart['week']['to'], 
							 'index': chart['week']['index'], 
							 'name': track['name'], 
							 'artist': track['artist'], 
							 'rank': track['rank'], 
							 'playcount': track['playcount']}
			track_list.append(current_track) # add to list for csv
			
			#add to list for playlist updating
			print "Searching for %s" % track['name']
			track_key = find_track(track)
			if track_key != None:
				if not track_key in existing_track_keys:
					print "Found new track %s" % track['name']
					new_track_keys.append(track_key)
				
	print "\nRe-writing history CSV...\n"
	write_history(track_list)
	
	for key in new_track_keys:
		rdio.call('addToPlaylist', {'playlist': playlist_key, 'tracks': key})
		make_last_track_first(playlist_key)

# returns list of dicts formed from rows of history CSV
def load_history(history_file = 'history.csv'):
	f = open(history_file, 'rb')
	reader = csv.reader(f)
	
	track_list = []
	
	for row in reader:
		track_entry = {'from': row[0], 'to': row[1], 'index': row[2],
					   'name': row[3], 'artist': row[4], 'rank': row[5],
					   'playcount': row[6]}
		track_list.append(track_entry)
	
	f.close()
	
	return track_list

def write_history(track_list):
	f = open('history.csv', 'w')
	writer = csv.writer(f)
	
	for track in track_list:
		writer.writerow([track['from'], track['to'], track['index'],
						track['name'], track['artist'], track['rank'],
						track['playcount']])
	f.close()
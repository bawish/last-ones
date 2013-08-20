import json
import urllib
import urllib2
import csv
import re
from rdio import Rdio
from credentials import *
import sys

ROOT_URL = 'http://ws.audioscrobbler.com/2.0/'

#query Last.fm API to get date ranges available
#returns a list of dictionaries with "to" and "from" keys
def getDates():
	dates = []
	query = {'method': 'user.getweeklychartlist', 'user': LAST_FM_USER_NAME,
			 'api_key': LAST_FM_KEY, 'format': 'JSON'}
	URL = '?'.join([ROOT_URL, urllib.urlencode(query)])
	data = json.load(urllib2.urlopen(URL))['weeklychartlist']['chart']

	for record in data:
		date_range = {'from':record['from'], 'to':record['to']}
		dates.append(date_range)
		
	return dates

#accepts the array of dicts with "to" and "from" values returned by getDates
def getTracks(dateRanges):
	charts = []	
	
	for date in dateRanges:
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
									'url': entry['url'],
									'playcount': entry['playcount']} 
					tracks.append(track_record)
					print 'Adding %s by %s' % (entry['name'], entry['artist']['#text'])
			except TypeError, e:
				pass
		else:
			print 'No tracks'
	
		charts.append({'week': {'from': date['from'], 'to': date['to']},
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
	
def makePlaylist(charts):
	trackKeys = []
	
	for chart in charts:
		for track in chart['tracks']:
			if track['rank'] == '1':
				print "Searching for %s" % track['name']
				trackKey = find_track(track)
				if trackKey != None:
					print "Found %s" % track['name']
					trackKeys.append(trackKey)
				
	print "\nSorting track keys...\n"
	trackKeysDeDuped = []
	
	#reverses list so that newest tracks appear at top of playlist
	for i in reversed(trackKeys):
		if i not in trackKeysDeDuped:
			trackKeysDeDuped.append(i)
			
	#convert track list into single, comma-separated string (which is required for some silly reason)
	keys_string = ', '.join(trackKeysDeDuped)
	
	print "Creating playlist...\n"
	return rdio.call('createPlaylist', {'name': sys.argv[1], 
								 'description': 'My weekly number ones from Last.fm', 
								 'tracks': keys_string})

if __name__ == '__main__':
	dateRanges = getDates()
	charts = getTracks(dateRanges)
	
	#write to csv in case you want to do anything else with the history; not strictly necessary
	f = open('history.csv', 'w')
	writer = csv.writer(f)
	for chart in charts:
		for track in chart['tracks']:
			writer.writerow([chart['week']['from'], chart['week']['to'],
							 track['name'], track['artist'], track['rank'],
							 track['playcount'], track['url']])
	f.close()
	
	print "\nFile created, now creating playlist"
	
	print "\nOpening Rdio connection...\n"
	rdio = Rdio((RDIO_CONSUMER_KEY, RDIO_CONSUMER_SECRET), (RDIO_TOKEN, RDIO_TOKEN_SECRET))
	
	print makePlaylist(charts)
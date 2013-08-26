from history_download import *

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
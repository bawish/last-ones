### My Last Ones

A Python script to make an Rdio playlist from your weekly #1 tracks in your Last.fm history

### Reason

I have seven years of history on my [Last.fm account](http://www.last.fm/user/picnicker/charts) now, and I churn through music quite quickly. I wanted an easy way to remind myself of songs I fell in love with, even if briefly. This is the solution.

### How it Works

The main function, `make_playlist()`, uses Last.fm's API to grab your history. Then it finds the top-ranked track from each week. It creates a playlist out of the results. 

The `update_playlist()` function updates your Last Ones playlist starting from the most recent track stored in history.csv.

You can see an example [here](http://www.rdio.com/people/Barrett/playlists/5782567/Last_Ones/)

### To Use It

1. Download the files, which include the [rdio-simple library](https://github.com/rdio/rdio-simple/tree/master/python).
2. In the same directory, create a credentials.py file with the following information:
	* RDIO_CONSUMER_KEY
	* RDIO_CONSUMER_SECRET
	* RDIO_TOKEN
	* RDIO_TOKEN_SECRET
	* LAST_ONES_PLAYLIST_KEY (add this once you've run `make_playlist()` once)
	* LAST_FM_KEY
	* LAST_FM_USER_NAME
3. Run the `make_playlist()` function once to create the playlist using your entire Last.fm history, from start to present.
4. Create a cron job to run the updater.py file on occasion. The updater file runs the `update_playlist()` function, which adds tracks starting from the most recent week stored in history.csv.
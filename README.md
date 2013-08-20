### My Last Ones

A Python script to make an Rdio playlist from your weekly #1 tracks in your Last.fm history

### Reason

I have seven years of history on my Last.fm account now, and I churn through music quite quickly. I wanted an easy way to remind myself of songs I fell in love with, even if briefly. This is the solution.

### How it Works

The script uses Last.fm's API to grab your history. Then it finds the most-listened-to track from each week. It creates a playlist out of the results. Pretty simple!

You can see an example [here](http://www.rdio.com/people/Barrett/playlists/2071446/My_Number_Ones/)

### To Use It

1. Download the files.
2. In the same folder, create a credentials.py file with the following information:
** RDIO_CONSUMER_KEY
** RDIO_CONSUMER_SECRET
** RDIO_TOKEN
** RDIO_TOKEN_SECRET
** LAST_FM_KEY
** LAST_FM_USER_NAME
3. Run the history_download.py script from the command line with an additional argument that names the playlist.
** E.g. "python history_download.py 'This is My Playlist Name'"
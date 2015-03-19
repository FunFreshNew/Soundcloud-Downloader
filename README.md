#Soundcloud Downloader

Download any track or playlist off of Soundcloud. Automatically adds ID3 tags to mp3 files including song title, artist, album, album artwork, genre, track number, and date released.  

##Usage

```shell
python scdownload.py [-h] [-o OUTPUT] url
```

arguments:  
  
url    The url of the soundcloud track or playlist.  
  
optional arguments:  
	-h, --help                  show this help message and exit.  
  	-o OUTPUT, --output OUTPUT  The name of the file (or folder if a playlist) to output to.  
  
  
URLs entered must be a URL of a playlist or a single song.  
  

##Dependencies

* python 2.7 or higher
* python-requests v2.6  
* eyed3 (ID3 tag editor for python)


##TODO

* Download an entire user's library  
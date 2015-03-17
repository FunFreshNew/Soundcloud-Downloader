#Soundcloud Downloader

Download any track or playlist off of Soundcloud.

##Usage

```shell
python scdownload.py [-h] [-o OUTPUT] [-s] url
```

arguments:  
  
url    The url of the soundcloud track or playlist.  
  
optional arguments:  
	-h, --help                  show this help message and exit.  
  	-o OUTPUT, --output OUTPUT  The name of the file (or folder if a playlist) to output to.  
  	-p, --playlist              Specifies that the URL entered is a Soundcloud playlist.  
  
  
  
URLs entered must be a URL of a playlist or a single song.  
  

##Dependencies

* python 2.7 or higher
* python-requests v2.6


##TODO

* Add ID3 tags to downloaded mp3s
* Download an entire user's library 
'''

scdownload.py
Ryan Wise
March 17, 2015

Locates and downloads mp3s off of soundcloud given a valid Soundcloud URL.

Dependencies:
python-requests v2.6
eyed3

'''


import requests
import sys
import json
import os
import argparse
import eyed3
from eyed3.id3.tag import Tag, ImagesAccessor
from eyed3.id3.frames import ImageFrame


TEMP_ARTWORK_FILE = 'artwork.jpg.tmp'


def scrape_json(raw_data):
	json_start_token = '<script>webpackJsonp([],{0:function(e,t,a){var c,n,i='
	ind = raw_data.find(json_start_token)

	if ind == -1:
		print 'Invalid URL!'
		sys.exit(0)

	raw_json = raw_data[ind + len(json_start_token):]
	raw_json = raw_json[:raw_json.find(',r=Date.now();')]

	j = None
	try:
		j = json.loads(raw_json)
	except:
		print 'Error locating raw mp3, check to make sure the URL entered is correct.'
		sys.exit(0)

	return j


def get_artwork(url):
	if os.path.exists(TEMP_ARTWORK_FILE):
		return

	response = requests.get(url, stream=True)

	with open(TEMP_ARTWORK_FILE, 'wb') as f:
		for chunk in response.iter_content(4096):
			f.write(chunk)

		f.close()


def set_id3_tag(track_data, output):
	mp3file = eyed3.load(output)
	mp3file.initTag(eyed3.id3.ID3_V2_3)

	mp3file.tag.artist = track_data['track_artist']
	mp3file.tag.title = track_data['track_title']

	if 'playlist_title' in track_data:
		mp3file.tag.album = track_data['playlist_title']

	mp3file.tag.genre = track_data['genre']
	mp3file.tag.release_date = track_data['release_date']
	mp3file.tag.original_release_date = track_data['release_date']

	if 'track_number' in track_data:
		mp3file.tag._setTrackNum(track_data['track_number'])

	get_artwork(track_data['artwork_url'])
	artwork_data = open(TEMP_ARTWORK_FILE, 'rb').read()
	mp3file.tag.images.set(ImageFrame.FRONT_COVER, artwork_data, 'image/jpeg')

	mp3file.tag.save()


def get_track_metadata(json_data):
	metadata = dict()

	metadata['track_id'] = json_data['id']
	metadata['track_title'] = json_data['title']
	metadata['track_artist'] = json_data['user']['username']

	if 'playlist_title' in json_data:
			metadata['playlist_title'] = json_data['playlist_title']

	metadata['genre'] = json_data['genre']

	date = json_data['created_at'].split('/')
	metadata['release_date'] = '%s-%s-%s' % (date[0], date[1], date[2][:2])
	metadata['artwork_url'] = json_data['artwork_url'].replace('large', 't500x500')
	metadata['artwork_url'] = metadata['artwork_url'].replace('https', 'http')  # Getting a weird SSL error downloading artwork with requests

	return metadata


def get_playlist_metadata(json_data):
	metadata = dict()

	metadata['track_count'] = json_data['track_count']
	metadata['playlist_title'] = json_data['title']
	metadata['tracks'] = list()

	for i in range(metadata['track_count']):
		json_data['tracks'][i]['playlist_title'] = metadata['playlist_title']
		metadata['tracks'].append(get_track_metadata(json_data['tracks'][i]))
		metadata['tracks'][i]['track_number'] = i + 1

	return metadata


def download(track_data, output=None):
	response = requests.get('https://api.soundcloud.com/i1/tracks/%s/streams?client_id=b45b1aa10f1ac2941910a7f0d10f8e28&app_version=88e6fe6' % track_data['track_id'])
	response = json.loads(response.text.encode('ascii'))

	url = response['http_mp3_128_url']
	url.replace('\u0026', '&')

	r = requests.get(url, stream=True)
	content_length = r.headers['content-length']
	progress = 0

	if not output:
		output = '%s - %s.mp3' % (track_data['track_artist'], track_data['track_title'])

	with open(output, 'wb') as f:
		for chunk in r.iter_content(4096):
			f.write(chunk)
			progress += 4096
			percent = (progress / float(content_length)) * 100
			sys.stdout.write('\rDownloading %s by %s: %d%%' % (track_data['track_title'], track_data['track_artist'], percent))
			sys.stdout.flush()

		f.close()

	sys.stdout.write('\n')
	sys.stdout.flush()

	#null_fds = [os.open(os.devnull, os.O_RDWR) for x in xrange(2)]  # Don't want to print eyed3 warnings
	#save = os.dup(2)
	#os.dup2(null_fds[1], 2)

	set_id3_tag(track_data, output)

	#os.dup2(save, 2)
	#os.close(null_fds[0])
	#os.close(null_fds[1])


def download_track(url, json_data, output=None):
	metadata = get_track_metadata(json_data)

	if '?in=' in url: # Track is part of a playlist, we want to get that playlist name for the id3 tag
		playlist_url = 'https://soundcloud.com/' + url[url.find('?in=') + 4:]
		response = requests.get(playlist_url)
		json_data = scrape_json(response.text)
		metadata['playlist_title'] = json_data['84'][0]['title']

	download(metadata, output)


def download_playlist(json_data, output=None):
	if output and output[len(output) - 1] != '/':
		output += '/'

	metadata = get_playlist_metadata(json_data)

	if not output:
		output = metadata['playlist_title'] + '/'

	print 'Found %s tracks for %s!' % (metadata['track_count'], metadata['playlist_title'])

	try:
		os.mkdir(output)
	except OSError, err:
		if err.errno == 17:
			print 'The folder %s already exists! Exiting...' % output
			sys.exit(0)

	for i in range(metadata['track_count']):
		out = output + '%s - %s.mp3' % (metadata['tracks'][i]['track_artist'], metadata['tracks'][i]['track_title'])
		download(metadata['tracks'][i], out)


def init_download(url, output=None):
	response = requests.get(url)
	raw_text = response.text

	json_data = scrape_json(raw_text)

	try:
		json_data = json_data['84'][0]
	except KeyError:
		print 'Invalid URL! URLs must be of a soundcloud track or playlist.'
		sys.exit(0)

	if 'track_count' in json_data:
		print 'Found a soundcloud playlist, downloading the entire playlist...'
		download_playlist(json_data, output)
	else:
		print 'Found a single track, downloading...'
		download_track(url, json_data, output)


if __name__=='__main__':
	parser = argparse.ArgumentParser(prog='python scdownload.py', description='Download any track or playlist off of soundcloud.')
	parser.add_argument('url', help='The url of the soundcloud track or playlist.')
	parser.add_argument('-o', '--output', help='The name of the file (or folder if a playlist) to output to')

	args = parser.parse_args()
	init_download(args.url, args.output)

	if os.path.exists(TEMP_ARTWORK_FILE):
		os.remove(TEMP_ARTWORK_FILE)
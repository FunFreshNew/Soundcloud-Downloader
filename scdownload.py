'''

scdownload.py
Ryan Wise
March 17, 2015

Locates and downloads mp3s off of soundcloud given a valid Soundcloud URL.

Dependencies:
python-requests v2.6

'''


import requests
import sys
import json
import os
import argparse


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


def get_track_metadata(json_data):
	metadata = dict()

	track_id = json_data['uri']
	metadata['track_id'] = track_id[track_id.find('/tracks/') + len('/tracks/'):]
	metadata['track_title'] = json_data['title']
	metadata['track_artist'] = json_data['user']['username']

	return metadata


def get_playlist_metadata(json_data):
	metadata = dict()

	try:
		metadata['track_count'] = int(json_data['track_count'])
	except KeyError:
		print 'URL entered is not of a playlist! Attempting to download as a single track...'
		data = get_track_metadata(json_data)
		download(data)
		sys.exit(0)

	metadata['playlist_title'] = json_data['title']
	metadata['tracks'] = list()

	for i in range(metadata['track_count']):
		metadata['tracks'].append(get_track_metadata(json_data['tracks'][i]))

	return metadata


def download(track_data, output=None):
	response = requests.get('https://api.soundcloud.com/i1/tracks/%s/streams?client_id=b45b1aa10f1ac2941910a7f0d10f8e28&app_version=88e6fe6' % track_data['track_id'])
	
	try:
		response = json.loads(response.text.encode('ascii'))
	except ValueError:
		print 'Error downloading track! If you have entered a URL of a playlist, you must specify the -s flag.'
		sys.exit(0)

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


def download_track(url, output=None):
	print 'Locating raw mp3...'

	response = requests.get(url)
	raw_text = response.text

	json_data = scrape_json(raw_text)

	try:
		json_data = json_data['84'][0]
	except KeyError:
		print 'Invalid URL! URLs must be a soundcloud track\'s main page'
		sys.exit(0)

	metadata = get_track_metadata(json_data)
	download(metadata, output)


def download_playlist(url, output=None):
	if output and output[len(output) - 1] != '/':
		output += '/'

	print 'Locating all mp3s in playlist...'

	response = requests.get(url)
	raw_text = response.text.encode('utf-8')

	json_data = scrape_json(raw_text)

	try:
		json_data = json_data['84'][0]
	except KeyError:
		print 'Invalid URL! URLs must be a soundcloud playlist\'s main page'
		sys.exit(0)

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


if __name__=='__main__':
	parser = argparse.ArgumentParser(prog='python scdownload.py', description='Download any track or playlist off of soundcloud.')
	parser.add_argument('url', help='The url of the soundcloud track or playlist.')
	parser.add_argument('-o', '--output', help='The name of the file (or folder if a playlist) to output to')
	parser.add_argument('-p', '--playlist', action='store_true', help='Specifies that the URL entered is a Soundcould playlist.')

	args = parser.parse_args()
	
	if args.playlist:
		download_playlist(args.url, args.output)
	else:
		download_track(args.url, args.output)
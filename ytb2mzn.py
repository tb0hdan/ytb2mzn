#!/usr/bin/env python
#-*- coding: utf-8 -*-
""" YTB2MZN """

import re
import sys

from apiclient.discovery import build  # pylint:disable=import-error
from apiclient.errors import HttpError  # pylint:disable=import-error
from mutagen.easyid3 import EasyID3
from oauth2client.client import GoogleCredentials
from youtube_dl import YoutubeDL

class Ytb2MZN(object):

    @classmethod
    def youtube(cls):
        credentials = GoogleCredentials.from_stream('./credentials.json')
        return build('youtube', 'v3', credentials=credentials)

    @classmethod
    def search(cls, query, max_results=25):
        """
        Run youtube search
        """
        youtube = cls.youtube()
        search_response = youtube.search().list(q=query,
                                                part="id,snippet",
                                                maxResults=max_results).execute()

        videos = []
        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                vname = search_result["snippet"]["title"]
                vid = search_result["id"]["videoId"]
                snippet = search_result['snippet']
                videos.append([vname, vid])
        return videos

    @classmethod
    def download_hook(cls, response):
        """
        YDL download hook
        """
        if response['status'] == 'finished':
            cls.target_filename = response['filename']

    @classmethod
    def download(cls, title, video_id):
        """
        Run youtube download
        """
        verbose = False
        template = '{0!s}.%(ext)s'.format(title)
        ydl_opts = {'keepvideo': False, 'verbose': verbose, 'format': 'bestaudio/best',
                    'quiet': not verbose, 'outtmpl': template,
                    'postprocessors': [{'preferredcodec': 'mp3', 'preferredquality': '0',
                                        'nopostoverwrites': True, 'key': 'FFmpegExtractAudio'}],
                    'progress_hooks': [cls.download_hook]}

        url = 'https://youtu.be/{0!s}'.format(video_id)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            audio_file = re.sub('\.[^\.]+$', '.mp3', cls.target_filename)
        return audio_file

    @classmethod
    def write_metadata(cls, fname, title):
        audio = EasyID3(fname)
        artist = title.split(' - ')[0]
        track = title.split(' - ')[1]
        audio['artist'] = artist
        audio['title'] = track
        audio['genre'] = 'electronic'
        audio.save()

    @classmethod
    def search_and_download(cls, query):
        results = cls.search(query)
        if results:
            fname = cls.download(results[0][0], results[0][1])
            if fname:
                cls.write_metadata(fname, results[0][0])

    @classmethod
    def run(cls):
        if len(sys.argv) > 1:
            title = ' '.join(sys.argv[1:])
            cls.search_and_download(title)

if __name__ == '__main__':
    Ytb2MZN.run()

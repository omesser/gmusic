#!/usr/local/bin/python

from gmusicapi import Mobileclient, Webclient
from os import path
from time import localtime, asctime
import pyglet



MY_GMAIL_ADDRESS = "<MY_GMAIL_ADDRESS>"
MY_PASSWORD = "<MY_PASSWORD>"


class GMusic(object):
    def __init__(self):
        self.mob_client = Mobileclient()
        self.web_client = Webclient()
        self.logfile = None
        self.logfile_open = False
        # logged_in is True if login was successful
        logged_in = self.mob_client.login(MY_GMAIL_ADDRESS, MY_PASSWORD, Mobileclient.FROM_MAC_ADDRESS)
        if logged_in:
            print("GoogleMusic MobileClient Logged In")
        else:
            raise Exception("Couldn't log in, exiting...")
        logged_in = self.web_client.login(MY_GMAIL_ADDRESS, MY_PASSWORD)
        if logged_in:
            print("GoogleMusic WebClient Logged In")
        else:
            raise Exception("Couldn't log in, exiting...")

    def build_play_list_dummy(self):
        library = self.mob_client.get_all_songs()
        tracks = [track for track in library if track['artist'] == 'Adhesive Wombat'
                  and "night shade" in track['title'].lower()]
        # for track in sweet_tracks:
        #     print(track)

        playlist_id = self.mob_client.create_playlist('Test playlist')
        for track in tracks:
            self.mob_client.add_songs_to_playlist(playlist_id, track['id'])

        return playlist_id

    def _setlogfile(self, logfile):
        if self.logfile_open:
            self._print_and_log("logfile {} already opened! Not opening again!")
        else:
            self.logfile = logfile
            with open(self.logfile, "w") as logfile:
                logfile.write("LOGSTART: {}, script: {}\n".format(asctime(localtime()), __file__))
            self.logfile_open = True

    def _print_and_log(self, msg):
        if self.logfile:
            with open(self.logfile, "a") as logfile:
                logfile.write(msg+"\n")
        print msg

    def find_duplicate_songs(self, outfile=None):
        duplicates = []
        if outfile:
            if path.exists(path.dirname(outfile)):
                self._setlogfile(outfile)
            else:
                raise IOError("Output filename given: {} is in an none-existing dir".format(outfile))

        library = self.mob_client.get_all_songs()
        tracks = [track for track in library]
        while tracks:
            track = tracks[0]
            dup_list = []
            dup_idx_list = []
            for idx, track_i in enumerate(tracks):
                if track['artist'].lower() == track_i['artist'].lower() and\
                   track['album'].lower() == track_i['album'].lower() and\
                    track['discNumber'] == track_i['discNumber'] and\
                    track['trackNumber'] == track_i['trackNumber'] and\
                   track['title'].lower() == track_i['title'].lower():
                    dup_idx_list.append(idx)
                    dup_list.append(track_i)
            # Remove them:
            for index in sorted(dup_idx_list, reverse=True):
                del tracks[index]
            if len(dup_list) > 1:
                duplicates.append(dup_list)
        for idx, dup_list in enumerate(duplicates):
            self._print_and_log("{}: '{}' was found {} times!".format(idx+1, dup_list[0]['title'].encode("utf-8"),
                                                                      len(dup_list)))
        self._print_and_log("Found a total of {} duplicate songs!".format(len(duplicates)))
        # Display important stuff
        for idx, track_list in enumerate(duplicates):
            self._print_and_log("{}: BAND: {}, NAME:  '{}'".format(idx+1, track_list[0]['artist'],
                                                                   track_list[0]['title'].encode("utf-8")))
            for el in track_list[0]:
                for track in track_list:
                    if el not in track:
                        track[el] = "NO VALUE"
                    if track[el] != track_list[0][el] and el not in ['id', 'url', 'recentTimestamp', 'storeId', 'nid', 'clientId']:
                        # unicode?
                        try:
                            r_val = track_list[0][el].encode("utf-8")
                        except:
                            r_val = track_list[0][el]
                        # unicode?
                        try:
                            l_val = track[el].encode("utf-8")
                        except:
                            l_val = track[el]

                        self._print_and_log("track_id {}: {}='{}'".format(track_list[0]['id'], el, r_val))
                        self._print_and_log("track_id {}: {}='{}'".format(track['id'], el, l_val))

            # raw_input("Press any key to continue...")
        return duplicates

    def delete_duplicates(self, duplicates):
        self._print_and_log("Cleaning duplicates [removing oldest of each duplicant]:")
        old_song_ids = []
        for idx, dup_list in enumerate(duplicates):
            self._print_and_log("{}: BAND: {}, NAME:  '{}'".format(idx+1, dup_list[0]['artist'],
                                                                   dup_list[0]['title'].encode("utf-8")))
            track_timstamp = None
            oldest_id = None
            for el in dup_list:
                if track_timstamp is None and oldest_id is None:
                    track_timstamp = el["timestamp"]
                    oldest_id = el["id"]
                elif el["timestamp"] < track_timstamp:
                    track_timstamp = el["timestamp"]
                    oldest_id = el["id"]
            # finished with dup_list - log oldest id:
            self._print_and_log("Will delete {}, track_id: {}".format(el["title"], el["id"]))
            old_song_ids.append(oldest_id)

        self.mob_client.delete_songs(old_song_ids)
        self._print_and_log("track_ids deleted:\n{}".format(old_song_ids))


class MusicPlay(object):
    def __init__(self):
        pass

    def play(self, mp3file=None):
        music = pyglet.resource.media('music.mp3')
        music.play()
        pyglet.app.run()

if __name__ == "__main__":
    dup_dump = "C:/Dropbox/google_music_duplicates.txt"
    player = MusicPlay()
    gm = GMusic()
    duplicates = gm.find_duplicate_songs(outfile=dup_dump)
    if raw_input("Delete duplicate songs(delete oldest) ? [y/n]: ") is 'y':
        gm.delete_duplicates(duplicates)
    gm.web_client.logout()
    # with open(dup_dump) as fh:
    #     fh.writelines(duplicates)
    # play_list = gm.build_play_list()
    # play_list_urls = []
    # for track_id in play_list:
    #     play_list_urls.append(gm.web_client.get_stream_audio(track_id))
    # player.play(play_list_urls[0])
    gm._print_and_log("Done... exiting")
import os
from pathlib import Path
from pytube import YouTube

class SoundManager():
    """Manages saving/loading of user sounds."""

    _instance = None

    def __init__(self):
        self.CONFIG_DIR = './config'
        self.CONFIG_PATH = os.path.join(self.CONFIG_DIR, 'config.csv')
        self.SOUND_DIR = './sound'

        #Check if config file and folder exists.
        if (not os.path.exists(self.CONFIG_DIR)):
            os.mkdir(self.CONFIG_DIR)
            file = open(self.CONFIG_PATH, 'w')
            file.close()

        #Check if sound folder exists
        if (not os.path.isdir(self.SOUND_DIR)):
            os.mkdir(self.SOUND_DIR)

        self.active_members = {}    #Key: MemberID, Value: PathToSound
        self.active_ids = []        #Active MemberIDs
        
    def add_member(self, member_id, member_sound_path, from_dbs = False):
        self.active_ids.append(member_id)
        if ("youtube" in member_sound_path):
            #Convert YT link to mp3
            path = self.download_from_youtube(member_sound_path)
            #Create new user and append him to active members
            self.add_member_sound(member_id, os.path.join(self.SOUND_DIR, path))
        elif (from_dbs):
            self.add_member_sound(member_id, member_sound_path)

    def add_member_sound(self, member_id, member_sound):
        self.active_members[member_id] = member_sound
        self.active_ids.append(member_id)
        self.save_members_csv()
            
    def get_member_sound(self, member_id):
        if (self.is_member_active(member_id)):
            return self.active_members[member_id]
        return None

    def is_member_active(self, member_id):
        if member_id in self.active_ids:
            return True
        return False

    def save_members_csv(self):
        file = open(self.CONFIG_PATH, 'w')
        for key, value in self.active_members.items():
            file.write('{};{}\n'.format(key, value))
        file.close()

    def load_members_csv(self):
        file = open(self.CONFIG_PATH, 'r')
        for line in file.readlines():
            line_split = line.split(';')
            self.add_member(int(line_split[0]), line_split[1].split('\n')[0], True)
        file.close()

    def download_from_youtube(self, link):
        yt = YouTube(link)
        stream = yt.streams.filter(only_audio = True, abr = '128kbps')
        stream[0].download(output_path = self.SOUND_DIR)
        filename = stream[0].default_filename
        
        print('[MUSIC DOWNLOAD] Path: {}'.format(filename))

        return filename

    def get_singleton():
        if (SoundManager._instance is None):
            print('[DEBUG] Creating new instance of SoundManager')
            SoundManager._instance = SoundManager()
            return SoundManager._instance
        print('[DEBUG] Returning an existing instance of SoundManager')
        return SoundManager._instance
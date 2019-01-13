import argparse
import codecs
import os
import re
import sys
from shutil import copyfile
from winreg import HKEY_LOCAL_MACHINE, OpenKey, EnumKey, QueryValueEx, KEY_READ
from mutagen.id3 import ID3NoHeaderError
from mutagen.id3 import ID3, TPE1, TIT2


VERSION = '0.4'


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def subkeys(key):
    i = 0
    while True:
        try:
            subkey = EnumKey(key, i)
            yield subkey
            i += 1
        except WindowsError:
            break


def find_osu_in_registry():
    key_path = r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    
    key = OpenKey(HKEY_LOCAL_MACHINE, key_path)

    app_path = ''

    for subkey in subkeys(key):
        path = key_path + "\\" + subkey
        key = OpenKey(HKEY_LOCAL_MACHINE, path, 0, KEY_READ) 

        try:
            app_name = QueryValueEx(key, 'DisplayName')[0]
        except WindowsError:
            continue

        if app_name == 'osu!':
            app_path = QueryValueEx(key, 'DisplayIcon')[0]
            app_path = app_path[:len(app_path)-8] + "songs" 
            break

    return app_path


def main():
    parser = argparse.ArgumentParser(description='Osu! songs retriever v%s' % VERSION)
    parser.add_argument('-i', '-in', nargs='?', dest='in_dir', help='Osu! songs directory')
    parser.add_argument('-o', '-out', nargs='?', dest='out_dir', default='out', help='Output directory to store songs')
    parser.add_argument('-rr', '-override', dest='override', action="store_true", help='Override existing songs in output directory')

    args = parser.parse_args()

    # if len(sys.argv) < 2:
    #     print("Please enter the path to songs dir")
    #     exit(0)

    # path = sys.argv[1]

    if not args.in_dir:
        path = find_osu_in_registry() 
    else:
        path = args.in_dir

    if not path:
        print('Installed osu! not found on your computer. Please specify osu! songs dir as -in parameter')
        exit(0)

    print(path)

    if not os.path.isdir(args.out_dir):
        if (query_yes_no('Output directory not exist. Create new one?')):
            os.mkdir(args.out_dir)
        else:
            print('Specify valid output directory as -out parameter (default: \'out\')')
            exit(0)

    dirs = os.listdir(path)

    if args.override:
        tracks = set([])
    else:    
        tracks = set(os.listdir(args.out_dir))

    imported_count = 0

    for dir in dirs:
        print('-'*40)
        print(dir)

        song_path = path + '\\' + dir
        files = os.listdir(song_path)

        for file in files:
            if len(file) < 4 or file[-4:] != '.osu':
                continue

            # print('\t%s' % file)
            file_path = song_path + '\\' + file
            osu_file = codecs.open(file_path, 'r', 'utf-8')
            # osu_file = open(file_path)
            osu = osu_file.read().replace('\r', '\n')
            osu_file.close()

            title_unicode = re.findall(r'TitleUnicode:(.+)\n+', osu)
            artist_unicode = re.findall(r'ArtistUnicode:(.+)\n+', osu)

            title = title_unicode[0] if title_unicode else re.findall(r'Title:(.+)\n+', osu)[0]
            artist = artist_unicode[0] if artist_unicode else re.findall(r'Artist:(.+)\n+', osu)[0]
            track_name = re.findall(r'AudioFilename: (.+)\n+', osu)[0]#.replace('\r', '')

            title = title.strip()
            artist = artist.strip()

            new_track_name = ('%s — %s.mp3' % (artist, title))\
                .replace('/', '_')\
                .replace('\\', '_')\
                .replace('?', '_')\
                .replace('|', '_')\
                .replace('*', '_')\
                .replace('<', '_')\
                .replace('>', '_')\
                .replace(':', '_')\
                .replace('"', '_')
            if new_track_name in tracks:
                continue

            track_path = song_path + '\\' + track_name
            new_track_path = args.out_dir + '\\' + new_track_name
            copyfile(track_path, new_track_path)
            tracks.add(new_track_name)

            print('\t' + new_track_name)

            try: 
                tags = ID3(new_track_path)
            except ID3NoHeaderError:
                print('\t' + 'Adding ID3 header')
                tags = ID3()

            if not "TIT2" in tags:
                tags["TIT2"] = TIT2(encoding=3, text=title)
            if not "TPE1" in tags:
                tags["TPE1"] = TPE1(encoding=3, text=artist)

            tags.save(new_track_path)

            imported_count = imported_count + 1

    print('\n Imported %i tracks in %s' % (imported_count, os.path.abspath(args.out_dir)))


if __name__ == '__main__':
    main()

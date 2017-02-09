import telepot, pylast, os, random, csv
import numpy as np
from pprint import pprint
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

# Load Pokedex
pd_national_dex = {}
pd_names = {}
initial = True

with open ('pokedex.csv', 'r') as f:
    for line in csv.reader(f):
        # skip header line
        if initial:
            initial = False
            continue

        pd_national_dex[line[1]] = line[3]
        pd_names[line[2].lower()] = line[3]

# API keys, etc.
bot = telepot.Bot(os.environ.get('TELEGRAM_API_TOKEN'))
LASTFM_API_KEY = os.environ.get('LASTFM_API_KEY')
LASTFM_API_SECRET = os.environ.get('LASTFM_API_SECRET')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

network = pylast.LastFMNetwork(api_key=LASTFM_API_KEY, api_secret=LASTFM_API_SECRET)
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=GOOGLE_API_KEY)

if os.path.exists('lastfm_handles.npy'):
    lastfm_handles = np.load('lastfm_handles.npy').item()
else:
    lastfm_handles = {}

def handle(msg):
    import numpy as np
    pprint(msg)

    if msg['text'].startswith('/pokedex'):
        try:
            query = msg['text'].split()[1].strip()
        except IndexError:
            to_send = 'You must specify a query.'
        else:
            try:
                national_dex = int(query)
                name = None
            except ValueError:
                national_dex = None
                name = query.lower()

            try:
                if national_dex is not None:
                    to_send = pd_national_dex[str(national_dex)]
                else:
                    to_send = pd_names[name]
            except KeyError:
                to_send = 'Couldn\'t find ' + query + '.'

        # Send the response
        bot.sendMessage(msg['chat']['id'], to_send)
        print('>>>' + to_send)

    if msg['text'].startswith('/toss'):
        if random.randint(1, 2) == 1:
            to_send = 'Heads.'
        else:
            to_send = 'Tails.'

        # Send the response
        bot.sendMessage(msg['chat']['id'], to_send)
        print('>>>' + to_send)

    if msg['text'].startswith('/roll'):
        to_send = 'Rolled a %d.' % random.randint(1, 6)

        # Send the response
        bot.sendMessage(msg['chat']['id'], to_send)
        print('>>>' + to_send)

    if msg['text'].startswith('/eval'):
        try:
            msg['text'].split()[1]
            query = ' '.join(msg['text'].split()[1:])
            to_send = query.strip() + ' = ' + str(eval(query, {}, {}))
        except IndexError:
            to_send = 'You must specify a query.'
        except:
            to_send = 'Invalid expression.'

        # Send the response
        bot.sendMessage(msg['chat']['id'], to_send)
        print('>>>' + to_send)

    if msg['text'].startswith('/youtube'):
        try:
            msg['text'].split()[1]
            query = ' '.join(msg['text'].split()[1:])
            search_response = youtube.search().list(q=query, type="video", part="id,snippet", maxResults=1).execute()

            for search_result in search_response.get("items", []):
                pprint(search_result)
                to_send = "%s\nhttps://youtube.com/watch?v=%s" % (search_result["snippet"]["title"], search_result["id"]["videoId"])
        except IndexError:
            to_send = 'You must specify a query.'

        # Send the response
        bot.sendMessage(msg['chat']['id'], to_send)
        print('>>>' + to_send)

    if msg['text'].startswith('/register_lastfm'):
        # Get handle
        try:
            username = msg['text'].split()[1]
            user = network.get_user(username)
        except IndexError:
            to_send = 'You must specify your last.fm username.'
        except pylast.WSError:
            to_send = 'User ' + username + ' does not exist.'
        else:
            lastfm_handles[msg['from']['username']] = username
            np.save('lastfm_handles.npy', lastfm_handles)
            to_send = 'Successfully registered ' + msg['from']['username'] + ' as ' + username + '.'

        # Send the response
        bot.sendMessage(msg['chat']['id'], to_send)
        print('>>>' + to_send)

    if msg['text'].startswith('/np'):
        # Get handle
        try:
            username = msg['text'].split()[1]

            if username.startswith('@') and username.lstrip('@') in lastfm_handles:
                username = lastfm_handles[username.lstrip('@')]
        except IndexError:
            if msg['from']['username'] in lastfm_handles:
                username = lastfm_handles[msg['from']['username']]
            else:
                username = msg['from']['username']

        # Do a lookup
        try:
            user = network.get_user(username)
            np = user.get_now_playing()

            if np is not None:
                to_send = username + ' is listening to: ' + np.get_name() + ' by ' + np.get_artist().get_name() + '.'
            else:
                lp = user.get_recent_tracks(limit=1)
                to_send = username + ' is not scrobbling right now.'
                if len(lp) != 0:
                    lp = lp[0].track
                    to_send += '\nLast played: ' + lp.get_name() + ' by ' + lp.get_artist().get_name() + '.'

        except pylast.WSError:
            to_send = 'User ' + username + ' does not exist.'

        # Send the response
        bot.sendMessage(msg['chat']['id'], to_send)
        print('>>>' + to_send)

bot.message_loop(handle, run_forever='Listening...')

import telepot, pylast, os
import numpy as np
from pprint import pprint
bot = telepot.Bot(os.environ.get('TELEGRAM_API_TOKEN'))

API_KEY = os.environ.get('LASTFM_API_KEY')
API_SECRET = os.environ.get('LASTFM_API_SECRET')

network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

if os.path.exists('lastfm_handles.npy'):
    lastfm_handles = np.load('lastfm_handles.npy').item()
else:
    lastfm_handles = {}

def handle(msg):
    import numpy as np
    pprint(msg)

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

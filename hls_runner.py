import json
import m3u8
from   multiprocessing import Process, Manager, Lock
import pdb
import requests
from   requests.packages.urllib3.exceptions import InsecureRequestWarning
from   requests.packages.urllib3.exceptions import InsecurePlatformWarning
import time
from   urlparse import urlparse


def average_list(list_items, shift=1):
  # Return average from list (normalised by shift to convert units)
  try:
    return float(sum(list_items))/float(len(list_items))/float(shift)
  except ZeroDivisionError as e:
    return None

def min_max_list(list_items, shift=1):
  # Return list minimum and maximum (normalised by shift to convert units)
  try:
    return min(list_items)/float(shift), max(list_items)/float(shift)
  except ValueError as e:
    return None, None

def calculated_response_times(durations):
  # Compile response times into Average, Min, and Max durations
  return {
            'Average': average_list(durations, 1000000),
            'Min': min_max_list(durations, 1000000)[0],
            'Max': min_max_list(durations, 1000000)[1]
          }

def construct_url(playlist_url, segment):
  # Segments point to absolute URL 
  if segment.startswith('http'):
    return segment
  # Segments point to relative URL, which need added path context
  else:
    if segment.startswith('./') and len(segment) > 2:
      segment = segment[2:]
      return playlist_url.rsplit('/', 1)[0] + ('/' + segment).replace('//', '/')
    elif segment.startswith('/'):
      return urlparse(playlist_url).scheme + '://' + (urlparse(playlist_url).netloc + segment).replace('//', '/')
    else:
      return playlist_url.rsplit('/', 1)[0] + '/' + segment


def get_playlist_details(m3u8_url, timeout, success):
  # Get playlist and extract m3u8 data
  try:
    r = requests.get(m3u8_url, verify=False, allow_redirects=True, timeout=(timeout['connect'], timeout['read']))

    if not r.status_code in [200, 201, 302, 307]:
      try: success[False] += 1
      except: success[False] = 1
      return
    else:
      try:
        playlist = m3u8.loads(r.text)
        try: success[True] += 1
        except: success[True] = 1
        return playlist
      except:
        try: success[False] += 1
        except: success[False] = 1
        return
  except:
    try: success[False] += 1
    except: success[False] = 1

def get_segment(url, status, results, duration, timeout, lock):
  # Get HLS Segment and tally status codes and errors
  try:
    r = requests.get(url=url, verify=False, allow_redirects=True, timeout=(timeout['connect'], timeout['read']))

    duration.append(r.elapsed.microseconds)

    lock.acquire()
    try: status[r.status_code] += 1
    except: status[r.status_code] = 1
    lock.release()

    lock.acquire()
    try: results['Valid Response'] += 1
    except: results['Valid Response'] = 1
    lock.release()
  
  except requests.exceptions.ReadTimeout as e:
    lock.acquire()
    try: results['Read Timeout'] += 1
    except: results['Read Timeout'] = 1
    lock.release()
  except requests.exceptions.ConnectTimeout as e:
    lock.acquire()
    try: results['Connect Timeout'] += 1
    except: results['Connect Timeout'] = 1
    lock.release()
  except requests.exceptions.ConnectionError as e:
    lock.acquire()
    try: results['Connection Error'] += 1
    except: results['Connection Error'] = 1
    lock.release()
  except Exception as e:
    print "Unknown Error %s" % e
    lock.acquire()
    try: results['Unknown Error'] += 1
    except: results['Unknown Error'] = 1
    lock.release()


def authenticate(authentication_url, username, password, request_type):
  # Get session cookies for URLs requiring authentication
  if request_type.lower() == 'get':
    auth_request = requests.get(authentication_url, auth=(username, password))
  elif request_type.lower() == 'post':
    payload = {'username': username, 'password': password}
    auth_request = requests.post(authentication_url, data=payload)
  
  return auth_request.cookies


def get_playlist(m3u8_url, live, loop, results, status, success, duration, playlists, timeout, cookies, lock, pid):
  # Extract HLS segments from M3U8 file for VOD or Live content

  playlist = get_playlist_details(m3u8_url, timeout, success)
  base_url = m3u8_url

  if playlist:
    loop_iterator, loop_limit = 1, 1000 
    seconds_since_new_file = 0
    no_file_timeout = 120
    segments = {}
    segments['count'] = 0
    segments['played'] = {}

    # For live content
    if live.lower() == 'true':
    
      # If playlist contains nested playlists, use the first
      if len(playlist.playlists) > 0:
        base_url = construct_url(m3u8_url, playlist.playlists[0].uri)
      
      while segments['count'] < int(loop):
        
        # In case no files are found, break loop after 1000 iterations
        loop_iterator += 1
        if loop_iterator >= loop_limit: 
          return

        # If playlists are continually requested with the same list of segments, timeout after no_file_timeout
        if seconds_since_new_file > no_file_timeout:
          return

        playlist = get_playlist_details(base_url, timeout, success)
        if not playlist:
          continue
        
        for idx, file in enumerate(playlist.files):
          
          # Break when enough segments (user set) have been requested
          if segments['count'] >= int(loop):
            return
          
          # Only request segments from [n - 3, n]
          if idx < (len(playlist.files) - 3):
            continue
          
          segment_url = construct_url(base_url, file)

          # If segement has not yet been requested (some playlists will overlap TS files if files if requested too fast)
          if not segments['played'].has_key(segment_url):
            seconds_since_new_file = 0
            
            lock.acquire()
            segments['count'] += 1
            lock.release()
            
            segments['played'][segment_url] = True
            time.sleep(timeout['sleep'])
            get_segment(segment_url, status, results, duration, timeout, lock)
        
        # Sleep before getting next playlists (in case there are no new segments, this loops too quickly)
        time.sleep(timeout['sleep'])
        seconds_since_new_file += int(timeout['sleep'])

    else: # VOD

      for loop_number in range(0, int(loop)):
    
        # If playlist contains all TS files directly
        if len(playlist.files) > 0:
          for idx, file in enumerate(playlist.files):

            time.sleep(timeout['sleep'])
            segment_url = construct_url(base_url, file)
            get_segment(segment_url, status, results, duration, timeout, lock)

        # If playlist contains nested playlists
        else:
          for sub_playlist in playlist.playlists:
            sub_playlist_url = construct_url(base_url, sub_playlist.uri)
            nested_playlist = requests.get(url=sub_playlist_url, verify=False, allow_redirects=True, timeout=(timeout['connect'], timeout['read']))
            
            for idx, file in enumerate(m3u8.loads(nested_playlist.text).files):
              time.sleep(timeout['sleep'])
              segment_url = construct_url(nested_playlist.url, file)
              get_segment(segment_url, status, results, duration, timeout, lock)

          
def get_hls_stream(m3u8_url, concurrency=1, live=True, loop=1, segment_sleep=1, authentication=None, timeouts=None):
  # Spawn concurrent subprocesses to get every HLS segment of stream

  # Disable all SSL Warnings (version dependent)
  try:
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
  except:
    pass
  
  # Configurables
  subprocesses = []
  process_id = 0
  timeout    = {'read': float(timeouts['read']), 
                'connect': float(timeouts['connect']), 
                'sleep': float(segment_sleep)}
  manager    = Manager()
  lock       = manager.Lock()
  durations  = manager.list()
  success    = manager.dict()
  results    = manager.dict()
  status     = manager.dict()
  playlists  = manager.dict()

  # Cookies for session authentication
  if authentication:
    cookies = (authentication['url'], authentication['username'], authentication['password'], authentication['type'])
  else:
    cookies = None

  # Spawn parallel subprocesses for each simulated client
  for x in range(0, int(concurrency)):
    process_id += 1
    p = Process(target=get_playlist, args=(m3u8_url, live, loop, results, status, success, durations, playlists, timeout, cookies, lock, process_id,))
    subprocesses.append(p)
    p.start()

  # Wait for all processes to complete
  for subprocess in subprocesses:
    while True:
      response_times = calculated_response_times(durations)
      yield results._getvalue(), status._getvalue(), response_times, success._getvalue()
      
      time.sleep(1)
      if not subprocess.is_alive():
        yield results._getvalue(), status._getvalue(), response_times, success._getvalue()
        break
  

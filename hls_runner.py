import m3u8
from   multiprocessing import Process, Manager, Lock
import pdb
import requests
from   requests.packages.urllib3.exceptions import InsecureRequestWarning
from   requests.packages.urllib3.exceptions import InsecurePlatformWarning
import time


def average_list(list_items, shift=1):
  try:
    return float(sum(list_items))/float(len(list_items))/float(shift)
  except ZeroDivisionError as e:
    return None

def min_max_list(list_items, shift=1):
  try:
    return min(list_items)/float(shift), max(list_items)/float(shift)
  except ValueError as e:
    return None, None


def construct_segment_url(playlist_url, segment):
  # Prepend URL segment with url origin if it is a relative path
  if segment.startswith('http'):
    return segment
  else:
    if segment.startswith('./') and len(segment) > 2:
      segment = segment[2:]
    return playlist_url.rsplit('/', 1)[0] + '/' + segment


def get_segment(url, status, results, duration, timeout, lock):
  # Get HLS Segment and tally status codes and errors
  try:
    r = requests.get(url=url, verify=False, timeout=(timeout['connect'], timeout['read']))

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
    print e
    lock.acquire()
    try: results['Unknown Error'] += 1
    except: results['Unknown Error'] = 1
    lock.release()


def get_playlist(m3u8_url, live, loop, results, status, success, duration, timeout, lock, pid):
  # Extract HLS segments from M3U8 file for VOD or Live content

  r = requests.get(m3u8_url, verify=False, timeout=(timeout['connect'], timeout['read']))

  if not r.status_code in [200, 201]:
    try: success[True] += 1
    except: success[True] = 1
  else:

    try:
      playlist = m3u8.loads(r.text)
      try: success[True] += 1
      except: success[True] = 1
    except:
      try: success[False] += 1
      except: success[False] = 1
      return

    segment_count = 0
    loop_iterator, loop_limit = 1, 1000 
    segments = {}

    # For live content
    if live.lower() == 'true':
      while segment_count < loop and loop_iterator < loop_limit:
        
        # In case no files are found, break loop after 1000 iterations
        loop_iterator += 1
        if loop_iterator >= loop_limit: return

        # TODO: catch exceptions / empty
        r = requests.get(m3u8_url, verify=False, timeout=(timeout['connect'], timeout['read']))
        playlist = m3u8.loads(r.text) 
        
        for file in playlist.files:
          if segment_count > loop: return
          
          segment_url = construct_segment_url(r.url, file)
          
          # If segement has not yet been requested (some playlists will overlap TS files if files if requested too fast)
          if not segments.has_key(segment_url):
            segment_count += 1
            segments[segment_url] = True
            time.sleep(timeout['sleep'])
            get_segment(segment_url, status, results, duration, timeout, lock)

    else: # VOD
      for loop_number in range(0, int(loop)):
    
        # If playlist contains all TS files directly
        if len(playlist.files) > 0:
          for file in playlist.files:

            time.sleep(timeout['sleep'])
            segment_url = construct_segment_url(r.url, file)
            get_segment(segment_url, status, results, duration, timeout, lock)

        # If playlist contains nested playlists
        else:
          for sub_playlist in playlist.playlists:
           
            sub_playlist_url = construct_segment_url(r.url, sub_playlist.uri)
            r2 = requests.get(url=sub_playlist_url, verify=False, timeout=(timeout['connect'], timeout['read']))
            
            for file in m3u8.loads(r2.text).files:

              segment_count += 1 ###DEBUG
              if segment_count > 6: return ###DEBUG

              time.sleep(timeout['sleep'])
              segment_url = construct_segment_url(sub_playlist.uri, file)
              get_segment(segment_url, status, results, duration, timeout, lock)

          
def get_hls_stream(m3u8_url, concurrency=1, live=True, loop=1, segment_sleep=1):
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
  timeout    = {'read': 10, 'connect': 10, 'sleep': float(segment_sleep)}
  manager    = Manager()
  lock       = manager.Lock()
  durations  = manager.list()
  success    = manager.dict()
  results    = manager.dict()
  status     = manager.dict()

  # Spawn parallel subprocesses for each simulated client
  for x in range(0, int(concurrency)):
    process_id += 1
    p = Process(target=get_playlist, args=(m3u8_url, live, loop, results, status, success, durations, timeout, lock, process_id,))
    subprocesses.append(p)
    p.start()

  # Wait for all processes to complete
  for subprocess in subprocesses:
    subprocess.join()

  response_times = {'Average': average_list(durations, 1000000),
                    'Min': min_max_list(durations, 1000000)[0],
                    'Max': min_max_list(durations, 1000000)[1]}

  return results, status, response_times, success


import m3u8
from   multiprocessing import Process, Manager, Lock
import pdb
import requests
from   requests.packages.urllib3.exceptions import InsecureRequestWarning
from   requests.packages.urllib3.exceptions import InsecurePlatformWarning
import time


def construct_segment_url(playlist_url, segment):
  # Prepend URL segment with url origin if it is a relative path
  if segment.startswith("http"):
    return segment
  else:
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

    # For live content
    if live.lower() == 'true':
      pass
      """ TODO - request new playlist in outer loop
      for file in playlist.files:
        segment_count += 1
        if segment_count > loop: return
        
        time.sleep(timeout['sleep'])
        segment_url = construct_segment_url(r.url, file)
        get_segment(segment_url, status, results, duration, timeout, lock)
      """
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

  return results, status, sum(durations), success


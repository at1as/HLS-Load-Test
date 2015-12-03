import datetime
from   flask import Flask, request, render_template
from   hls_runner import *
import json

app =  Flask(__name__)
test_running = False

@app.route('/')
def main():
  return render_template('index.html', test_stats=False)


@app.route('/start/', methods=['POST'])
def start():

  # Stream Parameters
  url = request.form['url']
  sleep = request.form['request_sleep']
  concurrency = request.form['concurrency']
  live = request.form['live']
  loop = request.form['loop']

  # Authentication Parameters
  auth_url = request.form['auth_url']
  auth_username = request.form['auth_username']
  auth_password = request.form['auth_password']
  auth_type = request.form['auth_type']

  # Authentication Payload
  if auth_url:
    authentication = {"url": auth_url, "username": auth_username, "password": auth_password, "type": auth_type}
  else:
    authentication = None

  print "Fetching Stream: %s (sleep: %s, concurrency: %s, live: %s, loop: %s)" %(url, sleep, concurrency, live, loop)
  results, status_codes, response_times, success = get_hls_stream(url, concurrency, live, loop, sleep, authentication)

  # Write Results to file
  timestamped_file = '/tmp/hls-' + str(datetime.datetime.now()).replace(' ', '_')
  
  with open(timestamped_file, 'w') as f:
    f.write("Status Codes\n")
    for key in status_codes.keys():
      f.write("%s : %s\n" %(key, status_codes[key]))
    
    f.write("\nResponse Types\n")
    for key in results.keys():
      f.write("%s : %s\n" %(key, results[key]))

    f.write("\nResponse Times\n")
    for key in response_times.keys():
      f.write("%s : %s\n" %(key, response_times[key]))
    
    f.write("\nPlaylist Acquired Successfully?\n")
    for key in success.keys():
      f.write("%s : %s\n" %(key, success[key]))

  print "Output written to %s" % timestamped_file

  return render_template(
           'index.html', test_stats=True, 
            playlist_url=url, sleep=sleep, concurrency=concurrency, live=live, loop=loop,
            auth_url=auth_url, auth_username=auth_username, auth_password=auth_password, auth_type=auth_type,
            results=results, status_codes=status_codes, response_times=response_times, success=success,
            test_stats=True
          )


if __name__ == "__main__":
  app.run(debug=True)


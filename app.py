import datetime
from   flask import Flask, request, render_template, Response, stream_with_context
from   hls_runner import *
import json

app =  Flask(__name__)
test_running = False
request_body = {}


##### HELPERS #####

def write_report(filename, results, status_codes, response_times, success):
  # Write results to a timestamped file in the /tmp directory
  try:
    with open(filename, 'w') as f:
    
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
    return True
  except:
    return False


def authentication_url(auth_url, auth_username, auth_password, auth_type):
  if auth_url:
    return {"url": auth_url, "username": auth_username, "password": auth_password, "type": auth_type}
  else:
    return None

def set_value(value, default):
  # Return given value, or if not set, return the default
  if value:
    return value
  else:
    return default


def build_request_body(request):
  global request_body

  # Stream Parameters
  request_body['url'] = request.json['url']
  request_body['sleep'] = set_value(request.json['request_sleep'], 2)
  request_body['concurrency'] = set_value(request.json['concurrency'], 1)
  request_body['live'] = set_value(request.json['live'], False)
  request_body['loop'] = set_value(request.json['loop'], 1) ## TODO: change default for Live/VOD

  # Timeouts
  read_timeout = set_value(request.json['read_timeout'], 10)
  connect_timeout = set_value(request.json['connect_timeout'], 10)
  request_body['timeouts'] = {'read': read_timeout, 'connect': connect_timeout}
  
  # Authentication Parameters
  auth_url = request.json['auth_url']
  auth_username = request.json['auth_username']
  auth_password = request.json['auth_password']
  auth_type = request.json['auth_type']

  # Authentication Payload
  request_body['authentication'] = authentication_url(auth_url, auth_username, auth_password, auth_type)


##### ROUTES #####

@app.route('/')
def main():
  return render_template('index.html', test_stats=False)


@app.route('/set/', methods=['POST'])
def set():
  build_request_body(request)
  return json.dumps({'success':True}), 200, {'ContentType':'application/json'}  


@app.route('/start/', methods=['GET'])
def start():
  def generate():
    global request_body

    # Write Results to file
    timestamped_file = '/tmp/hls-' + str(datetime.datetime.now()).replace(' ', '_')
    
    for results, status_codes, response_times, success in get_hls_stream(request_body['url'], request_body['concurrency'], request_body['live'], request_body['loop'], request_body['sleep'], request_body['authentication'], request_body['timeouts']):
      write_report(timestamped_file, results, status_codes, response_times, success)
     
      # EventSource format must be "data: <data>\n\n"
      yield 'data: ' + json.dumps({
          "request_data": request_body,
          "results": results,
          "status_codes": status_codes, 
          "response_times": response_times, 
          "success": success,
          "test_location": timestamped_file,
          "test_stats": True
        }) + '\n\n'
  
  # Stream response to client
  return Response(stream_with_context(generate()), mimetype="text/event-stream")


if __name__ == "__main__":
  app.run(debug=True, port=5000)


from flask import Flask, request, render_template
from hls_runner import *
app = Flask(__name__)


@app.route('/')
def main():
  return render_template('index.html', test_running=False)


@app.route('/start/', methods=['POST'])
def start():
  url = request.form['url']
  sleep = request.form['request_sleep']
  concurrency = request.form['concurrency']
  live = request.form['live']
  loop = request.form['loop']

  print url, sleep, concurrency, live, loop

  results, status_codes, duration, success = get_hls_stream(url, concurrency, live, loop, sleep)

  return render_template(
                         'index.html', test_running=True, 
                          playlist_url=url, sleep=sleep, concurrency=concurrency, live=live, loop=loop,
                          results=results, status_codes=status_codes, duration=duration, success=success
                          )


if __name__ == "__main__":
  app.run(debug=True)

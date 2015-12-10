# HLS Client

A configurable HLS client to simulate users requesting video segments


### Demo

Try it on [Heroku](http://hls.herokuapp.com/)

A few HLS playlists to try are listed on [Stackoverflow](http://stackoverflow.com/a/13265943)


### Usage

```bash
$ git clone https://github.com/at1as/hls_client.git
$ install dependencies in requirements.txt
$ python app.py
```

And the navigate to 0.0.0.0:5000 (or port 8000 if run with gunicorn)


### Features

* Supports Concurrency (can be used a load test utility. Spawns system subprocesses to alleviate GIL bottlenecks)
* Reports response times, status codes, and errors in real time for each requested segment
* Highly configurable (timeouts, sleeps, number of segments, etc are all configurable)


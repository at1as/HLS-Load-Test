function set_live(setting){
  if (setting.value === "True"){
    document.getElementById('loop').required = true;  
    document.getElementById('loop').placeholder = "Number of segments to get";
    document.getElementById('loop-label').innerHTML = 'Segments <span style="color:red">*</span>'; 
  } else {
    document.getElementById('loop').required = true;
    document.getElementById('loop').placeholder = "Times to loop playlist";
    document.getElementById('loop-label').innerHTML = 'Loop Playlist <span style="color:red">*</span>';
  }
}

function clear_form(form_name){
  document.getElementById(form_name).reset();
}

function assemble_payload(){
  var payload = {}
  /* Primary Parameters */
  payload.url = document.getElementById('url').value;
  payload.request_sleep = document.getElementById('request_sleep').value;
  payload.concurrency = document.getElementById('concurrency').value;
  payload.live = document.getElementById('live').value;
  payload.loop = document.getElementById('loop').value;

  /* Timeouts */
  payload.read_timeout = document.getElementById('read_timeout').value;
  payload.connect_timeout = document.getElementById('connect_timeout').value;

  /* Authentication Paramaters */
  payload.auth_url = document.getElementById('auth_url').value;
  payload.auth_username = document.getElementById('auth_username').value;
  payload.auth_password = document.getElementById('auth_password').value;
  payload.auth_type = document.getElementById('auth_type').value;

  return payload;
}

var es = false;

function send_form(){
  var url = '/set/';
  var client  = new XMLHttpRequest();
  var payload = assemble_payload();

  client.onreadystatechange = function() {
    if (client.readyState == 4 && client.status == 200) {

      es = new EventSource('/start/');
      document.getElementById('results_and_metrics').style.display = '';
      
      es.onmessage = function(e) {  
        // Responses
        var response = JSON.parse(e.data);
        var status_codes = response.status_codes;
        var results = response.results;
        var response_times = response.response_times;
        var success = response.success;

        // Data containers
        var return_code_container = document.getElementById('return_code_container');
        var response_type_container = document.getElementById('response_type_container');
        var response_times_container = document.getElementById('response_times_container');
        var playlist_status_container = document.getElementById('playlist_status_container');

        // Append Status Codes to view
        while (return_code_container.firstChild) {
            return_code_container.removeChild(return_code_container.firstChild);
        }
        
        var status_code_keys = Object.keys(status_codes);
        for (var i=0; i < status_code_keys.length; i++){
          var row_data = document.createElement('div');
          row_data.innerHTML = '<b>' + status_code_keys[i] + ' : </b>' + status_codes[status_code_keys[i]];
          return_code_container.appendChild(row_data);
        }

        // Response Types
        while (response_type_container.firstChild) {
            response_type_container.removeChild(response_type_container.firstChild);
        }
        
        var response_type_keys = Object.keys(results);
        for (var i=0; i < response_type_keys.length; i++){
          var row_data = document.createElement('div');
          row_data.style.marginLeft = ':20px';
          row_data.innerHTML = '<b>' + response_type_keys[i] + ' : </b>' + results[response_type_keys[i]];
          response_type_container.appendChild(row_data);
        }

        // Response Times
        while (response_times_container.firstChild) {
            response_times_container.removeChild(response_times_container.firstChild);
        }
        
        var response_times_keys = Object.keys(response_times);
        for (var i=0; i < response_times_keys.length; i++){
          var row_data = document.createElement('div');
          row_data.innerHTML = '<b>' + response_times_keys[i] + ' : </b>' + response_times[response_times_keys[i]] + ' seconds';
          response_times_container.appendChild(row_data);
        }

        // Playlists Acquired
        while (playlist_status_container.firstChild) {
            playlist_status_container.removeChild(playlist_status_container.firstChild);
        }
        
        var playlist_success_keys = Object.keys(success);
        for (var i=0; i < playlist_success_keys.length; i++){
          var row_data = document.createElement('div');
          row_data.innerHTML = '<b>' + playlist_success_keys[i] + ' : </b>' + success[playlist_success_keys[i]];
          playlist_status_container.appendChild(row_data);
        }

        // Text File Location
        document.getElementById('text_location').innerHTML = response.test_location;
      }
      
      es.onerror = function(e) {
        e = e || event, msg = '';
        switch( e.target.readyState ){
          case EventSource.CONNECTING: // Stream Closed
            es.close();
            document.getElementById('test_complete').innerHTML = 'Test Complete';
            document.getElementById('test_complete').style.color = 'green';
            return;
          case EventSource.CLOSED:
            console.log("Event source closed");
            document.getElementById('test_complete').innerHTML = 'Test Complete';
            document.getElementById('test_complete').style.color = 'green';
            return;
        }
      }
    } else {
      if(es.readyState !== 2) {
        try {
          es.close()
        } catch(e) {
          //socket already closed
        }
        return;
      }        
    }
  }

  document.getElementById('test_complete').innerHTML = 'Test Running';
  document.getElementById('test_complete').style.color = 'red';

  client.open('POST', url, true);
  client.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  client.send(JSON.stringify(payload));
}


function toggle_timeout_view(){
  // Minimize or Maximize Timeout Fields
  var timeout_fields = document.getElementById('timeout_fields');
  var timeout_header = document.getElementById('timeout_header');
  if (timeout_fields.style.display === 'none') {
    timeout_fields.style.display = '';
    timeout_header.innerHTML = '[&mdash;] Timeouts';
  } else {
    timeout_fields.style.display = 'none';
    timeout_header.innerHTML = '[+] Timeouts';
  }
}

function toggle_auth_view(){
  // Minimize or Maximize Authentication Fields
  var auth_fields = document.getElementById('auth_fields');
  var auth_header = document.getElementById('auth_header');

  if (auth_fields.style.display === 'none') {
    auth_fields.style.display = '';
    auth_header.innerHTML = '[&mdash;] Authentication';
  } else {
    auth_fields.style.display = 'none';
    auth_header.innerHTML = '[+] Authentication';
  }
}

// On Load
window.onload = function() {
  set_live(document.getElementById('live'));
  toggle_timeout_view();
  toggle_auth_view();
}


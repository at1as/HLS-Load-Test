function set_live(setting){
  if (setting.value === "True"){
    $('#loop').attr('required', true);  
    $('#loop').attr('placeholder', 'Number of segments to get');
    $('#loop-label').html('Segments <span style="color:red">*</span>'); 
  } else {
    $('#loop').attr('required', true);
    $('#loop').attr('placeholder', 'Times to loop playlist');
    $('#loop-label').html('Loop Playlist <span style="color:red">*</span>');
  }
}

function clear_form(form_name){
  $('#' + form_name).trigger('reset');
}

function assemble_payload(){
  var payload = {}
  /* Primary Parameters */
  payload.url = $('#url').val();
  payload.request_sleep = $('#request_sleep').val();
  payload.concurrency = $('#concurrency').val();
  payload.live = $('#live').val();
  payload.loop = $('#loop').val();

  /* Timeouts */
  payload.read_timeout = $('#read_timeout').val();
  payload.connect_timeout = $('#connect_timeout').val();

  /* Authentication Paramaters */
  payload.auth_url = $('#auth_url').val();
  payload.auth_username = $('#auth_username').val();
  payload.auth_password = $('#auth_password').val();
  payload.auth_type = $('#auth_type').val();

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
      $('#results_and_metrics').show();
      
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
          row_data.className = 'statistic';
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
          row_data.className = 'statistic';
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
          row_data.className = 'statistic';
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
          row_data.className = 'statistic';
          row_data.innerHTML = '<b>' + playlist_success_keys[i] + ' : </b>' + success[playlist_success_keys[i]];
          playlist_status_container.appendChild(row_data);
        }

        // Text File Location
        $('#text_location').html(response.test_location);
      }
      
      es.onerror = function(e) {
        e = e || event, msg = '';
        switch( e.target.readyState ){
          case EventSource.CONNECTING: // Stream Closed
            es.close();
            $('#test_complete').html('Test Complete');
            $('#test_complete').css('color', 'green');
            $('#submit_button').show();
            return;
          case EventSource.CLOSED:
            console.log("Event source closed");
            $('#test_complete').html('Test Complete');
            $('#test_complete').css('color', 'green');
            $('#submit_button').show();
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

  $('#test_complete').html('Test Running');
  $('#test_complete').css('color', 'red');
  $('#submit_button').hide();

  client.open('POST', url, true);
  client.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  client.send(JSON.stringify(payload));
}


function toggle_timeout_view(){
  // Minimize or Maximize Timeout Fields
  if ($('#timeout_fields').is(':hidden')) {
    $('#timeout_fields').show();
    $('#timeout_header').html('[&mdash;] Timeouts');
  } else {
    $('#timeout_fields').hide();
    $('#timeout_header').html('[+] Timeouts');
  }
}

function toggle_auth_view(){
  // Minimize or Maximize Authentication Fields
  if ($('#auth_fields').is(':hidden')) {
    $('#auth_fields').show();
    $('#auth_header').html('[&mdash;] Authentication');
  } else {
    $('#auth_fields').hide();
    $('#auth_header').html('[+] Authentication');
  }
}

// On Load
window.onload = function() {
  set_live($('#live'));
  toggle_timeout_view();
  toggle_auth_view();
}


// map.js
// Mon 02 Aug 2010 02:38:21 PM EEST

/* 
Initialization and simple manipulation functions for GeoTree demo.

Copyright (c) 2010 Artem Dudarev
License: Apache 2.0
*/

var map;
var geocoder;
var points_data = [];
var markersArray = [];
var lastLoadTime = 0;
var minLoadTimeDelta = 2000;
var min_zoom_points = 11;
var max_zoom_cities = 10;
var initialZoomIfGeolocated = 15;

// Deletes all markers in the array by removing references to them
// http://code.google.com/apis/maps/documentation/v3/overlays.html
function deleteOverlays() {
    if (markersArray) {
        for (i in markersArray) {
            markersArray[i].setMap(null);
        }
        markersArray.length = 0;
    }
}

// Initialization function
function initialize_map() {
    var myOptions = {
        zoom: 4,
        center: new google.maps.LatLng(48.03,20),
        mapTypeControl: true,
        mapTypeControlOptions: {style: google.maps.MapTypeControlStyle.DROPDOWN_MENU},
        navigationControl: true,
        navigationControlOptions: {style: google.maps.NavigationControlStyle.SMALL},
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };

    map = new google.maps.Map(document.getElementById("map_canvas_2"), myOptions);

    // http://code.google.com/apis/maps/documentation/javascript/basics.html#DetectingUserLocation
    // Try W3C Geolocation (Preferred)
    if(navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            initialLocation = new google.maps.LatLng(position.coords.latitude,position.coords.longitude);
            map.setCenter(initialLocation);
            map.setZoom(initialZoomIfGeolocated);
        }, function() {
            handleNoGeolocation();
        });
    }

    function handleNoGeolocation() {
    }

    geocoder = new google.maps.Geocoder();

    // Insert this overlay map type as the first overlay map type at
    // position 0. Note that all overlay map types appear on top of
    // their parent base map.
    map.overlayMapTypes.insertAt(
        0, new CoordMapType(new google.maps.Size(256, 256)));

    google.maps.event.addListener(map, 'zoom_changed', function() {
        var d = new Date();
        if (map.zoom >= min_zoom_points){
            if ( (d.getTime() - lastLoadTime) > minLoadTimeDelta ){
                lastLoadTime = d.getTime();
                setTimeout(load_points, 200);
                setTimeout(request_update, 200);
            }
        } else {
            if ( (d.getTime() - lastLoadTime) > minLoadTimeDelta ){
                lastLoadTime = d.getTime();
                setTimeout("load_points('cities')", 200);
            }
        }
        if (map.zoom > 16){
             $("#update_osm_button").attr("disabled","");
        } else {
             $("#update_osm_button").attr("disabled","disabled");
        }
    });
    
    load_points('cities');
}

// Load JSON of all points in tiles (3x3 tiles around center tile)
function load_points(type){
    deleteOverlays();

    z = map.getZoom();
    centerTile = PointToTile(map.getCenter(),z);
    center =  centerTile.x + ',' + centerTile.y + ',' + z;
    
    if (type == 'cities'){
        url = '/gt/t/?c=' + center + '&gt=cities';
    } else {
        url = '/gt/t/?c=' + center;
    }

    $.ajax({ url: url, success: function(data){
            points_data = eval(data);
            for(var i=0; i<points_data.length; i++){
                var lat = points_data[i]['coord'][0];
                var lon = points_data[i]['coord'][1];
                var marker = new google.maps.Marker({
                    position: new google.maps.LatLng(lat,lon), 
                    map: map,
                    info: lat
                });   
                markersArray.push(marker);
                attachInfoDiv(marker,i);
                $('#marker_info').html('');
                $('#update_info').html('');
            }
      }});
}

// requests update of the POIs in the database
function request_update(){
    var p = map.getCenter();
    var lat = p.lat();
    var lng = p.lng();
    z = map.getZoom();
    centerTile = PointToTile(map.getCenter(),z);
    center =  centerTile.x + ',' + centerTile.y + ',' + z;
    
    url = '/gt/up/?ll=' + lat + ',' + lng;
    $.ajax({ 
            url: url,
            success: function(data){}
          });
}

// Update city info div when mouseover over marker
function attachInfoDiv(marker,i){
    google.maps.event.addListener(marker, "mouseover", function(e) {
            var html = '<h2>'+points_data[i]['name']+'</h2>';
            html += 'importance: '+points_data[i]['importance']+'<br/>';
            var lat = points_data[i]['coord'][0];
            var lon = points_data[i]['coord'][1];
            var z = map.getZoom();
            var tile = PointToTile(new google.maps.LatLng(lat,lon),z);
            var tile_str =  tile.x + ',' + tile.y + ',' + z;
            html += 'tile: ' + tile_str;
            $('#marker_info').html(html);
            $('#attr_container').html('');
        });
    info_window = new google.maps.InfoWindow({});
    google.maps.event.addListener(marker, "click", function(e) {
            info_window.close(null);

            var attr_data = '';

            if (points_data[i]['name']){
                // info_window.content = '<div id="info_window_holder"><a href="/p/'+points_data[i]['key_name']+'"><span key_name="'+points_data[i]['key_name']+'" id="place_name">'+points_data[i]['name']+'</span></a>';
                $("#place-title-holder").text(points_data[i]['name']);
                } else {
                // info_window.content = '<div id="info_window_holder"><a href="/p/'+points_data[i]['key_name']+'"><span key_name="'+points_data[i]['key_name']+'" id="place_name">'+points_data[i]['key_name']+'</span></a>';
                $("#place-title-holder").text(points_data[i]['key_name']);
                }
            info_window.content += '<br/><span id="attr_data"></span>';
            info_window.content += "<br/><br/><br/><input type='button' id='up_button' value='Up' onclick='upPlace()'/>";
            info_window.content += "&nbsp;&nbsp;&nbsp;&nbsp;<input type='button' id='down_button' value='Down' onclick='downPlace()'/>";
            info_window.content += "</div>";
            // info_window.open(map,marker);
            connect_marker = marker;
            
            url = '/p/'+points_data[i]['key_name'];
            $.ajax({ url: url, success: function(data){
                $("#attr_container").html(data);
            }});

        });
}

function geocodeCity() {
    var address = $("#city-field").val();
    if (geocoder) {
      geocoder.geocode( { 'address': address}, function(results, status) {
        if (status == google.maps.GeocoderStatus.OK) {
          map.setCenter(results[0].geometry.location);
          if (results[0].geometry.bounds){
              map.fitBounds(results[0].geometry.bounds);
          }
          if (results[0].geometry.viewport){
              map.fitBounds(results[0].geometry.viewport);
          }
        } else {
          alert("Geocode was not successful for the following reason: " + status);
        }
      });
    }
}

function geocodeOnEnter(e) {
    evt = e || window.event;
    var keyPressed = evt.which || evt.keyCode;
    if (keyPressed == 13){
        geocodeCity();
    }
    else {
        return true;
    }
}

function upPlace(key_name) {
    var key_name = $("#place_name").attr("key_name");
    url = '/up_place/' + key_name;
    $.ajax({ url: url, success: function(data){
        $("#update_info").html(data);
    }});
}

function downPlace(key_name) {
    var key_name = $("#place_name").attr("key_name");
    url = '/down_place/' + key_name;
    $.ajax({ url: url, success: function(data){
        $("#update_info").html(data);
    }});
}

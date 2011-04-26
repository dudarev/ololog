// google-maps-v3-samples.js
// Mon 15 Mar 2010 10:23:00 AM EET

/* 
These are collections of functions picked up from Google Maps API v3 samples posted at
http://code.google.com/p/gmaps-samples-v3/

License: Apache 2.0
*/

// To have conversion PointToTile
// http://code.google.com/apis/maps/documentation/v3/examples/map-coordinates.html
var MERCATOR_RANGE = 256;
 
function bound(value, opt_min, opt_max) {
  if (opt_min != null) value = Math.max(value, opt_min);
  if (opt_max != null) value = Math.min(value, opt_max);
  return value;
}
 
function degreesToRadians(deg) {
  return deg * (Math.PI / 180);
}
 
function radiansToDegrees(rad) {
  return rad / (Math.PI / 180);
}
 
function MercatorProjection() {
  this.pixelOrigin_ = new google.maps.Point(
      MERCATOR_RANGE / 2, MERCATOR_RANGE / 2);
  this.pixelsPerLonDegree_ = MERCATOR_RANGE / 360;
  this.pixelsPerLonRadian_ = MERCATOR_RANGE / (2 * Math.PI);
};
 
MercatorProjection.prototype.fromLatLngToPoint = function(latLng, opt_point) {
  var me = this;
 
  var point = opt_point || new google.maps.Point(0, 0);
 
  var origin = me.pixelOrigin_;
  point.x = origin.x + latLng.lng() * me.pixelsPerLonDegree_;
  // NOTE(appleton): Truncating to 0.9999 effectively limits latitude to
  // 89.189.  This is about a third of a tile past the edge of the world tile.
  var siny = bound(Math.sin(degreesToRadians(latLng.lat())), -0.9999, 0.9999);
  point.y = origin.y + 0.5 * Math.log((1 + siny) / (1 - siny)) * -me.pixelsPerLonRadian_;
  return point;
};
 
MercatorProjection.prototype.fromPointToLatLng = function(point) {
  var me = this;
  
  var origin = me.pixelOrigin_;
  var lng = (point.x - origin.x) / me.pixelsPerLonDegree_;
  var latRadians = (point.y - origin.y) / -me.pixelsPerLonRadian_;
  var lat = radiansToDegrees(2 * Math.atan(Math.exp(latRadians)) - Math.PI / 2);
  return new google.maps.LatLng(lat, lng);
};
 
function PointToTile(point,z){
    var projection = new MercatorProjection();
    var worldCoordinate = projection.fromLatLngToPoint(point);
    var pixelCoordinate = new google.maps.Point(worldCoordinate.x * Math.pow(2, z), worldCoordinate.y * Math.pow(2, z));
    var tileCoordinate = new google.maps.Point(Math.floor(pixelCoordinate.x / MERCATOR_RANGE), Math.floor(pixelCoordinate.y / MERCATOR_RANGE));
    return tileCoordinate;
}

// To have tiles with numbers overlayed.
// http://code.google.com/apis/maps/documentation/v3/examples/maptype-overlay.html
// http://code.google.com/apis/maps/documentation/v3/overlays.html#OverlayMapTypes
function CoordMapType(tileSize) {
    this.tileSize = tileSize;
}

CoordMapType.prototype.getTile = function(coord, zoom, ownerDocument) {
    var div = ownerDocument.createElement('DIV');
    div.innerHTML = '<div style="padding:10px; font-size:20px;">' + coord.x + ', ' + coord.y + ', ' + zoom + '</div>';
    div.style.width = this.tileSize.width + 'px';
    div.style.height = this.tileSize.height + 'px';
    div.style.borderStyle = 'solid';
    div.style.borderWidth = '1px';
    div.style.borderColor = '#AAAAAA';
    div.style.color = ' #FF7878';
    div.style.fontSize = '30';
    return div;
};

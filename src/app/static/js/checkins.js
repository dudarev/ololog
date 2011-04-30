function checkinsAdd(){
    var place_key_name = $('#place-title-holder').attr('key_name');
    var place_title = $('#place-title-holder').text();
    $('#place-title-holder').text('Checking in...');
    // showProgress("#tweet-messages");
    $.post("/checkins/add", {
              place_key_name: place_key_name
              },
              function (data) {
                if( data.match(/Success/) ){
                    $('#place-title-holder').text('Success');
                } else {
                    $('#place-title-holder').text('Error');
                }
              }
          );
};

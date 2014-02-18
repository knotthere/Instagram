// A sample application that uses the Instagram and Google Maps API's
// 
// knotthere@gmail.com
// 20140217


$(document).ready(function() {
    var gIndex = 0;
    var gFront = true;  // So we can fade in and out...
    var gPause = false;
    var gLocal = false; // Local development?

    // Cycle through the 9 cells.  Allow 81 so local development can tell the progress
    function nextCell() {
        var _nextIndex = (gIndex % 8).toString();
        if (++gIndex == 8) {
            gIndex = 0;
            gFront = !gFront
        }

        return _nextIndex;
    }

    var gTimer = setInterval(function() {
        myTimer()
    }, 4000);

    function myTimer() {
        if (gPause)
            return;

        if (gLocal) {
            var cell = nextCell();
            $("#a" + cell).text(gIndex.toString());
            $("#a" + cell).attr('href', "http://instagram.com");
        } else {
            // Poll for new image...
            $.get("/fetchone", function(data) {
                //$.each( data, function( key, val ) {
                if (data != "") {
                    // Can skip calling this if we asked for JSON
                    //var json = $.parseJSON(data);   // Error if blank
                    var cell = nextCell();
                    $("#a" + cell).attr('href', "http://instagram.com/" + data[0]).attr('title', data[3]);
                    // Oftentimes, we cannot access the resource - error handling below
                    $("#i0" + cell)
                        .attr('data-lat', data[4]['latitude'].toString())
                        .attr('data-lng', data[4]['longitude'].toString())
                        .attr('src', data[2]); // src last, so lat/lng are up to date.
                }
                //});
            }, "json"); // Ask for "json" and result is automatically converted
        }
    }

    function myStopFunction() {
        clearInterval(gTimer);
    }

    $("img").error(function() {
        // This is still needed, even with 'alt' defined
        $(this).attr('src', 'static/FreshTracks.jpg');
    }).load(function() {
        $(":not(this)").css('border-color', '#ffffff');
        $(this).css('border-color', '#000000');
        if ($(this).attr('data-lat')) {
            panMap(Number($(this).attr('data-lat')), Number($(this).attr('data-lng')));
        }
    })  .attr('src', 'static/FreshTracks.jpg') 
        .attr('alt', 'static/FreshTracks.jpg'); // Both required

    // These were intended for fade-in/out, but I can't get the img's to overlay just yet
    $('img[id^="i1"]').css('display', 'none');

    $("a").attr('target', '_blank');

    // Any click pauses the fetch
    $("body").click(function() {
        gPause = !gPause;
        var _color = (gPause ? "#888888" : "#ffffff");
        $("body").attr('bgcolor', _color);
    });

    function returnPoint(lat, lng) {
        return new google.maps.LatLng(lat, lng);
    }

    function panMap(lat, lng) {
        map.panTo(returnPoint(lat, lng));
    }

    var map = new google.maps.Map($("#map")[0], {
        zoom: 16,
        center: returnPoint(-122, 44),
        mapTypeId: google.maps.MapTypeId.HYBRID
    });
});
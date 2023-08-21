$(document).on('click', 'button', function() {
    var request_type = $(this).attr('data-request_type');
    var device_id = $(this).attr('data-device_id');
    var post_data = {};
    var request_url;

    if(!device_id)
    {
        console.log("Missing device id");
        return;
    }

    post_data['device_id'] = device_id;

    switch(request_type)
    {
        case 'status':
            console.log("status request")
            request_url = "api/status"
            post_data['command'] = 'status'
            break;
        case 'sprinkle-1-min':
            console.log("sprinkle 1 min")
            request_url = "api/sprinkle_start"
            post_data['command'] = 'sprinkle_start'
            post_data['watering_length_minutes'] = 1;
            break;
        case 'sprinkle-on':
            console.log("Sprinkle on")
            request_url = "api/sprinkle_on"
            break;
        case 'sprinkle-off':
            console.log("Sprinkle off")
            request_url = "api/sprinkle_off"
            break;
        default:
            console.log(`Unknown request type ${request_type}`)
            return;
    }

    $.ajax({
        type: "POST",
        url: request_url,
        data: JSON.stringify(post_data),
        dataType: "json",
        success: function() {
            console.log("Successfully sent request");
            console.log(`url: ${request_url}`);
            console.log("Post data");
            console.log(post_data);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.log(`Error making request to url ${request_url}.  Status: ${textStatus}, Error: ${errorThrown}`)
        }
    })
})

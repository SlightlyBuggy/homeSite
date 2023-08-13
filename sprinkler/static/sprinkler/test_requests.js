$(document).on('click', 'button', function() {
    var request_type = $(this).attr('data-request_type');
    var device_id = $(this).attr('data-device_id');
    var post_data = {};
    var test_url;

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
            test_url = "test_device_command_status"
            post_data['command'] = 'status'
            break;
        case 'sprinkle-1-min':
            console.log("sprinkle 1 min")
            test_url = "test_device_command_sprinkle_start"
            post_data['command'] = 'sprinkle_start'
            post_data['watering_length_minutes'] = 1;
            break;
        default:
            console.log(`Unknown request type ${request_type}`)
            return;
    }

    $.ajax({
        type: "POST",
        url: test_url,
        data: JSON.stringify(post_data),
        dataType: "json",
        success: function() {
            console.log("Successfully sent request");
            console.log(`url: ${test_url}`);
            console.log("Post data");
            console.log(post_data);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.log(`Error making request to url ${test_url}.  Status: ${textStatus}, Error: ${errorThrown}`)
        }
    })
})
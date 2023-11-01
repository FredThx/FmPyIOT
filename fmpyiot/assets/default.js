function update_files() {
    $('#list select option').remove();
    $.getJSON("/api/ls", function(data) {
        $.each(data['files'], function(index, file) {
                $('<option />', {html: file}).appendTo($('#list select'));
        });
    });
}

function update_status() {
    $.getJSON("/api/status", function(data) {
        $.each([], function(index, key) {
            $('#' + key).html(data[key]);
        });
    });
}

function init_vars() {
    $.getJSON("/api/status", function(data) {
        $.each(['name', 'description'], function(index, key) {
            $('#'+key).html(data['./SYSINFO'][key]);
        });
    });
}

$(document).ready(function() {
    $(document).on('submit', '#upload', function(e) {
        var form = $(this);
        var success = 0;
        $.each($('#files').prop('files'), function(index, file) {
            $('#status').html("Sending " + file.name);

            $.ajax({
                async: false,
                url: form.attr('action') + file.name,
                method: 'PUT',
                data: file,
                processData: false,  // tell jQuery not to process the data
                contentType: false,  // tell jQuery not to set contentType
            }).done(function() {
                success++;

                update_files();
            });
        });

        $('#status').html(success + " file(s) uploaded successfully.");

        e.preventDefault();
    }).on('submit', '#list', function(e) {
        var file = $(this).find('select').val()[0];
            if (file) {
                var button = document.activeElement['value'];
                if (button=="Download"){
                    window.location = '/api/download/' + file;
                }
                if (button=="Delete"){
                    $.ajax({
                        async: false,
                        url: "/api/delete/" + file,
                        method: 'DELETE',
                    }).done(function() {
                        update_files();
                    });
                }
            }

        e.preventDefault();
    });

    setInterval(update_status, 1000);

    init_vars();
    update_files();
    update_status();
});

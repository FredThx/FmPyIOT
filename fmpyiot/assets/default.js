//Mise à jour de la liste des fichier présents sur le device
//TODO : recursif
function update_files() {
    $('#list select option').remove();
    $.getJSON("/api/ls", function(data) {
        $.each(data['files'], function(index, file) {
                $('<option />', {html: file}).appendTo($('#list select'));
        });
    });
}

//Mise à jour du status : ("./SYSINFO")
//  - #json_sysinfo
//  - valeurs des topics
// Est executée toutes les secondes
function update_status() {
    $.getJSON("/api/status", function(data) {
        var sysinfo = data["./SYSINFO"].payload
        $('#json_sysinfo').html(JSON.stringify(sysinfo, undefined, 2));
        Object.entries(data).forEach(entry => {
            const [topic,data_topic] = entry;
            $('#' + data_topic.id).html(data_topic.payload);
            });
    });
}

//Initialisation des valeurs
//  - #name, #descriptions, #list_topics
//Est executé au chargement
function init_vars() {
    $.getJSON("/api/status", function(data) {
        $.each(['name', 'description'], function(index, key) {
            $('#'+key).html(data['./SYSINFO'].payload[key]);
        });
        $('#REPL-logging-level-select').val(data['./SYSINFO'].payload['logging_level']);
    });
    $.get("/api/topics", function(html) {
        $('#list-topics').html(html);
    });
}

// Mise à jour de REPL
// Est executé toutes les 500 ms
REPL_lines = []
function update_repl(){
    $.getJSON("/api/repl", function(data){
        data.repl.forEach(function(line){
            len_REPL_lines = REPL_lines.push(line);
            if (len_REPL_lines>100){
                REPL_lines.shift();
            }
            let textarea = $('#REPL-output');
            let input = $('#REPL-input');
            let bt_input = $("#REPL-input-btn");
            textarea.val(REPL_lines.join('\n'));
            textarea.scrollTop(textarea[0].scrollHeight);
            input.width(textarea.width()-bt_input.width()-20);
        })
    })

}

//Quand la page est chargée
$(document).ready(function() {
    // gestion des evenements
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
    }).on('submit', '#form-list-topics', function(e){
        let button = document.activeElement['value'];
        let datas = {
            'topic' : document.getElementById("_topic_"+button).value,
            'payload' : document.getElementById("_payload_"+button).value
            };
        $.ajax({
            async : false,
            url : '/api/action/'+button,
            method:'POST',
            data: datas,
        })
        e.preventDefault();
    });

    $("#REPL-logging-level-select").on("change", function(e){
        let level = $("#REPL-logging-level-select").val();
        $.ajax({
            async: false,
            url: "/api/logging-level/" + level,
            method: 'POST',
        })
    })

    // main
    setInterval(update_status, 1000);
    setInterval(update_repl, 500);

    init_vars();
    update_files();
    update_status();
});

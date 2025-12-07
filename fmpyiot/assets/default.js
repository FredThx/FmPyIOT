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
        //Update sysinfo data
        var sysinfo = data["./SYSINFO"].payload;
        $('#json_sysinfo').html(JSON.stringify(sysinfo, undefined, 2));
        //Update topics data
        Object.entries(data).forEach(entry => {
            const [topic,data_topic] = entry;
            $('#' + data_topic.id).html(JSON.stringify(data_topic.payload));
            });
        //Update head data
        //RSSI
        $('#ssid').html(sysinfo.wifi.ssid);
        // Wifi strenght
        var wifi_class;
        if (sysinfo.wifi.rssi > -66){
            wifi_class = "waveStrength-4";
        }else if (sysinfo.wifi.rssi > -70){
            wifi_class = "waveStrength-3";
        }else if (sysinfo.wifi.rssi > -82){
            wifi_class = "waveStrength-2";
        }else{
            wifi_class = "waveStrength-1";
        }
        $('#wifi_strenght').attr("class", wifi_class);
        // Mem free
        let e_mem_free = $("#mem_free");
        let mem_free_percent = ~~(100*sysinfo.mem_free / (sysinfo.mem_free + sysinfo.mem_alloc));
        if (mem_free_percent>25){
            e_mem_free.attr("class", "progress-bar bg-success");
        }else{
            e_mem_free.attr("class", "progress-bar bg-danger");
        }
        e_mem_free.attr("style", "width: " + mem_free_percent + "%");
        e_mem_free.attr("aria-valuenow", mem_free_percent.toString());
        $("#mem_free_text").text(mem_free_percent + "%");
        // Flash memory free
        let e_flash_mem_free = $("#flash_mem_free");
        let flash_mem_free_percent = ~~(100*sysinfo.statvfs.f_bfree / sysinfo.statvfs.f_blocks);
        let flash_mem_free = ~~((sysinfo.statvfs.f_bfree * sysinfo.statvfs.f_frsize)/1000);
        if (flash_mem_free_percent>15){
            e_flash_mem_free.attr("class", "progress-bar bg-success");
        }else{
            e_flash_mem_free.attr("class", "progress-bar bg-danger");
        }
        e_flash_mem_free.attr("style", "width: " + flash_mem_free_percent + "%");
        e_flash_mem_free.attr("aria-valuenow", flash_mem_free_percent.toString());
        $("#flash_mem_free_text").text(flash_mem_free + "Ko");
        //Title
        $('title').html("FmPyIot " + sysinfo.name);
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
    $.get("/api/params", function(html) {
        $('#list-params').html(html);
    });
}

// Mise à jour de REPL
// Est executé toutes les 500 ms
REPL_lines = []
function update_repl(){
    let textarea = $('#REPL-output');
    $.getJSON("/api/repl", function(data){
        data.repl.forEach(function(line){
            len_REPL_lines = REPL_lines.push(line);
            if (len_REPL_lines>100){
                REPL_lines.shift();
            }
            textarea.val(REPL_lines.join('\n'));
            textarea.scrollTop(textarea[0].scrollHeight);
        })
    })
    let input = $('#REPL-input');
    let bt_input = $("#REPL-input-btn");
    input.width(textarea.width()-bt_input.width()-20);
}

function do_repl_cmd(){
    let cmd = $("#REPL-input").val();
    if (cmd){
        $.ajax({
            async : true,
            url : '/api/repl/cmd',
            method:'POST',
            contentType: "application/json",
            dataType: "json",
            data: JSON.stringify({'cmd' : cmd}),
        }).done(function(r){
            $("#REPL-input").val("");
        });
    }
}

//Mise à jour du main : (render_web)
// Est executée toutes les secondes
function update_main() {    
    $.get("/api/render_web", function(html) {
        $('#render_web').html(html);
    });
}

function initApp(){
    console.log("App initialized");
    //Quand la page est chargée
    $(document).ready(function() {
        // gestion des evenements
        $(document).on('submit', '#upload', function(e) {
            var form = $(this);
            var success = 0;
            $.each($('#files').prop('files'), function(index, file) {
                $('#status-upload').html("Sending " + file.name);

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
            $('#status-upload').html(success + " file(s) uploaded successfully.");
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
                async : true,
                url : '/api/action/'+button,
                method:'POST',
                contentType: "application/json",
                dataType: "json",
                data: JSON.stringify(datas),
            })
            e.preventDefault();
        }).on('submit', '#upload-folder', function(e){
            var form = $(this);
            var success = 0;
            $('#status-upload-folder').html("Upload files ...");
            $.each($('#files-folder').prop('files'), function(index, file) {
                $.ajax({
                    async: false,
                    url: form.attr('action') + file.webkitRelativePath,
                    method: 'PUT',
                    data: file,
                    processData: false,  // tell jQuery not to process the data
                    contentType: false,  // tell jQuery not to set contentType
                }).done(function() {
                    success++;
                    update_files();
                });
            });
            $('#status-upload-folder').html(success + " file(s) uploaded successfully.");
            e.preventDefault();
        }).on('submit', '#form-list-params', function(e){
                let key = document.activeElement['id'].substring(12); // Extract the key from the id '_set_params_key' or 'del_params_key'
                let action = document.activeElement['id'].substring(1,11); // Extract the action from the id 'set_params_key' or 'del_params_key'
                if (action == "set_params"){
                    let datas = {
                        'topic' : "",
                        'payload' : {}
                    };
                    datas['payload'][key] = document.getElementById("_params_"+key).value
                    $.ajax({
                        async : true,
                        url : '/api/action/action_T__SET_PARAMS',
                        method:'POST',
                        contentType: "application/json",
                        dataType: "json",
                        data: JSON.stringify(datas),
                    });
                } else if (action == "del_params") {
                    $.ajax({
                        async : true,
                        url : '/api/params/delete/' + key,
                        method:'DELETE',
                    });
                    document.getElementById("_line_params_"+key).remove();
                }
                e.preventDefault();
        });

        $("#REPL-logging-level-select").on("change", function(e){
            let level = $("#REPL-logging-level-select").val();
            $.ajax({
                async: false,
                url: "/api/logging-level/" + level,
                method: 'POST',
            });
            e.preventDefault();
        });

        $("#REPL-input-btn").on("click", function(e){
            do_repl_cmd();
            e.preventDefault();
        });
        $("#REPL-input").on("keypress", function(e){
            if (e.key === "Enter"){
                do_repl_cmd();
                e.preventDefault();
            }
        });
        $("#REBOOT").on("click", function(e){
            $.ajax({
                async : true,
                url : '/api/reboot',
                method:'GET',
            }).done();
            e.preventDefault();
        });
        $("#BOOTLOADER").on("click", function(e){
            $.ajax({
                async : true,
                url : '/api/bootloader',
                method:'GET',
            }).done();
            e.preventDefault();
        });

    setInterval(update_status, 1000);
    setInterval(update_main, 1000);
    setInterval(update_repl, 500);
    init_vars();
    update_files();
    update_status();
        
    });

}

odoo.define('portal_provider.update_sku', function (require){
"use strict";
    var ajax = require('web.ajax');

     $(document).ready(function(){

        function create_notification(header, message, status){
            var o_toast_color = '' // danger, success, warning
            if (status == 0) {
                o_toast_color = 'bg-danger'
            }else if(status == 1){
                o_toast_color = 'bg-warning'
            }else{
                o_toast_color = 'bg-success'
            }

            var toast = '<div class="position-fixed top-0 end-0 p-3" style="z-index: 11">'+
            '<div id="notification-manager" class="toast rounded '+ o_toast_color +' fade show" role="alert" aria-live="assertive" aria-atomic="true">' +
                            '<div class="toast-header">' +
                               '<strong class="me-auto">'+ header +'</strong>'+
                                '<small class="text-muted">justo ahora</small>'+
                                '<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"/>'+
                            '</div>'+
                            '<div class="toast-body">' + message + '</div></div></div>'

            return toast;
        };

        function delete_notification(){
            $("#notification-manager").remove();
        };

        $(document).on("click", "#close-alert-notification", function() {
            delete_notification();
        });
        
        //Add for all buttons on click event handler to display the modal.
        var buttons = document.querySelectorAll("button[name='update_sku']");
        console.log(buttons);
        for (var i=0; i<buttons.length ; i++ ){
            buttons[i].addEventListener('click',update_sku);
        }

        function update_sku(event){
            delete_notification();
            var button = event.target;
            var form_data = {}
            var p_id = button.id
            form_data['product_id'] = p_id;
            var query = "input[id='" + p_id.toString() + "']"
            form_data['sku'] = $(query)[0].value;
            ajax.jsonRpc('/update_sku','call',{vals : form_data}).then(function(result){
                var notif = create_notification(result['header'], result['message'], result['status']);
                $('body').prepend(notif);
            });
        }

        $('#product_import_csv').on('click',function(e){
            $("#import_product_csv_modal").css('display','block');
        });

        $('#csvFile').change(function(e){
            var fileName = e.target.files[0];
            var length = 23
            if (fileName != null){
                $('#label-csv-file-selector').text("Name file: " + fileName.name.substring(0,length));
            }else{
                $('#label-csv-file-selector').text("No file chosen ...");
            }
        });

        $('#close_span_import_csv').on('click',function(e){
            $("#import_product_csv_modal").css('display','none');
        });

        $("#import_btn_csv_portal").click(function(e){
            var input = $('input[type="file"]')[0].files[0];
            if (input != null){
                var reader = new FileReader();
                reader.onload = function(){
                    var dataURL = reader.result;
                    var form_data = {}
                    form_data['fname'] = input.name;
                    form_data['data'] = dataURL //e.target.result;
                    $.blockUI();
                    ajax.jsonRpc('/import_product_csv','call',{vals : form_data}).then(function(result){
                        $.unblockUI();
                        $("#import_product_csv_modal").css('display','none');
                        location.reload();
                    });
                };
                reader.readAsDataURL(input);
            }else{
              var notif = create_notification("Informatión", "You have not selected a file to import", 1);
                $('body').prepend(notif);
            }
        });

    });
});
    

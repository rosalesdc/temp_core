odoo.define('w_website_account_invoice.import_xml', function (require){
"use strict";

    var ajax = require('web.ajax');  
    
    var spinner = `
    <div>
        <div class="oe_blockui_spin" style="height: 50px">
            <img src="/web/static/img/spin.png" style="animation: fa-spin 1s infinite steps(12);" alt="Loading..."/>
        </div>
        <br />
        <div class="oe_throbber_message" style="color:white">
            Loading...
        </div>
    </div>
    `;

    $.blockUI.defaults.baseZ = 1100;
    $.blockUI.defaults.message = spinner;
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';

    $(function(){
        
        $('#my-file-selector-portal').change(function(e){
            var fileName = e.target.files[0];
            var length = 50
            if (fileName != null){
                $('#label-file-selector').text(fileName.name);
            }else{
                $('#label-file-selector').text("No file chosen ...");
            }
        });

        $('#close_span').on('click',function(){
            var modal = document.getElementById('portal_message_modal');
            modal.style.display = "none";
        }); 

        $('#close_span_add_xml').on('click',function(){
            var modal = document.getElementById('add_xml_modal');
            modal.style.display = "none";
        }); 

        //Add for all buttons on click event handler to display the modal.
        var buttons = document.querySelectorAll('#add_xml_button');
        for (var i=0; i<buttons.length ; i++ ){
            buttons[i].addEventListener('click',displayXmlModal);
        }

        function displayXmlModal(event){
            var button = event.target;
            var po_id = button.attributes["poid"].value;
            var po_name = button.attributes["poname"].value;
            $("#purchase_order_name").val(po_name);
            $("#purchase_order_id").val(po_id);
            $("#purchase_order_name").text(po_name);
        }

        $('#submit_button_portal').on('click',function(e){
            var input = $('input[type="file"]')[0].files[0];
            if (input != null){
                var p_id = $("#purchase_order_id").val();
                var reader = new FileReader();
                reader.onload = function(e){
                    var dataURL = reader.result;
                    var form_data = {}
                    form_data['fname'] = input.name;
                    form_data['data'] = dataURL  // e.target.result;
                    form_data['order_id'] = p_id;
                    $.blockUI();
                    var server_response = ajax.jsonRpc('/check_load_xml','call',{vals : form_data});
                    server_response.then(function(result){
                        var modal = document.getElementById('portal_message_modal');
                        var messages = ""
                        for (var i=0; i<result.length ; i++ ){

                            var message = result[i]['message'];
                            var head = result[i]['header'];
                            var fname = result[i]['name'];
                            var code = result[i]['code'];
                            var style = ""
                            console.log(message);
                            console.log(head);
                            console.log(fname);
                            if (code == 0) {
                                style = 'style = "color: #ff5252;"';
                            }else if(code == 1){
                                style = 'style = "color: #ffeb3b;"';
                            }else{
                                style = 'style = "color: #00c853;"';
                            }
                            
                            messages = messages + "<div style='font-size: 16px;'> <p style='font-weight: bold;'>"+fname+":</p> <span "+ style + ">"+head+":</span> <span>"+message+"</span> </div><p></p>"
                        } 
                        $('#messages').html(messages)
                        $('#title_response').text("Resultado");
                        modal.style.display = 'block';
                        $.unblockUI();
                        setTimeout(function() { window.location.reload(); }, 3000);
                        
                });
                //$.unblockUI();
                };
                reader.readAsDataURL(input);
            }else{
                alert("No ha seleccionado un archivo para enviar");
            }
        });
        
    });
    
});

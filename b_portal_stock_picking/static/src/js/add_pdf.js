odoo.define('b_portal_stock_picking.add_pdf', function (require) {
    "use strict";

    var ajax = require('web.ajax');

    $(function () {

        $('td.td_invoices select.invoice').change(function (event) {
            var corr_add_pdf_button = $(event.target).closest('tr').find('button.b_add_pdf_btn');
            if ($(event.target).val()) {
                corr_add_pdf_button.removeClass('d-none');
            } else {
                corr_add_pdf_button.addClass('d-none');
            }
        });

        // Modal
        $('#b_add_pdf_modal #b_add_pdf_file_selector').change(function (e) {
            var fileName = e.target.files[0];
            var length = 23
            if (fileName != null) {
                $('#b_add_pdf_file_selector_label').text(fileName.name.substring(0, length) + "...");
            } else {
                $('#b_add_pdf_file_selector_label').text("No file chosen ...");
            }
        });

        $('#b_add_pdf_close').click(function () {
            var modal = $('#b_add_pdf_modal');
            modal.css('display', 'none');
        });

        $('.b_add_pdf_btn').click(function (event) {
            var button = $(event.target);
            var corr_invoice_select = button.closest('tr').find('td.td_invoices select.invoice');
            var modal = $('#b_add_pdf_modal');
            var invoice_name = corr_invoice_select.find('option:selected').text();
            var invoice_name_el = modal.find('#b_add_pdf_invoice_name');
            invoice_name_el.data('invoice_id', corr_invoice_select.val());
            invoice_name_el.data('invoice_name',);
            invoice_name_el.text(invoice_name);
            $('#b_add_pdf_file_selector').val(null);
            $('#b_add_pdf_file_selector_label').text('Seleccione un fichero')
            modal.css('display', 'block');
        })

        $('#b_add_pdf_submit_button').on('click', function (e) {
            //Read the file and send it to the controller and show th response
            var input = $('#b_add_pdf_file_selector')[0].files[0];
            if (input != null) {
                var fname_arr = input.name.split('.');
                if (fname_arr.length > 1 && fname_arr[fname_arr.length - 1] == 'pdf') {
                    var invoice_name_el = $('#b_add_pdf_invoice_name');
                    var invoice_id = invoice_name_el.data('invoice_id');
                    var reader = new FileReader();
                    reader.onload = function (e) {
                        var form_data = {}
                        form_data['invoice_id'] = invoice_id;
                        form_data['data'] = e.target.result;
                        form_data['fname'] = input.name;

                        $.blockUI();
                        var server_response = ajax.jsonRpc('/invoice_load_pdf', 'call', { vals: form_data });
                        server_response.then(function (result) {
                            var modal = $('#b_message_modal');
                            modal.find('#b_title_response').text("Resultado");
                            modal.find('#b_messages').html(result.message)
                            if ('success' in result && result.success) {
                                $('#b_add_pdf_modal').css('display', 'none');
                            }
                            modal.css('display', 'block');
                            setTimeout(function () {
                                modal.css('display', 'none');
                            }, 5000);
                            $.unblockUI();
                        }).catch(result => $.unblockUI());
                    };
                    reader.readAsDataURL(input);
                } else {
                    alert("Debe seleccionar un fichero pdf");
                }
            } else {
                alert("No ha seleccionado un archivo para enviar");
            }
        });
    });
});

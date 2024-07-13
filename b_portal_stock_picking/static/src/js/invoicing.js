odoo.define('b_portal_stock_picking.invoicing', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var rpc = require('web.rpc');

    $(function () {
        var picking_select = $('td.td_picking_ids select.picking');
        picking_select.change(function (evt) {
            var pickid = $(evt.target).val();
            var add_inv_btn = $(evt.target).closest('tr').find('.b_add_invoice_buttom');
            if (!pickid) {
                add_inv_btn.addClass('d-none');
            } else {
                pickid = parseInt(pickid);
                $.blockUI();
                rpc.query({
                    model: 'stock.picking',
                    method: 'check_invoiced',
                    args: [pickid],
                }).then(function (result) {
                    $.unblockUI();
                    if (result.invoiced) {
                        add_inv_btn.addClass('d-none');
                    } else {
                        add_inv_btn.removeClass('d-none');
                        add_inv_btn.data('spid', pickid)
                    }
                }).catch(function () {
                    $.unblockUI();
                });
            }
        });

        $('td.td_add_invoice .b_add_invoice_buttom').click(function (event) {
            var button = $(event.target);
            var form_data = {}
            form_data = {
                'pid': button.data('pid'),
                'picking': button.data('spid'),
            }
            $.blockUI();
            ajax.jsonRpc('/create_invoice', 'call', { vals: form_data }).then(function (result) {
                var modal = $('#b_message_modal');
                modal.find('#b_title_response').text("Resultado");
                modal.find('#b_messages').html(result.message)
                if ('success' in result && result.success) {
                    $(event.target).closest('tr').find('.b_add_invoice_buttom').addClass('d-none');
                    setTimeout(function () {
                        location.reload();
                    }, 1000);
                }
                modal.css('display', 'block');
                $.unblockUI();
            }).catch(function () {
                $.unblockUI();
            });
        });
    });
});
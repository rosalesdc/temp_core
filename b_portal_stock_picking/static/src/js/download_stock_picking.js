odoo.define('b_portal_stock_picking', function (require) {
    "use strict";

    $(function () {
        $('td.td_picking_ids select.picking').change(function (evt) {
            var pickid = $(evt.target).val();
            var download_btn = $(evt.target).closest('tr').find('.b_download_delivery_slip');
            if (!pickid) {
                download_btn.addClass('d-none');
            } else {
                download_btn.removeClass('d-none');
                download_btn.data('pick_id', pickid);
            }
        });

        $('.b_download_delivery_slip').click(function (event) {
            var button = $(event.target);
            var pick_id = button.data('pick_id');
            window.open("/my/purchase/print/" + pick_id, '_self');
        });
    });
});
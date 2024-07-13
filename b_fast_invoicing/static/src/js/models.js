odoo.define('u_fast_invoicing.models', function(require) {
    "use strict";

    const { PosGlobalState, Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    var session = require('web.session');

    const AutoPostOrder = (Order) => class AutoPostOrder extends Order {
        // @Override
        constructor() {
            super(...arguments);
        }
        //@Override
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            var self = this;
            if(!self.invoicing_ref) {
                self.invoicing_ref = Math.random().toString(36).slice(2, 12);
            }
            var base_url = self.pos.config.domain || session['web.base.url'];
            json['invoicing_url'] = base_url + '/autofactura';
            json['invoicing_ref'] = self.invoicing_ref;
            self.invoicing_url = base_url + '/autofactura';
            console.log(json['invoicing_url']);
            return json;
        }
        // @Override
        export_for_printing() {
            const receipt = super.export_for_printing(...arguments);
            receipt.invoicing_ref = this.invoicing_ref;
            receipt.invoicing_url = this.invoicing_url;
            console.log(receipt.invoicing_url);
            return receipt;
        }
        
    }
    Registries.Model.extend(Order, AutoPostOrder);
});

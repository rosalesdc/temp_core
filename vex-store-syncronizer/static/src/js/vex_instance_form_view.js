/** @odoo-module */

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
const rpc = require('web.rpc');

class VexInstanceListController extends FormController {
    setup(){
        super.setup();

        let instance_id = this.props.resId

        if (!instance_id) {
            return;
        }
        
        rpc.query({
            model: "vex.instance",
            method: "get_status",
            args: [instance_id],
        }).then(function (result) {

            
            setTimeout(() => {

                const stepItems = document.querySelectorAll('.step-wizard-item');

                stepItems.forEach((stepItem, index) => {

                    if (index == result) {
                        stepItem.classList.add('current-item');
                    } else {
                        stepItem.classList.remove('current-item');
                    }
                });

            }, 100);

            
        }).catch(function (error) {
            console.error("Error al llamar a get_status: ", error);
        });
    }
}

export const vexIstanceFormView = {
    ...formView,
    Controller: VexInstanceListController,
};

registry.category("views").add("vex_instance_form_view", vexIstanceFormView);
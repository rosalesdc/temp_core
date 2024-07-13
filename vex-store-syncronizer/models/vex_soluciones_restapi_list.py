from odoo import api, fields, models, _

class VexRestapilist(models.Model):
    _name = "vex.restapi.list"
    _description = "List Vex RestApi"

    def _generate_count(self):
        for record in self:
            record.total_count = 0
        # for record in self:
        #     model = record.model
        #     if model:
        #         if model =='product.pricelist':
        #             count = self.env[str(model)].search_count([('server_meli', '!=', False)])
        #         else:
        #             count = self.env[str(model)].search_count([('server_meli', '!=', False), ('meli_code', '!=', False)])
        #         record.total_count = count
        #     else:
        #         record.total_count = 0

    name = fields.Char(required=True)
    argument = fields.Char()
    model = fields.Char()
    automatic = fields.Boolean()
    importv = fields.Boolean()
    export = fields.Boolean()

    # View from fields
    total_count = fields.Integer(compute='_generate_count')

    per_page = fields.Integer(default=10, required=True, string="Items per page")
    limit_action = fields.Integer(default=80, string="Limit Action")
    last_number_import = fields.Integer(default=0,string="Ultima Cantidad Importada")

    log_ids = fields.One2many('vex.meli.logs', 'vex_restapi_list_id', string='Logs')

    def go_export_product(self):
        name = _('Export Products to Mercadolibre')
        view_mode = 'form'        
        return {

            'name': name,

            'view_type': 'form',

            'view_mode': view_mode,

            'res_model':'vex.export.product.wizard',

            'type': 'ir.actions.act_window',

            'target': 'new',

        }

    def go_action_list(self):
        name = _('Close Shift')

        view_mode = 'tree,form'        
        return {

            'name': name,

            'view_type': 'form',

            'view_mode': view_mode,

            'res_model':self.model,

            'type': 'ir.actions.act_window',

            'target': 'current',

        }
    
    def clear_log(self):
        for log in self.log_ids:
            if log.action_type == 'Order':
                log.unlink()

    
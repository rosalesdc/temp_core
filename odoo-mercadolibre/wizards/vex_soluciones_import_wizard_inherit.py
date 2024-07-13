from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError

class VexSolucionesActionInherit(models.TransientModel):
    _inherit = "vex.import.wizard"
    
    store = fields.Selection(selection_add=[('mercadolibre', 'Mercadolibre')])
    action_mercadolibre = fields.Selection([('product', 'Product'),('category', 'Category'),('customer', 'Customer'),('order', 'Order'),('pricelist', 'Pricelist')],string="Action")
    
    meli_import_unit = fields.Boolean('Import Unit')
    meli_code_unit = fields.Char('Meli Code')
    
    # product
    meli_stock_import = fields.Boolean('Stock import')
    meli_import_images = fields.Boolean('Import images')
    meli_import_images_website = fields.Selection([
        ('save_url', 'Save url'),
        ('save_url_and_download', 'Save url and download')
    ], string='Import images website')

    # customer
    meli_date_from = fields.Datetime('Date from')
    meli_date_to = fields.Datetime('Date to')
    
    def synchronize(self):
        
        res = super(VexSolucionesActionInherit, self).synchronize()
        
        if self.store == 'mercadolibre':
            
            # Validando la accion a realizar
            if not self.action_mercadolibre:
                raise ValidationError("Selecting an action is mandatory.")
            
            if self.action_mercadolibre == "product":
                
                if not self.instance_id.meli_import_product:
                    raise ValidationError(f"'{self.instance_id.name}' instance cannot import products")
                
            if self.action_mercadolibre == "category":
                
                if not self.instance_id.meli_import_category:
                    raise ValidationError(f"'{self.instance_id.name}' instance cannot import categorys")
                
            if self.action_mercadolibre == "order":
                
                if not self.instance_id.meli_import_order:
                    raise ValidationError(f"'{self.instance_id.name}' instance cannot import orders")
                
            if self.action_mercadolibre == "pricelist":
                pass
            
            if self.action_mercadolibre == "customer":
                pass
            
        return res

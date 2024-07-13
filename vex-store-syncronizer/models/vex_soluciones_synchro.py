from odoo import fields, models, api

class VexSolucioensWooSynchro(models.Model):
    _name = "vex.synchro"
    
    def calculate_list_price(self, action, amount, type_amount, price):
        if action == 'increase':
            if type_amount == 'percentage':
                return price + (price * amount/100)
            else:
                return price + amount
        elif action == 'discount':
            if type_amount == 'percentage':
                return price - (price * amount/100)
            else:
                return price - amount
    
    def create_or_update_stock(self, product_id, location_id, stock_qty):
        try:
            existing_quant = self.env['stock.quant'].search([
                ('product_id', '=', product_id.id),
                ('location_id', '=', location_id.id)
            ])
            
            if existing_quant:
                existing_quant.write({'inventory_quantity': stock_qty})
                existing_quant.action_apply_inventory()
            else:
                self.env['stock.quant'].create({
                    'product_id': product_id.id,
                    'location_id': location_id.id,
                    'quantity': stock_qty,
                })
        except Exception as e:
            print(f"Error en create_or_update_stock: {e}")
    
    def get_stock_data(self, product_id, stock_qty):
        try:
            product_product_id = self.env['product.product'].search([('product_tmpl_id','=', product_id.id),('active','=',True)])
            location_id = self.env.ref('vex-store-syncronizer.general_stock')

            self.create_or_update_stock(product_product_id, location_id, stock_qty)
        except Exception as e:
            print(f"Error en get_stock_data: {e}")


    def expor_to_store(self):
        
        print("expor_to_store")
        
        # Obtengo config settings
        config_settings_id = self.env.ref('vex-store-syncronizer.vex_config_settigns')
        instances_ids = config_settings_id.export_to
        export_stock = config_settings_id.export_stock
        export_price = config_settings_id.export_price
        
        for instance_id in instances_ids:
            self.export_to_store_method(instance_id, export_stock, export_price)
        
    def export_to_store_method(self, instance_id, export_stock, export_price):
        pass
        
from odoo import models, fields, api

class VexSolucionesProductInherit(models.Model):
    _inherit = 'product.template'
    
    meli_server = fields.Boolean('Meli server')
    
    # Campos relacionados al producto de mercadolibre.
    meli_id = fields.Char('Id')
    meli_title = fields.Char('Title')
    meli_sku = fields.Char('Sku')
    meli_site_id = fields.Char('Site id')
    meli_seller_id = fields.Integer('Seller Id')
    meli_category_id = fields.Char('Category Id')
    
    meli_user_product_id = fields.Char('User Product Id')
    meli_official_store_id = fields.Char('Official Store Id')
    meli_price = fields.Float('Price')
    meli_base_price = fields.Float('Base Price')
    meli_original_price = fields.Char('Original Price')
    meli_inventory_id = fields.Char('Inventory Id')
    
    meli_currency_id = fields.Char('Currency Id')
    meli_initial_quantity = fields.Integer('Initial Quantity')
    meli_sold_quantity = fields.Integer('Sold Quantity')
    meli_warranty = fields.Char('Warranty')
    meli_buying_mode = fields.Char('Buying Mode')
    meli_listing_type_id = fields.Char('Listing Type Id')
    
    meli_condition = fields.Char('Condition')
    meli_permalink = fields.Char('Permalink')
    meli_thumbnail = fields.Char('Thumbnail')
    # pictures
    meli_accepts_mercadopago = fields.Boolean('Accepts Mercadopago')
    meli_mode = fields.Char('Mode')
    meli_free_shipping = fields.Boolean('Free Shipping')
    
    meli_logistic_type = fields.Char('Logistic Typ')
    # attributes
    meli_status = fields.Char('Status')
    # tags
    meli_catalog_product_id = fields.Char('Catalog Product Id')
    # channels
    
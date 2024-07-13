from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError
from .vex_soluciones_meli_config import COUNTRIES, CURRENCIES, COUNTRIES_DOMINIO
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class VexSolucinesInstaceInherit(models.Model):
    _inherit = "vex.instance"
    

    @api.onchange('store', 'meli_app_id', 'meli_redirect_uri', 'meli_country')
    def _onchange_field(self):
        if self.store == 'mercadolibre':
            if self.meli_app_id and self.meli_redirect_uri and self.meli_country:
                code_country = COUNTRIES_DOMINIO[self.meli_country]
                self.meli_url_get_server_code = 'https://auth.mercadolibre.com.{}/authorization?response_type=code&client_id={}&redirect_uri={}'.format(code_country, self.meli_app_id, self.meli_redirect_uri)
            else:
                self.meli_url_get_server_code = ""

    store = fields.Selection(selection_add=[('mercadolibre', 'Mercadolibre')])
    
    # Fields: 'Initial settings'
    meli_app_id = fields.Char('App ID')
    meli_secret_key = fields.Char('Secret Key')
    meli_redirect_uri = fields.Char('Redirect uri')
    meli_country = fields.Selection(COUNTRIES, string='Country')
    meli_default_currency = fields.Selection(CURRENCIES, string='Default Courrency')
    meli_nick = fields.Char('Nick')
    meli_user_id = fields.Char('User ID')

    # Fields: 'Keys'
    meli_url_get_server_code = fields.Char('Url Get Server Code')
    meli_server_code = fields.Char('Server Code')
    meli_access_token = fields.Char('Access Token')
    meli_refresh_token = fields.Char('Refresh Token')
    
    # Fields: 'Settings'
    meli_location_id = fields.Many2one('stock.location', string="Stock Location")
    meli_company = fields.Many2one('res.company', string='Company')
    meli_warehouse = fields.Many2one('stock.warehouse', string="Warehouse")
    meli_active_automatic = fields.Boolean(default=False, string="Activate automatic sync", readonly=True)
    
    meli_url_license = fields.Char(default='https://www.pasarelasdepagos.com/', required=True, string="Url License")
    meli_license_secret_key = fields.Char(default='587423b988e403.69821411', string="License Secret Key")
    meli_license_key = fields.Char("License Key")
    meli_registered_domain = fields.Char('Registered domain', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('web.base.url'))

    meli_import_product = fields.Boolean('Product', default=True)
    meli_import_order = fields.Boolean('Order', default=True)
    meli_create_invoice = fields.Boolean('Invoices')
    meli_invoice_status = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Invoices Status')
    meli_to_bring_order = fields.Selection([
        ('draft', 'Draft'),
        ('order', 'Order')
    ], string='to bring order?', default="draft")
    meli_import_category = fields.Boolean('Category', default=True)
    meli_export_product = fields.Boolean('Product', default=True)
    
    # Import price rule
    meli_behavior_price_rule = fields.Selection([
        ('just_in_creation', 'Just in creation'), # Solo en creacion
        ('creation_and_updating', 'Both, creation and updating')
    ], string='Behavior price rule', default="just_in_creation")
    meli_import_price_list = fields.Boolean('Allow price rule?')
    meli_import_increase_or_discount = fields.Selection([('increase', 'Increase'),('discount', 'Discount')], string='Increase/Discount')
    meli_import_type_amount = fields.Selection([('percentage', 'Percentage'),('fixed', 'Fixed')], string='Type amount')
    meli_import_amount = fields.Integer('Amount')
    
    # Export price rule
    meli_export_price_list = fields.Boolean('Allow price rule?')
    meli_export_increase_or_discount = fields.Selection([('increase', 'Increase'),('discount', 'Discount')], string='Increase/Discount')
    meli_export_type_amount = fields.Selection([('percentage', 'Percentage'),('fixed', 'Fixed')], string='Type amount')
    meli_export_amount = fields.Integer('Amount')
    meli_import_product_dropshipping = fields.Boolean('Dropshipping', default=True)
    
    def get_user(self):
        if not self.meli_nick:
            raise ValidationError('NOT NICK')
        if not self.meli_country:
            raise ValidationError('NOT COUNTRY')
        
        url_user = "https://api.mercadolibre.com/sites/{}/search?nickname={}".format(self.meli_country, self.meli_nick)
        
        item = requests.get(url_user).json()
        
        if 'seller' in item:
            self.meli_user_id = str(item['seller']['id'])
        else:
            raise ValidationError(f'INCORRECT NICK OR COUNTRY: {str(item)}')
    
    def get_token(self):
        if not self.meli_app_id:
            raise ValidationError('Not App ID')
        if not self.meli_secret_key:
            raise ValidationError('Not secret key')
        if not self.meli_redirect_uri:
            raise ValidationError('Not Redirect Uri')
        
        self.get_access_token()
        
    def get_access_token(self):
        
        url = 'https://api.mercadolibre.com/oauth/token?grant_type=authorization_code&client_id={}&client_secret={}&code={}&redirect_uri={}'.format(self.meli_app_id, self.meli_secret_key, self.meli_server_code, self.meli_redirect_uri)

        try:
            response = requests.post(url)
            if response.status_code == 200:
                json_obj = json.loads(response.text)
                if 'access_token' in json_obj:
                    self.write({
                        'meli_access_token': json_obj['access_token'],
                        'meli_refresh_token': json_obj['refresh_token'],
                    })
            else:
                _logger.error("response.content: %s", response.content)
                raise UserError("Credenciales invalidas.")
        except Exception as ex:
            raise UserError(f"Error al obtener el Access Token. \n'{str(ex)}'")
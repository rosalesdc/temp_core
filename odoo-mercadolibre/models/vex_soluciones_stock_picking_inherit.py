from odoo import models, fields, api
import requests
import base64
API_URI = 'https://api.mercadolibre.com'
PRINT_TICKET_URI = API_URI + '/shipment_labels?shipment_ids={}&response_type=pdf'

class VexSolucionesStockPickingInherit(models.Model):
    _inherit = 'stock.picking'


    def print_ticket(self):
        
        order_id = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f'Bearer {order_id.instance_id.meli_access_token}'}
     
        #Obtener el ticket
        print_uri = PRINT_TICKET_URI.format(self.vex_meli_shipment_id)
        response = requests.get(print_uri, headers=headers)
        
        print("response: ", response.content)
         
        # Save the PDF
        if response.status_code == 200:
            with open('prueba.pdf', "wb") as f:
                f.write(response.content)
                f.close()
            file = open("prueba.pdf", "rb")
            out = file.read()
            file.close()
            self.shipment_label = base64.b64encode(out)            
        else:
            print(response.status_code)
        return response.content    
    
    def compute_data_sale_order(self):
        for item in self:
            sale_order_origin = item.origin
            order_id = self.env['sale.order'].search([('name', '=', sale_order_origin)], limit=1)
            
            item.vex_meli_shipment_id = order_id.vex_meli_shipment_id
            item.vex_meli_shipment_type = order_id.vex_meli_shipment_type
            item.vex_meli_shipment_logistic_type =  order_id.vex_meli_shipment_logistic_type
            item.vex_meli_shipment_status = order_id.vex_meli_shipment_status
            item.vex_meli_shipment_listing_type = order_id.vex_meli_shipment_listing_type
    
    vex_meli_shipment_id = fields.Char('MELI Shipment Code', compute=compute_data_sale_order)
    vex_meli_shipment_type = fields.Char('MELI Shipment Type', compute=compute_data_sale_order)
    vex_meli_shipment_logistic_type = fields.Char('MELI Logistic Type', compute=compute_data_sale_order)
    vex_meli_shipment_status = fields.Char('MELI Shipment Status', compute=compute_data_sale_order)
    vex_meli_shipment_listing_type = fields.Char('MELIListing Type', compute=compute_data_sale_order)
    shipment_label = fields.Binary('Shipment Label', readonly=True)
    

from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime, time, date
import requests
import json
import logging
import urllib.parse

_logger = logging.getLogger(__name__)

GET_ORDER="https://api.mercadolibre.com/orders/search?seller={}&order.date_created.from={}&order.date_created.to={}&sort=date_desc&limit={}&offset={}"

class VexSolucionesSynchroInherit(models.Model):
    _inherit = "vex.synchro"
    
    def export_to_store_method(self, instance_id, export_stock, export_price):
        
        res = super(VexSolucionesSynchroInherit, self).export_to_store_method(instance_id, export_stock, export_price)
        
        if instance_id.store == 'mercadolibre':
            
            product_ids = self.env['product.template'].search([('instance_ids', 'in', [instance_id.id]), ('export_store', '=', True)])
            
            headers = {
                        "Content-Type": "application/json",
                        'Authorization': f'Bearer {instance_id.meli_access_token}'
                      }

            for product_id in product_ids:
                self.export_to_mercadolibre(product_id, instance_id, export_stock, export_price, headers)
        
        return res
    
    def export_to_mercadolibre(self, product_id, instance_id, export_stock, export_price, headers):
        if product_id.action_export == 'edit':
            
            obj={}
            
            quantity_id = self.env['stock.quant'].search([('product_id', '=', product_id.id)], limit=1)
            
            if export_stock:
                obj['available_quantity'] = quantity_id.quantity
            
            if export_price:
                
                # Obteniendo list price opciones
                import_price_list = instance_id.meli_export_price_list
                action = instance_id.meli_export_increase_or_discount
                type_amount =  instance_id.meli_export_type_amount 
                amount = instance_id.meli_export_amount
                
                try:
                    if not import_price_list:
                        obj['price'] = float(product_id.list_price)
                    else:
                        obj['price'] = self.calculate_list_price(action, amount, type_amount, float(product_id.list_price))
                except Exception as ex:
                    _logger.error("Log que fallo al extraer el list_price: %s", str(ex))
            
            try:
                url_export = f"https://api.mercadolibre.com/items/{product_id.meli_id}"
                response_item = requests.put(url_export, headers=headers, data=json.dumps(obj))

                if response_item.status_code == 200:
                    _logger.info("El producto se exporto con exito")
                    
            except Exception as ex:
                _logger.error("Error en export_to_mercadolibre: %s", str(ex))
            
        
    def validate_meli_token(self, instancia_id):
        
        obj = {
            'success': False,
            'msg': '',
        }
        
        headers = {
                        'Content-Type': "Content-Type: application/json",
                        'Authorization': f'Bearer {instancia_id.meli_access_token}'
                    }
        
        url_validate = "https://api.mercadolibre.com/sites/MLA/categories"
        
        validated_request = requests.get(url=url_validate, headers=headers)
  
        if validated_request.status_code == 401 or validated_request.status_code != 200:
            validate_token = self.get_access_token(instancia_id)
            
            if not validate_token:
                obj['success'] = False
                obj['msg'] = "unauthorized - invalid access token" + " " +  instancia_id.name
            else:
                obj['success'] = True
        
        if validated_request.status_code == 200:
            obj['success'] = True
            
        return obj
    
    def get_access_token(self, instance_id):
        url = 'https://api.mercadolibre.com/oauth/token?grant_type=client_credentials&client_id={}&client_secret={}'.format(instance_id.meli_app_id, instance_id.meli_secret_key)

        try:
            response = requests.post(url)
            if response.status_code == 200:
                json_obj = json.loads(response.text)
                if 'access_token' in json_obj:
                    self.write({
                        'meli_access_token': json_obj['access_token']
                    })
                    return True
            else:
                return False
        except Exception as ex:
           return False
        
    def import_meli_products(self):
        
        instance_ids = self.env['vex.instance'].search([('store', '=', 'mercadolibre'), ('meli_import_product', '=', True), ('meli_active_automatic', '=', True)])

        for instance_id in instance_ids:

            validate_token = self.validate_meli_token(instance_id)
            
            if not validate_token['success']:
                _logger.error("Failed to refresh token, check credentials.")
                continue
            
            headers = {
                        'Content-Type': "Content-Type: application/json",
                        'Authorization': f'Bearer {instance_id.meli_access_token}'
                    }
            
            self.get_product_sku(instance_id.meli_user_id, headers, instance_id)
            
    def get_product_sku(self, data, headers, instance_id):
        
        limit = 100
        offset = 0
        total = 500
        
        while(total >= offset):
            
            url_sku = f"https://api.mercadolibre.com/users/{data}/items/search?limit={limit}&offset={offset}"
            
            try:
                response = requests.get(url_sku, headers=headers)
            except Exception as ex:
                # Log error al consumir producto
                _logger.error("Log error al consumir producto: %s", ex)
                break
            
            if response.status_code != 200:
                # Log request diferente a 200
                break
            
            if response.status_code == 200:
                
                json_sku = json.loads(response.text)
                
                skus = json_sku['results']
                
                for sku in skus:
                    self.get_product_by_sku(sku, headers, instance_id)
                
                # Paginacion
                total = json_sku['paging']['total']
                offset += limit
            
            # print("total: ", total)
            # print("offset: ", offset)
               
    def get_product_by_sku(self, sku, headers, instance_id):
        
        # Armando url
        url_item = f"https://api.mercadolibre.com/items?ids={sku}"
        
        try:
            response_item = requests.get(url_item, headers=headers)
        except Exception as ex:
            # Log error al consumir producto by sku
            _logger.error("Log error al consumir producto by sku: %s", ex)
            pass
            
        if response_item.status_code != 200:
            # Log request diferente a 200
            _logger.error("get_product_by_sku: Log request diferente a 200")
            pass
        else:
            items = json.loads(response_item.text)
            
            for item in items:
                
                if item['code'] != 200:
                    # Log request diferente a 200 en resultado de producto
                    _logger.error("Log request diferente a 200 en resultado de producto: %s", item)
                    break
                
                # Obteniendo SKU
                has_sku = False
                value_sku = ''
                # obtener opcion de dropshipping
                # Atributos de mercadolibre libre
                attributes = []
                
                try:
                    for attribute in item['body']['attributes']:
                        if attribute['id'] == 'SELLER_SKU':
                            has_sku = True
                            value_sku = attribute['value_name']
                        else:
                            attributes.append({
                                'name': attribute['name'], 
                                'meli_code': attribute['id'], 
                                'value_name': attribute['value_name']
                            })
                except Exception as ex:
                    # Log error al crear objeto por el sku
                    _logger.error("Error en el sku %s", ex)
                    continue
                
                # Obteniendo list price opciones
                import_price_list = instance_id.meli_import_price_list
                action = instance_id.meli_import_increase_or_discount
                type_amount =  instance_id.meli_import_type_amount 
                amount = instance_id.meli_import_amount
                
                try:
                    if not import_price_list:
                        price = float(item['body']['price'])
                    else:
                        price = self.calculate_list_price(action, amount, type_amount, float(item['body']['price']))
                except Exception as ex:
                    _logger.error("Log que fallo al extraer el list_price:%s", str(ex))
                    continue
                
                obj = {}
                
                try:
                    obj['meli_id'] = item['body']['id']
                    obj['meli_site_id'] = item['body']['site_id']
                    obj['meli_title'] = item['body']['title']
                    obj['meli_seller_id'] = item['body']['seller_id']
                    obj['meli_sku'] = value_sku if has_sku else None
                    obj['default_code'] = value_sku if has_sku else None
                    obj['meli_category_id'] = item['body']['category_id']
                    obj['meli_user_product_id'] = item['body']['user_product_id']
                    obj['meli_official_store_id'] = item['body']['official_store_id']
                    obj['meli_price'] = price
                    obj['meli_base_price'] = item['body']['base_price']
                    obj['meli_original_price'] = item['body']['original_price']
                    obj['meli_inventory_id'] = item['body']['inventory_id']
                    obj['meli_currency_id'] = item['body']['currency_id']
                    obj['meli_initial_quantity'] =  item['body']['initial_quantity']
                    obj['meli_sold_quantity'] = item['body']['available_quantity']
                    obj['meli_warranty'] = item['body']['warranty']
                    obj['meli_buying_mode'] = item['body']['buying_mode']
                    obj['meli_listing_type_id'] = item['body']['listing_type_id']
                    obj['meli_condition'] = item['body']['condition']
                    obj['meli_permalink'] = item['body']['permalink']
                    obj['meli_thumbnail'] = item['body']['thumbnail']
                    obj['meli_accepts_mercadopago'] =  item['body']['accepts_mercadopago']
                    obj['meli_mode'] = item['body']['shipping']['mode']
                    obj['meli_free_shipping'] = item['body']['shipping']['free_shipping']
                    obj['meli_logistic_type'] = item['body']['shipping']['logistic_type']
                    obj['meli_status'] = item['body']['status']
                    obj['meli_catalog_product_id'] = item['body']['catalog_product_id']
                    obj['detailed_type'] = 'product'
                    obj['action_export'] = 'edit'
                    obj['meli_server'] = True
                except Exception as ex:
                    # Log error de creacion de producto
                    _logger.error("Log error de armar objeto de producto: %s", ex)
                    continue
                    
                domain = []
                
                domain.append(('active', '=', True)) # Para traer productos no archivados
                
                
                if has_sku:
                    domain.append(('default_code', '=',  value_sku))
                else:
                    domain.append(('meli_id', '=',  item['body']['id']))
                                        
                # Instanciando product_id
                product_id = False
                config_settings_id = self.env.ref('vex-store-syncronizer.vex_config_settigns')
                    
                # Buscamos productos
                existing_product = self.env['product.template'].search(domain)
                
                # Validacion de producto si se crea o actualiza
                if not existing_product:
                    
                    # print("No existe producto")

                    # Agregamdp campos obligatorios al crear el producto
                    obj['name'] = item['body']['title']
                    obj['list_price'] = price
                    obj['instance_ids'] = [(4, instance_id.id)]
                    # obj['attribute_line_ids'] = attribute_value_tuples
                    
                    try:
                        product_id = self.env['product.template'].create(obj)
                    except Exception as ex:
                        # Log error al crear producto
                        _logger.error("Log error al crear producto: %s", ex)
                        continue
                    
                    try:
                        # create_product = existing_product.write(obj)
                        if product_id: # Validando si esta creado
                            product_id = product_id
                            publications = self.env['vex.product.publications'].search([('publication_id','=',item['body']['id'])])

                            if not publications:

                                publication_values = {
                                    'product_id': product_id.id,
                                    'publication_id': item['body']['id'],
                                    'publication_description': item['body']['title'],
                                    'publication_url': item['body']['permalink'],
                                    'publication_type': item['body']['listing_type_id'],
                                    'publication_category': item['body']['category_id'],
                                    'publication_price': price
                                }
                                self.env['vex.product.publications'].create(publication_values)
                    except Exception as ex:
                        # Log error al actualizar producto
                        _logger.error("Log error al actualizar producto: %s", ex)
                        continue
                        
                    if instance_id.id == config_settings_id.instance_id.id:
                        if config_settings_id.frequency == 'once':
                            
                            if 'available_quantity' in item['body'] and item['body']['available_quantity'] is not None:
                                _logger.info("Listo para actualizar stock:")
                                stock_qty = item['body']['available_quantity']
                                self.get_stock_data(product_id, stock_qty)    
                    
                else:
                    
                    # print("Existe producto")
                    
                    if not existing_product.meli_server:
                        
                        # Comprobar primero si el ID ya está presente
                        if instance_id not in existing_product.instance_ids:
                            obj['instance_ids'] =  [(4, instance_id.id)]
                        
                        producto_actualizado = existing_product.write(obj)
                    
                    # Validando el precio
                    if instance_id.meli_behavior_price_rule == 'creation_and_updating':
                        obj['list_price'] = price
                    
                    # Obteniendo ids de indstance ids de product
                    current_ids = existing_product.instance_ids.ids
                    
                    try:
                        
                        if existing_product and existing_product.meli_id == item['body']['id']:
                            
                            validation_existing_product = existing_product.write(obj)
                            
                            if instance_id.id == config_settings_id.instance_id.id:
                                if config_settings_id.frequency == 'always':
                                    
                                    if 'available_quantity' in item['body'] and item['body']['available_quantity'] is not None:
                                        _logger.info("Listo para actualizar stock:")
                                        stock_qty = item['body']['available_quantity']
                                        self.get_stock_data(existing_product, stock_qty)
                            
                            
                        if existing_product: # Validando si esta creado
                            product_id = existing_product
                            publications = self.env['vex.product.publications'].search([('publication_id','=',item['body']['id'])])

                            if not publications:

                                publication_values = {
                                    'product_id': existing_product.id,
                                    'publication_id': item['body']['id'],
                                    'publication_description': item['body']['title'],
                                    'publication_url': item['body']['permalink'],
                                    'publication_type': item['body']['listing_type_id'],
                                    'publication_category': item['body']['category_id'],
                                    'publication_price': price
                                }
                                self.env['vex.product.publications'].create(publication_values)
                    except Exception as ex:
                        # Log error al actualizar producto
                        _logger.error("Log error al actualizar producto: %s", ex)
                        continue
    
    def validation_licence_mercadolibre(self):
        instace_ids = self.env['vex.instance'].search([('store', '=', 'mercadolibre')])
        for instace_id in instace_ids:
            self.license_key(instace_id)

    def extract_domain(self, url):
        parsed_url = urllib.parse.urlparse(url)
        return parsed_url.netloc    
    
    def license_key(self, instance_id):
        
        # print("=================================")
        
        if not instance_id.meli_url_license or not instance_id.meli_license_key or not instance_id.meli_license_secret_key:
            _logger.error("Ingrese todos los datos.")
            instance_id.meli_active_automatic = False
            return
        
        URL = f"{instance_id.meli_url_license}?license_key={instance_id.meli_license_key}&slm_action=slm_check&secret_key={instance_id.meli_license_secret_key}&registered_domain={self.extract_domain(instance_id.meli_registered_domain)}"

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        try:
            r = requests.get(url=URL, headers=headers)
            r.raise_for_status()  # Raise an error for non-200 status codes
            response_json = r.json()  # Try to parse JSON
        except requests.exceptions.RequestException as e:
            _logger.error("Error making request: %s", e)
            instance_id.meli_active_automatic = False
            return
        except json.JSONDecodeError as e:
            _logger.error("Error decoding JSON response: %s", e)
            _logger.error("Response content: %s", r.text)
            instance_id.meli_active_automatic = False
            return

        _logger.info("response_json: %s", response_json)
        
        # Check if the response contains the expected keys
        if 'result' in response_json:
            if response_json['result'] != 'success':
                _logger.info("False")
                instance_id.meli_active_automatic = False
            else:
                _logger.info("True")
                instance_id.meli_active_automatic = True
        else:
            _logger.info("Else False")
            instance_id.meli_active_automatic = False
    
    def import_meli_orders(self):
        
        instance_ids = self.env['vex.instance'].search([('store', '=', 'mercadolibre'), ('meli_import_order', '=', True), ('meli_active_automatic', '=', True)])
        instance_ids_with_invoice = self.env['vex.instance'].search([('store', '=', 'mercadolibre'), ('meli_import_order', '=', True), ('meli_active_automatic', '=', True),('meli_create_invoice', '=', True)])

        if instance_ids:
        # Recorremos las instancias obtenidas
            for instance_id in instance_ids:
                
                validate_token = self.validate_meli_token(instance_id)
                
                if not validate_token['success']:
                    _logger.error("Failed to refresh token, check credentials.")
                    continue
                
                # Validacion
                there_is_orders= True
                
                # Datos
                limit = 20 
                current_page = 1
                counter = 0
                
                # Fechas de ordenes 24 hrs
                fecha_before_formate = ""
                fecha_after_formate = ""
                
                try:
                    # Obtener la fecha actual
                    fecha_actual = datetime.now().date()

                    # Crear objetos datetime con la hora ajustada
                    fecha_before = datetime.combine(fecha_actual, time.min)
                    fecha_after = datetime.combine(fecha_actual, time.max)
                    
                    fecha_before_formate = fecha_before.strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
                    fecha_after_formate= fecha_after.strftime("%Y-%m-%dT%H:%M:%S.000-00:00")
                    
                except Exception as ex:
                    _logger.error("Error al obtener fecha:%s", ex)
                    
                headers = {
                            "Content-Type": "application/json",
                            'Authorization': f'Bearer {instance_id.meli_access_token}'
                        }

                while(there_is_orders):
                    
                    # Paginacion
                    offset = (current_page - 1) * limit
                    
                    # Obteniendo url para ordenes
                    url_orders = GET_ORDER.format(instance_id.meli_user_id, fecha_before_formate, fecha_after_formate, limit,offset)
                    
                    response_item = requests.get(url_orders, headers=headers)
                    
                    if response_item.status_code != 200:
                        _logger.error("Fallo al consumir el resquest de ordernes")
                        _logger.error("response_item.status:%s", response_item.status_code)
                        _logger.error("response_item.content:%s", response_item.content)
                        there_is_orders = False
                        break
                    
                    json_orders = json.loads(response_item.text)
        
                    data = json_orders["results"]
                    if len(data) == 0:
                        _logger.info("No tiene contenido")
                        there_is_orders = False
                        break
                    
                    for order in data:
                        _logger.info("Order:%s", order)
                        
                        #Si la orden existe, no hago nada y paso a la siguiente                
                        sale_order_exist = self.env['sale.order'].search([('meli_code', '=', order['id'])], limit=1)
                        
                        if sale_order_exist:
                            _logger.error("La orden ya existe:%s", str(sale_order_exist))
                            continue
                        
                        # Variables de shipping
                        meli_shipment_id = ""
                        meli_shipment_status= ""
                        meli_shipment_type = ""
                        
                        #Traigo Info del shipping si existe 
                        if order['shipping']['id'] != None:
                            url_shipment = f"https://api.mercadolibre.com/shipments/{order['shipping']['id']}"
                            response_shipment = requests.get(url_shipment, headers=headers)
                            if response_shipment.status_code == 200:
                                json_shipment = json.loads(response_shipment.text)
                                meli_shipment_id = json_shipment['id']
                                meli_shipment_type= json_shipment['logistic_type']  if 'logistic_type' in json_shipment else ""
                                meli_shipment_status = json_shipment['status']     
                        else: #Sino, es nor delivered    
                            meli_shipment_status = "Not Delivered"
                        
                        # Obteniendo informacion de Cliente
                        data_name = ""
                        data_lastname = ""
                        data_street = ""
                        data_ruc = ""
                        data_country = ""
                        document_type_id = False
                        
                        try:
                            #Busco al cliente
                            RUT_URI="https://api.mercadolibre.com/orders/{}/billing_info"
                            url_rut = RUT_URI.format(order["id"])
                            json_billing = requests.get(url_rut, headers = headers)
                            
                            if json_billing.status_code != 200:
                                _logger.error("Log no se pudo obtener la información de facturación:%s", json_billing.content)
                                continue
                            
                            billing = json.loads(json_billing.text)
                            
                            _logger.info("billing:%s", billing)
                            
                            document_type = billing['billing_info']['doc_type'] 
                            document_type_id = self.env['l10n_latam.identification.type'].search([('name','=', document_type)])
                            for data in billing["billing_info"]["additional_info"]:
                                if data["type"] == "DOC_NUMBER":
                                    data_ruc = data["value"]
                                if document_type =='DNI':
                                    if data["type"] == "FIRST_NAME":
                                        data_name = data["value"]
                                    if data["type"] == "LAST_NAME":
                                        data_name = data_name + " " + data["value"]
                                else: 
                                    if data["type"] == "BUSINESS_NAME":
                                        data_name = data["value"] 
                                if data["type"] == "DOC_NUMBER":
                                    data_ruc = data["value"]                                                                                                            
                                if data["type"] == "COUNTRY_ID":
                                    data_country = data["value"]
                        except Exception as ex:
                            _logger.error("Error Buscar al cliente:%s", ex)
                            continue
                        
                        # Inizializacion variables partner
                        partner_id = False
                        
                        #Busco al cliente
                        partner_exist = self.env["res.partner"].search([('vat','=', data_ruc)],limit=1)
                        country_id = self.env['res.country'].search([('code','=',data_country)])
                        
                        #Si no existe, lo creo
                        if len(partner_exist) == 0 :
                            try:
                                obj={}
                                obj["name"]= data_name if data_name else "Anónimo"
                                #obj["lastname"]= data_lastname
                                obj["vat"]= data_ruc
                                obj["street"]= data_street
                                obj["l10n_latam_identification_type_id"]=1
                                # obj["server_meli"]=True
                                # obj["meli_code"]=data_ruc
                                obj["country_id"]=country_id.id if country_id else None,
                                obj['l10n_latam_identification_type_id'] = document_type_id.id
                                obj['meli_server']=True

                            except Exception as ex:
                                _logger.error("Error al la creacion de objeto de cliente:%s", str(ex))
                                continue
                            
                            try:
                                partner_id = self.env['res.partner'].create(obj)
                            except Exception as ex:
                                _logger.error("Error al crear el cliente:%s", str(ex))
                                continue
                            
                            try:                       
                                            
                                # Creación del contacto de facturación
                                obj_billing_partner = {
                                    'name': data_name,
                                    'street': data_street,
                                    'parent_id': partner_id.id,
                                    "country_id": country_id.id if country_id else None,
                                    'type': 'invoice'
                                }
                                
                                billing_partner_id = self.env['res.partner'].create(obj_billing_partner)
                                
                                # Consumiendo shiping
                                url_shipments = f"https://api.mercadolibre.com/shipments/{str(order['shipping']['id'])}"
                                json_shipments = requests.get(url_shipments, headers = headers)
                                if json_shipments.status_code == 200:
                                    
                                    shipments = json.loads(json_shipments.text)
                                    
                                    obj_shipping_partner = {
                                        'name': shipments['receiver_address']['receiver_name'],
                                        'street': shipments['receiver_address']['street_name'],
                                        'city': shipments['receiver_address']['city']['name'],
                                        'zip': shipments['receiver_address']['zip_code'],
                                        "country_id": country_id.id if country_id else None,
                                        'parent_id': partner_id.id,
                                        'type': 'delivery'
                                    }
                                    
                                    shipping_partner_id = self.env['res.partner'].create(obj_shipping_partner)
                                
                            except Exception as ex:
                                _logger.error("Error al crear los hijos:%s", ex)
                        else:
                            partner_id = partner_exist
                        
                        # print("partner_id: ", partner_id)
                        
                        # Validacion si el producto no existe.
                        existing_product = False
                        
                        product_id = False
                        
                        
                        # Instanciando lista de ordenes
                        obj_line_order = []
                        
                        for item in order['order_items']:
                            
                            _logger.info("Identificador de producto: %s", item['item']['id'])
                            
                            publication_id = self.env['vex.product.publications'].search([('publication_id', '=', item['item']['id'])])
                        
                            if publication_id:
                                product_id = publication_id.product_id
                            
                            # Si no existe el producto deberia parar
                            if not product_id:
                                existing_product = True
                                _logger.info("producto no existe")
                                break    
                            
                            product_product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_id.id)], limit=1)
                            
                            try:
                                obj_line_order.append((0,0,{
                                    'product_id': product_product_id.id,
                                    'product_template_id': product_id.id,
                                    'name': product_id.name,
                                    'display_type': False,
                                    'product_uom_qty': int(item['quantity']),
                                    'price_unit': float(item['unit_price']),
                                    'price_subtotal': float(item['quantity'] * item['unit_price']),
                                    'tax_id':[]
                                }))
                            except Exception as ex:
                                _logger.error("Erro al armar linea de orden:%s", str(ex))
                            
                        
                        if not existing_product: # Creando orden
                            
                            obj_order = {}
                            
                            try:
                                payments_list=[]
                                for payment in order['payments']:
                                    try:
                                        obj_payment ={}
                                        obj_payment['meli_payment_id'] = str(payment['id'])
                                        obj_payment['meli_payment_reason'] = payment['reason']
                                        obj_payment['meli_payment_status_code'] = payment['status_code']
                                        obj_payment['meli_payment_total_paid_amount'] = payment['total_paid_amount']
                                        obj_payment['meli_payment_operation_type'] = payment['operation_type']
                                        obj_payment['meli_payment_transaction_amount'] = payment['transaction_amount']
                                        obj_payment['meli_payment_date_approved'] = str(payment['date_approved']).strftime('%Y-%m-%d %H:%M:%S') if payment['date_approved'] else False
                                        obj_payment['meli_payment_collector_id'] = str(payment['collector']['id'])
                                        obj_payment['meli_payment_coupon_id'] = payment['coupon_id']
                                        obj_payment['meli_payment_installments'] = payment['installments']
                                        obj_payment['meli_payment_authorization_code'] = payment['authorization_code']
                                        obj_payment['meli_payment_taxes_amount'] = payment['taxes_amount']
                                        obj_payment['meli_payment_date_last_modified'] = payment['date_last_modified']
                                        obj_payment['meli_payment_coupon_amount'] = payment['coupon_amount']
                                        # obj_payment['meli_payment_available_actions_ids'] = payment['']
                                        obj_payment['meli_payment_shipping_cost'] = payment['shipping_cost']
                                        obj_payment['meli_payment_installment_amount'] = payment['installment_amount']
                                        obj_payment['meli_payment_date_created'] = payment['date_created']
                                        obj_payment['meli_payment_activation_uri'] = payment['activation_uri']
                                        obj_payment['meli_payment_overpaid_amount'] = payment['overpaid_amount']
                                        obj_payment['meli_payment_card_id'] = str(payment['card_id'])
                                        obj_payment['meli_payment_status_detail'] = payment['status_detail']
                                        obj_payment['meli_payment_issuer_id'] = payment['issuer_id']
                                        obj_payment['meli_payment_method_id'] = payment['payment_method_id']
                                        obj_payment['meli_payment_type_id'] = payment['payment_type']
                                        obj_payment['meli_payment_deferred_period'] = payment['deferred_period']
                                        obj_payment['meli_payment_atm_transfer_ref_transaction_id'] = payment['atm_transfer_reference']['transaction_id']
                                        obj_payment['meli_payment_atm_transfer_ref_company'] = payment['atm_transfer_reference']['company_id']
                                        obj_payment['meli_payment_site_id'] = payment['site_id']
                                        obj_payment['meli_payment_payer_id'] = (payment['payer_id'])
                                        # obj_payment['meli_payment_marketplace_fee'] = payment['']
                                        # obj_payment['meli_payment_order_code'] = payment['']
                                        # obj_payment['meli_payment_order_id'] = payment['']
                                        obj_payment['meli_payment_currency_id'] = payment['currency_id']
                                        obj_payment['meli_payment_status'] = payment['status']
                                        obj_payment['meli_payment_transaction_order_id'] = payment['transaction_order_id']
                                        
                                    except Exception as ex:
                                        _logger.error("Error al armar el objeto payment: %s", str(ex))
                                        
                                    try:
                                        # print("obj_payment: ", obj_payment)
                                        
                                        payments_id = self.env['vex.meli.payments'].create(obj_payment)
                                        if payments_id:
                                            payments_list.append(payments_id.id)
                                    except Exception as ex:
                                        _logger.error("Erro al crear en meli_payments:%s", str(ex)) 
                                    
                                date_order = False
                                
                                _logger.info("payments_list:%s", payments_list)
                                
                                if order['date_created']:
                                    formatted_time = datetime.strptime(order['date_created'], '%Y-%m-%dT%H:%M:%S.%f%z') 
                                    date_order = formatted_time.strftime('%Y-%m-%d %H:%M:%S')
                                    
                                # Consumiendo shiping
                                url_shipments = f"https://api.mercadolibre.com/shipments/{str(order['shipping']['id'])}"
                                json_shipments = requests.get(url_shipments, headers = headers)
                                if json_shipments.status_code == 200:
                                    
                                    shipments = json.loads(json_shipments.text)

                                    obj_order['vex_meli_shipment_id']  = shipments['id']
                                    # obj_order['vex_meli_shipment_type'] = shipments
                                    obj_order['vex_meli_shipment_logistic_type'] = shipments['logistic_type']  if 'logistic_type' in json_shipment else ""
                                    obj_order['vex_meli_shipment_status'] = shipments['status'] 
                                    # obj_order['vex_meli_shipment_listing_type'] =
                                
                                obj_order['meli_code'] = str(order['id'])
                                obj_order['date_order'] = date_order
                                obj_order['order_line'] = obj_line_order
                                obj_order['partner_id'] = partner_id.id

                                obj_order['meli_order_seller_id'] = str(order['seller']['id'])
                                obj_order['meli_order_seller_nickname'] = order['seller']['nickname']
                                obj_order['meli_order_payment_ids'] = [(6, 0, payments_list)] if payments_list else False
                                obj_order['meli_order_fulfilled'] = order['fulfilled']
                                #obj_order['meli_order_buying_mode'] = order['buying_mode']
                                obj_order['meli_order_expiration_date'] = datetime.strptime(order['expiration_date'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d %H:%M:%S')
                                obj_order['meli_order_feedback_sale'] = order['feedback']['buyer']
                                obj_order['meli_order_feedback_purchase'] = order['feedback']['seller']
                                obj_order['meli_order_shipping_id'] = str(order['shipping']['id'])
                                obj_order['meli_order_date_closed'] = datetime.strptime(order['date_closed'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d %H:%M:%S')
                                #obj_order['meli_order_manufacturing_ending_date'] = datetime.strptime(order['manufacturing_ending_date'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d %H:%M:%S')
                                #obj_order['meli_order_hidden_for_seller'] = order['hidden_for_seller']
                                obj_order['meli_order_last_updated'] = datetime.strptime(order['last_updated'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d %H:%M:%S')
                                #obj_order['meli_order_comments'] = order['comments']
                                obj_order['meli_order_pack_id'] = order['pack_id']
                                obj_order['meli_order_coupon_id'] = order['coupon']['id']
                                obj_order['meli_order_coupon_amount'] = order['coupon']['amount']
                                obj_order['meli_order_shipping_cost'] = order['shipping_cost']
                                obj_order['meli_order_date_created'] = datetime.strptime(order['date_created'], '%Y-%m-%dT%H:%M:%S.%f%z').strftime('%Y-%m-%d %H:%M:%S')
                                #obj_order['meli_order_application_id'] = order['application_id']
                                obj_order['meli_order_pickup_id'] = order['pickup_id']
                                obj_order['meli_order_status_detail'] = order['status_detail']
                                #obj_order['meli_order_tag_ids'] = order['meli_order_tag_ids']
                                obj_order['meli_order_buyer_id'] = str(order['buyer']['id'])
                                obj_order['meli_order_buyer_nickname'] = order['buyer']['nickname']
                                obj_order['meli_order_total_amount'] = order['total_amount']
                                obj_order['meli_order_paid_amount'] = order['paid_amount']
                                obj_order['meli_order_currency_id'] = order['currency_id']
                                obj_order['meli_order_status'] = order['status']
                                obj_order['meli_order_context_application'] = order['context']['application']
                                obj_order['meli_order_context_product_id'] = order['context']['product_id']
                                obj_order['meli_order_context_channel'] = order['context']['channel']
                                obj_order['meli_order_context_site'] = order['context']['site']
                                obj_order['meli_server'] = True
                                obj_order['instance_id'] = instance_id.id

                                #obj_order['meli_order_context_channel'] = order['context']['channel']
                                #obj_order['meli_order_context_site'] = order['context']['site']
                                #obj_order['meli_order_context_flows'] = order['context']['flows']
                                _logger.info("Objeto order:%s",obj_order)
                            except Exception as ex:
                                _logger.error("Error al armar el objeto de la orden:%s", ex)
                                continue
                            
                            order_id = False
                            
                            try:
                                order_id =self.env['sale.order'].create(obj_order)
                            except Exception as ex:
                                _logger.error("Erro al crear la orden:%s", ex)
                                continue
                            
                            try:
                                if order_id and instance_id.meli_to_bring_order == 'order':
                                    
                                    order_id.action_confirm()
                                    stock_id = self.env['stock.picking'].search([('origin', '=', order_id.name)], limit=1)
                                    _logger.info('MELICREATEINVOICE%s',instance_id.meli_create_invoice)
                                    _logger.info('MELIINVOICESTATUS%s',instance_id.meli_invoice_status)
                                    _logger.info('2222222222222222%s',instance_id.meli_create_invoice and instance_id.meli_invoice_status == 'draft')
                                    
                                    if instance_id.meli_create_invoice and instance_id.meli_invoice_status == 'draft':
                                        try:
                                            order_id._create_invoices(self, final=False, date=None)
                                        except Exception as ex:
                                            _logger.error("Error al crear la factura:%s", ex)
                                    if instance_id.meli_create_invoice and instance_id.meli_invoice_status == 'done':
                                        try:
                                            invoices = order_id._create_invoices(self, final=False, date=None)
                                            for invoice in invoices:
                                                invoice.action_post()
                                        except Exception as ex:
                                            _logger.error("Error al crear la factura:%s", ex)

                                    if stock_id:
                                        
                                        immediate_transfer_line_ids = []
                                        
                                        for picking in stock_id:
                                            immediate_transfer_line_ids.append([0, False, {
                                            'picking_id': picking.id,
                                            'to_immediate': True}
                                            ])
                                        
                                        res = self.env['stock.immediate.transfer'].create({
                                                'pick_ids': [(4, p.id) for p in stock_id],
                                                'show_transfers': False,
                                                'immediate_transfer_line_ids': immediate_transfer_line_ids
                                            })
                                        
                                        res.with_context(button_validate_picking_ids=res.pick_ids.ids).process()                                    
                            except Exception as ex:
                                _logger.error("Error al manipular el stock:%s", ex)
                                continue

                        _logger.info("===================================D")
                        _logger.info(order)
                        _logger.info("===================================D")
                    
                    current_page += 1

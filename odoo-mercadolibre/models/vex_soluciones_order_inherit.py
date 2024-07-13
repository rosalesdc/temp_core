from odoo import api, fields, models

class VexSolucionesOrderInherit(models.Model):
    _inherit = "sale.order"
    
    meli_code = fields.Char('MELI Code')
    meli_server = fields.Boolean('Meli server')
    meli_order_seller_id = fields.Char('Seller ID')
    meli_order_seller_nickname = fields.Char('Seller Nickname')
    meli_order_payment_ids = fields.One2many('vex.meli.payments', 'meli_payment_order_id', string='field_name')
    meli_order_fulfilled = fields.Boolean('Fulfilled?')
    meli_order_expiration_date = fields.Datetime('Expiration Date')
    meli_order_feedback_sale = fields.Char('Feedback Sale')
    meli_order_feedback_purchase = fields.Char('Feedback Purchase')
    meli_order_shipping_id = fields.Char('Shipping ID')
    meli_order_date_closed = fields.Datetime('MELI Date Closed')
    meli_order_date_last_updated = fields.Datetime('Date Last Update')
    meli_order_last_updated = fields.Datetime('Last Update')
    meli_order_pack_id = fields.Char('Pack ID')
    meli_order_coupon_id = fields.Char('Coupon ID')
    meli_order_coupon_amount = fields.Char('Coupon Amount')
    meli_order_shipping_cost = fields.Float('Shipping Cost')
    meli_order_date_created = fields.Datetime('MELI Date Created')
    meli_order_pickup_id = fields.Char('Pickup ID')
    meli_order_status_detail = fields.Char('MELI Order Status Detail')
    meli_order_tag_ids = fields.Many2many('vex.meli.order.tag', string='Order Tags')
    meli_order_buyer_id = fields.Char('Buyer ID')
    meli_order_buyer_nickname = fields.Char('Buyer Nickname')
    meli_order_total_amount = fields.Float('Total Amount')
    meli_order_paid_amount = fields.Float('Paid Amount')
    meli_order_currency_id = fields.Char('Currency')
    meli_order_status = fields.Char('MELI Order Status')
    meli_order_context_application = fields.Char('Context Application')
    meli_order_context_product_id = fields.Char('Context Product')
    meli_order_context_channel = fields.Char('Context Channel')
    meli_order_context_site = fields.Char('Context Site')
    
    vex_meli_shipment_id = fields.Char('MELI Shipment Code')
    vex_meli_shipment_type = fields.Char('MELI Shipment Type')
    vex_meli_shipment_logistic_type = fields.Char('MELI Logistic Type')
    vex_meli_shipment_status = fields.Char('MELI Shipment Status')
    vex_meli_shipment_listing_type = fields.Char('MELIListing Type')
    


class VexSolucionesMeliPaymentsAvailableAction(models.Model):
    _name="vex.meli.order.tag"

    name = fields.Char('name')

"""
	"results": [{
		"seller": {
			"nickname": "VENDASDKMB",
			"id": 239432672
		},
		"payments": [{
			"reason": "Kit Com 03 Adesivo Spray 3m 75 Cola Silk Sublimação 300g",
			"status_code": null,
			"total_paid_amount": 129.95,
			"operation_type": "regular_payment",
			"transaction_amount": 129.95,
			"date_approved": "2019-05-22T03:51:07.000-04:00",
			"collector": {
				"id": 239432672
			},
			"coupon_id": null,
			"installments": 1,
			"authorization_code": "008877",
			"taxes_amount": 0,
			"id": 4792155710,
			"date_last_modified": "2019-05-22T03:51:07.000-04:00",
			"coupon_amount": 0,
			"available_actions": [
				"refund"
			],
			"shipping_cost": 0,
			"installment_amount": 129.95,
			"date_created": "2019-05-22T03:51:05.000-04:00",
			"activation_uri": null,
			"overpaid_amount": 0,
			"card_id": 203453778,
			"status_detail": "accredited",
			"issuer_id": "24",
			"payment_method_id": "master",
			"payment_type": "credit_card",
			"deferred_period": null,
			"atm_transfer_reference": {
				"transaction_id": "135292",
				"company_id": null
			},
			"site_id": "MLB",
			"payer_id": 89660613,
			"marketplace_fee": 14.290000000000001,
			"order_id": 2000003508419013,
			"currency_id": "BRL",
			"status": "approved",
			"transaction_order_id": null
		}],
		"fulfilled": true,
		"buying_mode": "buy_equals_pay",
		"taxes": {
			"amount": null,
			"currency_id": null
		},
		"order_request": {
			"change": null,
			"return": null
		},
		"expiration_date": "2019-06-19T03:51:07.000-04:00",
		"feedback": {
			"sale": null,
			"purchase": null
		},
		"shipping": {
			"id": 27968238880
		},
		"date_closed": "2019-05-22T03:51:07.000-04:00",
		"id": 2032217210,
		"manufacturing_ending_date": null,
		"hidden_for_seller": false,
		"order_items": [{
			"item": {
				"seller_custom_field": null,
				"condition": "new",
				"category_id": "MLB33383",
				"variation_id": null,
				"variation_attributes": [],
				"seller_sku": null,
				"warranty": "Garantia de 1 ano fabricante",
				"id": "MLB1054990648",
				"title": "Kit Com 03 Adesivo Spray 3m 75 Cola Silk Sublimação 300g"
			},
			"quantity": 1,
			"differential_pricing_id": null,
			"sale_fee": 14.29,
			"listing_type_id": "gold_special",
			"base_currency_id": null,
			"unit_price": 129.95,
			"full_unit_price": 129.95,
			"base_exchange_rate": null,
			"currency_id": "BRL",
			"manufacturing_days": null
		}],
		"date_last_updated": "2020-02-14T02:55:49.811Z",
		"last_updated": "2019-05-28T15:16:04.000-04:00",
		"comments": null,
		"pack_id": null,
		"coupon": {
			"amount": 0,
			"id": null
		},
		"shipping_cost": 0,
		"date_created": "2019-05-22T03:51:05.000-04:00",
		"application_id": "7092",
		"pickup_id": null,
		"status_detail": null,
		"tags": [
			"delivered",
			"paid"
		],
		"buyer": {
			"nickname": "S.VICTORHUGO",
			"id": 89660613
		},
		"total_amount": 129.95,
		"paid_amount": 129.95,
		"mediations": [],
		"currency_id": "BRL",
		"status": "paid"
	}],

"""
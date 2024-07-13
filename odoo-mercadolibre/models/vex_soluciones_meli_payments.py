from odoo import fields, models, api

class VexSolucionesMeliPayments(models.Model):
    _name="vex.meli.payments"

    meli_payment_id = fields.Char('MELI Payment ID')
    meli_payment_reason = fields.Char('Reason')
    meli_payment_status_code = fields.Char('Status Code')
    meli_payment_total_paid_amount = fields.Float('Total Paid')
    meli_payment_operation_type = fields.Char('Operation Type')
    meli_payment_transaction_amount = fields.Float('Transaction')
    meli_payment_date_approved = fields.Datetime('Date Approved')
    meli_payment_collector_id = fields.Char('Collector')
    meli_payment_coupon_id = fields.Char('Coupon')
    meli_payment_installments = fields.Integer('Installments')
    meli_payment_authorization_code = fields.Char('Authorization Code')
    meli_payment_taxes_amount = fields.Float('Taxes')
    meli_payment_date_last_modified = fields.Datetime('Date Last Modified')
    meli_payment_coupon_amount = fields.Float('Coupon Amount')
    meli_payment_available_actions_ids = fields.Many2many('vex.meli.payments.available.action', string='Available Acitions')
    meli_payment_shipping_cost = fields.Float('Shipping Cost')
    meli_payment_installment_amount = fields.Float('Installment Amount')
    meli_payment_date_created = fields.Datetime('Date Created')
    meli_payment_activation_uri = fields.Char('Activation Uri')
    meli_payment_overpaid_amount = fields.Float('Overpaid')
    meli_payment_card_id = fields.Char('Card ID')
    meli_payment_status_detail = fields.Char('Status Detail')
    meli_payment_issuer_id = fields.Char('Issuer')
    meli_payment_method_id = fields.Char('Payment Method')
    meli_payment_type_id = fields.Char('Payment Type')
    meli_payment_deferred_period = fields.Char('Deferred Period')
    meli_payment_atm_transfer_ref_transaction_id = fields.Char('ATM Transfer Ref (Transaction)')
    meli_payment_atm_transfer_ref_company = fields.Char('ATM Transfer Ref (Company')
    meli_payment_site_id = fields.Char('meli_payment_site_id')
    meli_payment_payer_id = fields.Char('Payer ID')
    meli_payment_marketplace_fee = fields.Float('Marketplace Fee')
    meli_payment_order_code = fields.Char('MELI Order Code')
    meli_payment_order_id = fields.Many2one('sale.order', string='Sale Order')
    meli_payment_currency_id = fields.Char('Currency')
    meli_payment_status = fields.Char('Status')
    meli_payment_transaction_order_id = fields.Char('Transaction Order')

class VexSolucionesMeliPaymentsAvailableAction(models.Model):
    _name="vex.meli.payments.available.action"

    name = fields.Char('name')

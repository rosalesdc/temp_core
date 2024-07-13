{
    'name': 'Mercadolibre odoo',
    'version': '16.0.0.1',
    'description': 'Mercadolibre integration with odoo',
    'summary': 'Mercadolibre integration with odoo',
    'author': 'Vex Soluciones',
    'website': 'https://www.vexsoluciones.com',
    'license': 'OPL-1',
    'category': 'Uncategorized',
    'depends': [
        'vex-store-syncronizer',
        'purchase'  
    ],
    'data': [
        'security/security.xml',
        'data/vex_cron.xml',
        'data/vex_category_data.xml',
        'data/vex_data_resapi_list_meli.xml',
        'menus/menu.xml',
        'views/vex_soluciones_instance_inherit_view.xml',
        'views/vex_soluciones_product_inherit_view.xml',
        'wizards/vex_soluciones_import_wizard_inherit.xml',
        'views/vex_soluciones_sale_order_inherit_view.xml',
        'views/vex_soluciones_stock_picking_inherit_view.xml',
        'views/vex_soluciones_restapi_list_meli.xml',
    ],
    'demo': [],
    'auto_install': False,
    'application': False,
    # 'price': 470.00,
    # 'currency': 'USD',
    'assets': {
        'web.assets_backend': [
            'odoo-mercadolibre/static/src/js/gridstack-all.js',
            'odoo-mercadolibre/static/src/xml/vex-dashboard.xml',
            'odoo-mercadolibre/static/src/js/vex-dashboard.js',
            'odoo-mercadolibre/static/src/css/gridstack.css',
            'odoo-mercadolibre/static/src/css/gridstack-extra.css',            
        ]
    }
}
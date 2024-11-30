{
    'name': 'My Custom Module',
    'version': '1.0',
    'summary': 'A custom module for demonstration',
    'description': """A detailed description of the module.""",
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'category': 'Custom',
    'depends': ['base','sale_management', 'stock', 'account','sale','sale_stock'],
    'data': [
        'security/admin_security.xml',
        'security/ir.model.access.csv',
        'views/my_model_view.xml',
        'views/sale_order_view.xml',
        # 'views/sale_settings.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
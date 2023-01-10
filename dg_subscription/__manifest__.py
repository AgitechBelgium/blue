# -*- coding: utf-8 -*-

{
    'name': 'Dg Subscriptions',
    'version': '15.0.1.0.0',
    'category': 'Sales/Subscriptions',
    'sequence': 116,
    'summary': 'Generate recurring invoices based on the financial year',
    'description': """Generate recurring invoices based on the financial year""",
    'depends': [
        'sale',
        'sale_subscription',
    ],
    'data': [
        'data/cron.xml',
        'views/subscription.xml',
    ],
    'license': 'LGPL-3',
    'demo': [
    ],
}

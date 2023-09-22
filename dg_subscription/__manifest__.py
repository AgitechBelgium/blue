# -*- coding: utf-8 -*-

{
    'name': 'Dg Subscriptions',
    'version': '16.0.1.0.1',
    'category': 'Sales/Subscriptions',
    'sequence': 116,
    'summary': 'Generate recurring invoices based on the financial year',
    'description': """Generate recurring invoices based on the financial year""",
    'depends': [
        'sale',
        'sale_subscription',
        'sale_timesheet',
    ],
    'data': [
        'data/cron.xml',
        'views/subscription.xml',
        'views/product_template.xml',
        'views/subscription_templates.xml',
        'views/sale_total_template.xml',
        'views/sale_portal_template.xml',
    ],
    'license': 'LGPL-3',
    'demo': [
    ],
}

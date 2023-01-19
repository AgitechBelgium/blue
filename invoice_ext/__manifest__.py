# -*- coding: utf-8 -*-
{
    'name': "Facture Extension",
    'summary': """ invoice_ext """,
    'description': """ invoice_ext """,
    'author': "DG",
    'category': 'account',
    'version': '16.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'web', 'base_setup'],
    'data': [
        'views/templates.xml',
        'report/account_report.xml',
        'report/report_invoice.xml',
    ],
}

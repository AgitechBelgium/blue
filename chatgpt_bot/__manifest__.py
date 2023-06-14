# -*- coding: utf-8 -*-
{
    'name': 'ChatGPT Bot',
    'version': '16.0.1.0.0',
    'category': 'Productivity/Discuss',
    'summary': 'ChatGPT Bot ',
    'website': 'https://www.ensigncode.com',
    'depends': ['mail'],
    'auto_install': True,
    'installable': True,
    'data': [
        'views/chatgpt_setting_views.xml',
        'data/data.xml',
    ],
    'external_dependencies': {
        'python': ['openai']
    },
    'license': 'LGPL-3',
}

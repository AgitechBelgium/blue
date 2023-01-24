# -*- coding: utf-8 -*-
{
	'name': "Web FID Manager",
	'summary': """ This menu will let you open FID Manager website from odoo. """,
	'category': 'web',
	'version': '16.0.1.0.0',
	'depends': ['base', 'web'],
	'assets': {
		'web.assets_backend': {
			'web_fid_manager/static/src/js/fid_manager.js',
			'web_fid_manager/static/src/xml/fid_systray.xml',
		},
		'web.assets_qweb': {
			'web_fid_manager/static/src/xml/fid_systray.xml',
		},
	},
}

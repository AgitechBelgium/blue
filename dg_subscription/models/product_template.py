# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, Command


class ProductTemplate(models.Model):
	_inherit = "product.template"

	is_provision = fields.Boolean(string="Provision Invoice", default=False)

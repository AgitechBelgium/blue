# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, Command


class ProductTemplate(models.Model):
	_inherit = "product.template"

	is_provision = fields.Boolean(string="Provision Invoice", default=False)
	computed_in_total_invoice = fields.Boolean(string="Computed In Total Invoiced?", default=False)

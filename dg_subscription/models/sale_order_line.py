# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, Command


class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	def _get_invoice_lines(self):
		self.ensure_one()
		if self.temporal_type != 'subscription':
			return super()._get_invoice_lines()
		else:
			return self.invoice_lines

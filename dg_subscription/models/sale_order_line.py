# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, Command


class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	def _get_subscription_qty_invoiced(self, last_invoice_date=None, next_invoice_date=None):
		result = {}
		amount_sign = {'out_invoice': 1, 'out_refund': -1}
		for line in self:
			if line.temporal_type != 'subscription' or line.order_id.state not in ['sale', 'done']:
				continue
			qty_invoiced = 0.0
			related_invoice_lines = line.invoice_lines.filtered(
				lambda l: l.move_id.state != 'cancel')
			for invoice_line in related_invoice_lines:
				line_sign = amount_sign.get(invoice_line.move_id.move_type, 1)
				qty_invoiced += line_sign * invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_uom)
			result[line.id] = qty_invoiced
		return result

	def _get_invoice_lines(self):
		self.ensure_one()
		if self.temporal_type != 'subscription':
			return super()._get_invoice_lines()
		else:
			return self.invoice_lines

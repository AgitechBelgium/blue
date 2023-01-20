# -*- coding: utf-8 -*-

from odoo import fields, models, api, _, Command


class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	def _prepare_invoice_line(self, **optional_values):
		"""Prepare the values to create the new invoice line for a sales order line.

		:param optional_values: any parameter that should be added to the returned invoice line
		:rtype: dict
		"""
		first_product = self.id == self.order_id.order_line[0].id if self.order_id.order_line else False
		self.ensure_one()
		res = {
			'display_type': self.display_type or 'product',
			'sequence': self.sequence,
			'name': self.name,
			'product_id': self.product_id.id,
			'product_uom_id': self.product_uom.id,
			'quantity': self.product_uom_qty/4 if first_product else self.qty_to_invoice,
			'discount': self.discount,
			'price_unit': self.price_unit,
			'tax_ids': [Command.set(self.tax_id.ids)],
			'sale_line_ids': [Command.link(self.id)],
			'is_downpayment': self.is_downpayment,
		}
		analytic_account_id = self.order_id.analytic_account_id.id
		if self.analytic_distribution and not self.display_type:
			res['analytic_distribution'] = self.analytic_distribution
		if analytic_account_id and not self.display_type:
			if 'analytic_distribution' in res:
				res['analytic_distribution'][analytic_account_id] = res['analytic_distribution'].get(analytic_account_id, 0) + 100
			else:
				res['analytic_distribution'] = {analytic_account_id: 100}
		if optional_values:
			res.update(optional_values)
		if self.display_type:
			res['account_id'] = False
		return res

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

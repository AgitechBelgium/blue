from odoo import fields, api, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


def get_current_quarter_dates():
	current_date = datetime.now()
	current_quarter = round((current_date.month - 1) / 3 + 1)
	first_date = datetime(current_date.year, 3 * current_quarter - 2, 1)
	last_date = datetime(current_date.year, 3 * current_quarter + 1, 1) + timedelta(days=-1)
	return first_date.date(), last_date.date()


class Order(models.Model):
	_inherit = 'sale.order'

	next_quarterly_invoice_date = fields.Date(string="Next Date", default=fields.Date.today)

	@api.model
	def cron_dg_subscription_generate_invoices_quarterly(self):
		"""
		Cron to generate invoice quarterly based on the year
		:return:
		"""
		stages_in_progress = self.env['sale.order.stage'].sudo().search([('category', '=', 'progress')])
		applicable_orders = self.sudo().search([
			('is_subscription', '=', True),
			('stage_id', 'in', stages_in_progress.ids),
			('state', '=', 'sale'),
			('invoice_status', 'in', ['to invoice', False]),
			('next_quarterly_invoice_date', 'in', [fields.Date.today(), False])
		])
		self.env.cr.commit()
		quarter_first_date, quarter_last_date = get_current_quarter_dates()
		for order in applicable_orders:
			if order.invoice_ids.filtered(lambda x: quarter_first_date <= x.invoice_date <= quarter_last_date):
				continue
			else:
				try:
					invoices = order.sudo()._create_invoices()
					self.env.cr.commit()
					invoices.sudo().write({'invoice_date': quarter_first_date})
					self.env.cr.commit()
					for invoice_line in invoices.mapped('invoice_line_ids'):
						invoice_line.sudo().write({'quantity': invoice_line.quantity/4})
						self.env.cr.commit()
					for ol in order.order_line:
						ol.qty_invoiced = sum(ol.invoice_lines.mapped('quantity'))
					order.next_quarterly_invoice_date = quarter_last_date + timedelta(days=1)
					self.env.cr.commit()
				except Exception as e:
					raise UserError(f"Error returned for order: {self.name}\n{e}")
			self.env.cr.commit()

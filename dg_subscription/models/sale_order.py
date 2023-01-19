from dateutil.relativedelta import relativedelta
from odoo import fields, api, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import pytz



def get_current_quarter_dates():
	current_date = datetime.now()
	current_quarter = round((current_date.month - 1) / 3 + 1)
	first_date = datetime(current_date.year, 3 * current_quarter - 2, 1)
	last_date = datetime(current_date.year, 3 * current_quarter + 1, 1) + timedelta(days=-1)
	return first_date.date(), last_date.date()


def get_all_quarters():
	first_date = datetime.now().date().replace(month=1, day=1)
	return [first_date, first_date + timedelta()]


class Order(models.Model):
	_inherit = 'sale.order'

	next_quarterly_invoice_date = fields.Date(string="Next Date", default=fields.Date.today)

	def action_invoice_subscription(self):
		account_move = self._create_recurring_invoice()
		for rec in self:
			for move in account_move:
				move.invoice_date = rec.next_quarterly_invoice_date
				rec.next_quarterly_invoice_date = (rec.next_quarterly_invoice_date or rec.date_order) + relativedelta(months=3)
		if account_move:
			return self.action_view_invoice()
		else:
			raise UserError(self._nothing_to_invoice_error_message())

	def get_order_quarter(self):
		quarter_list = []
		current_invoice_date = self.date_order.date()
		for i in [3]*4:
			next_invoice_date = current_invoice_date + relativedelta(months=i)
			quarter_list.append((current_invoice_date, next_invoice_date))
			current_invoice_date = next_invoice_date
		return quarter_list

	def get_remaining_quarter(self):
		quarter_list = self.get_order_quarter()
		return list(filter(lambda x: not self.invoice_ids.filtered(lambda y: x[0] <= y.invoice_date <= x[1]), quarter_list))

	def set_close(self):
		for order in self:
			quarter_list = self.get_remaining_quarter()
			for quarter_start, quarter_end in quarter_list:
				self.create_quarterly_invoice(order, quarter_first_date=quarter_start, quarter_last_date=quarter_end)
		return super(Order, self).set_close()

	def create_quarterly_invoice(self, order, quarter_first_date, quarter_last_date):
		try:
			invoices = order.sudo()._create_invoices()
			self.env.cr.commit()
			invoices.sudo().write({'invoice_date': quarter_first_date})
			self.env.cr.commit()
			for invoice_line in invoices.mapped('invoice_line_ids'):
				invoice_line.sudo().write({'quantity': invoice_line.quantity / 4})
				self.env.cr.commit()
			for ol in order.order_line:
				ol.qty_invoiced = sum(ol.invoice_lines.mapped('quantity'))
			order.next_quarterly_invoice_date = quarter_last_date + timedelta(days=1)
			self.env.cr.commit()
		except Exception as e:
			raise UserError(f"Error returned for order: {self.name}\n{e}")

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
			('next_quarterly_invoice_date', 'in', [datetime.now().astimezone(pytz.timezone(self.env.user.tz)).replace(tzinfo=None).date(), False])
		])
		self.env.cr.commit()
		quarter_first_date, quarter_last_date = get_current_quarter_dates()
		for order in applicable_orders:
			# if order.invoice_ids.filtered(lambda x: quarter_first_date <= x.invoice_date <= quarter_last_date):
			# 	continue
			# else:
			self.create_quarterly_invoice(order=order, quarter_first_date=quarter_first_date, quarter_last_date=quarter_last_date)
			self.env.cr.commit()

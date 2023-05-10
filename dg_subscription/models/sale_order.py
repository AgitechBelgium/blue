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
	total_tasks = fields.Monetary(string="Total Tasks", store=True, compute='_compute_amounts', tracking=6)
	total_invoiced_hours = fields.Monetary(string="Total Invoiced", store=True, compute='_compute_amounts', tracking=6)
	left_to_invoice_hours = fields.Monetary(string="Left To Invoice", store=True, compute='_compute_amounts', tracking=8)
	provision_invoiced = fields.Boolean(string="Provision Invoiced?", compute="_is_provision_invoiced")

	def _is_provision_invoiced(self):
		for rec in self:
			rec.provision_invoiced = len(rec.invoice_ids.filtered('provision_invoice')) >= 4

	def subscription_line_qty(self, sale_line_id=False):
		"""
		Update quantity on the subscription
		:return: None
		"""
		timesheet_ids = self.filtered('is_subscription').timesheet_ids
		sale_line_ids = sale_line_id or timesheet_ids.mapped('so_line')
		for sale_line in sale_line_ids:
			sale_line.write({
				'product_uom_qty': sum(timesheet_ids.filtered(lambda t: t.so_line.id == sale_line.id).mapped('unit_amount'))
			})

	@api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.qty_invoiced', 'order_line.price_total')
	def _compute_amounts(self):
		for order in self:
			if order.order_line:
				order_lines = order.order_line.filtered(lambda x: not x.display_type)
				order.total_tasks = sum(order.order_line[1::].mapped('price_subtotal'))
				order.total_invoiced_hours = sum(order.order_line.invoice_lines.mapped('move_id.amount_untaxed_signed'))
				order.left_to_invoice_hours = 0 if (order.total_tasks - order.total_invoiced_hours) < 0 else (order.total_tasks - order.total_invoiced_hours)
				order.amount_untaxed = order.left_to_invoice_hours
				order.amount_tax = sum(order_lines.mapped('price_tax'))
				order.amount_total = sum(order_lines.mapped('price_total'))
			else:
				order.total_tasks = order.total_invoiced_hours = order.left_to_invoice_hours = 0

	def action_invoice_subscription(self):
		if self.is_subscription:
			manual_invoice = self.env['account.move'].create({
				'partner_id': self.partner_id.id,
				'move_type': 'out_invoice',
				'date': fields.Date.today(),
				'sale_id': self.id,
				'invoice_line_ids': [
					(0, 0, {
						'name': 'Left To invoice',
						'quantity': 1.0,
						'price_unit': self.left_to_invoice_hours,
						'tax_ids': [(6, 0, self.env.user.company_id.account_sale_tax_id.ids)],
					}),
				],
			})
			if manual_invoice:
				for line in self.order_line[1::]:
					line.invoice_lines = [(4, inv_line_id.id) for inv_line_id in manual_invoice.invoice_line_ids]
				# Forcefully computed invoiced quantity
				self.order_line._compute_qty_invoiced()
				# Forcefully computed invoices, and it's count because of manual invoice creation.
				self._get_invoiced()
				return self.action_view_invoice()

		invoices = super(Order, self.with_context(force_super=True)).action_invoice_subscription()
		for line in self.order_line:
			line.write({'invoice_status': 'invoiced'})
		self.write({'invoice_status': 'invoiced'})
		return invoices

	def get_order_quarter(self):
		quarter_list = []
		current_invoice_date = self.date_order.date()
		for i in [3] * 4:
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

	def _get_invoiceable_lines(self, final=False):
		invoiceable_lines = super(Order, self)._get_invoiceable_lines(final)
		if self._context.get('provision_invoice', False) and invoiceable_lines:
			invoiceable_lines = invoiceable_lines[0]
		return invoiceable_lines

	def create_quarterly_invoice(self, order, quarter_first_date, quarter_last_date, auto_commit=False):
		"""

		:param order:
		:param quarter_first_date:
		:param quarter_last_date:
		:param auto_commit:
		:return:
		"""
		try:
			invoices = order.sudo().with_context(from_subscription_invoice=True, provision_invoice=True)._create_invoices()
			if auto_commit:
				self.env.cr.commit()
			invoices.sudo().with_context(check_move_validity=False).write({'invoice_date': quarter_first_date})
			if auto_commit:
				self.env.cr.commit()
			if auto_commit:
				self.env.cr.commit()
			for ol in order.order_line:
				ol.qty_invoiced = sum(ol.invoice_lines.mapped('quantity'))
				if auto_commit:
					self.env.cr.commit()
			order.next_quarterly_invoice_date = quarter_last_date + timedelta(days=1)
			if auto_commit:
				self.env.cr.commit()
			return invoices
		except Exception as e:
			raise UserError(f"Error returned for order: {self.name}\n{e}")

	def action_provision_invoice_subscription(self):
		quarter_first_date, quarter_last_date = get_current_quarter_dates()
		if self.get_remaining_quarter():
			account_move = self.create_quarterly_invoice(self, quarter_first_date=quarter_first_date, quarter_last_date=quarter_last_date, auto_commit=False)
			for rec in self:
				for move in account_move:
					move.sudo().with_context(check_move_validity=False).write({
						'invoice_date': rec.next_quarterly_invoice_date,
						'provision_invoice': True,
					})
					rec.next_quarterly_invoice_date = (rec.next_quarterly_invoice_date or rec.date_order) + relativedelta(months=3)
			# Forcefully computed amounts
			self._compute_amounts()
			if account_move:
				return self.action_view_invoice()
			else:
				raise UserError(self._nothing_to_invoice_error_message())

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
			if self.get_remaining_quarter():
				self.create_quarterly_invoice(order=order, quarter_first_date=quarter_first_date, quarter_last_date=quarter_last_date, auto_commit=True)
				for move in order.invoice_ids:
					move.sudo().with_context(check_move_validity=False).write({
						'invoice_date': order.next_quarterly_invoice_date
					})
					order.next_quarterly_invoice_date = (order.next_quarterly_invoice_date or order.date_order) + relativedelta(months=3)
				self.env.cr.commit()

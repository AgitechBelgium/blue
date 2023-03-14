from odoo import fields, api, models, _


class AnalyticLine(models.Model):
	_inherit = 'account.analytic.line'

	@api.model_create_multi
	def create(self, vals_list):
		"""
		Update quantity on the sale order line
		:param vals_list: values
		:return: RecordSet
		"""
		res = super(AnalyticLine, self).create(vals_list)
		res.task_id.sale_line_id.order_id.subscription_line_qty(res.task_id.sale_line_id)
		return res

	def write(self, values):
		"""
		Update quantity on the sale order line
		:param values: values
		:return: RecordSet
		"""
		res = super(AnalyticLine, self).write(values)
		self.task_id.sale_line_id.order_id.subscription_line_qty(self.task_id.sale_line_id)
		return res

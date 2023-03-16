from odoo import models, api, fields, _


class Move(models.Model):
	_inherit = 'account.move'

	sale_id = fields.Many2one('sale.order', string="Linked Order")

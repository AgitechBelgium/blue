from odoo import models, api, fields, _
from collections import defaultdict


class Tax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None):
        tax_totals = super(Tax, self)._prepare_tax_totals(base_lines, currency, tax_lines)
        if 'subtotals' in tax_totals:
            tax_totals['subtotals'] = list(filter(lambda x: 'Untaxed' not in x.get('name'), tax_totals['subtotals']))
        if 'groups_by_subtotal' in tax_totals:
            reduced_d = defaultdict(list, {k: v for k, v in tax_totals['groups_by_subtotal'].items() if 'Untaxed' not in k})
            tax_totals['groups_by_subtotal'] = reduced_d
        tax_totals['subtotals_order'] = list(filter(lambda z: 'Untaxed' not in z, tax_totals['subtotals_order']))
        return tax_totals

from odoo import fields, models, _
from odoo.exceptions import UserError


class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        self = self.with_context(force_company=self.company_id.id)
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()

        if self.location_id.valuation_out_account_id:
            acc_src = self.location_id.valuation_out_account_id.id
        else:
            acc_src = accounts_data['stock_input'].id

        if self.location_dest_id.valuation_in_account_id:
            acc_dest = self.location_dest_id.valuation_in_account_id.id
        else:
            acc_dest = accounts_data['stock_output'].id

        acc_valuation = accounts_data.get('stock_valuation', False)
        if acc_valuation:
            acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(
                _('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts.'))
        if not acc_src:
            raise UserError(
                _('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (
                    self.product_id.display_name))
        if not acc_dest:
            raise UserError(
                _('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (
                    self.product_id.display_name))
        if not acc_valuation:
            raise UserError(
                _('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
        journal_id = self.picking_type_id.journal_id.id if self.picking_type_id.journal_id.id else accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest, acc_valuation


from odoo import api, models
# from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_report_base_filename(self):
        return self._get_move_display_name()

    def is_invoice(self, include_receipts=False):
        if self.env.context.get('im_from_move_report'):
            return True
        return self.type in self.get_invoice_types(include_receipts)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def render_qweb_pdf(self, res_ids=None, data=None):
        return super(IrActionsReport, self.with_context(im_from_move_report=True)).render_qweb_pdf(res_ids, data)

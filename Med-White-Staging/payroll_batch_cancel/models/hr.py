# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[('cancel', 'Cancelled')])

    def action_cancel(self):
        for batch in self:
            batch.slip_ids.action_payslip_cancel()
            batch.write({'state': 'cancel'})

    def action_reset_draft(self):
        for batch in self:
            batch.slip_ids.action_payslip_draft()
            batch.slip_ids.unlink()
            batch.write({'state': 'draft'})

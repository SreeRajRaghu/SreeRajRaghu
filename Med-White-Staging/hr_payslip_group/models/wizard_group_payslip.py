# coding: utf-8

from odoo import fields, models, _
from odoo.exceptions import UserError


class WizardPayslipReport(models.Model):
    _name = 'emp.payslip.group'
    _description = 'Emp Payslip Group'

    name = fields.Char(string="Name", required=True)
    date_start = fields.Date('Date Start')
    date_end = fields.Date('Date End')
    # company_id = fields.Many2one('res.company', string='Company', re)
    batch_ids = fields.One2many("hr.payslip.run", "group_id", string="Batches")
    payslip_ids = fields.One2many("hr.payslip", "group_id")

    def action_generate_payslip(self):
        ctx = self.env.context.copy()
        company_ids = ctx.get('allowed_company_ids')
        if len(company_ids) == 1:
            raise UserError(_("Multiple Company Not Selected, For Single Company you can create a batch manually."))

        batches = Batch = self.env['hr.payslip.run'].sudo()
        GenPayslipWiz = self.env['hr.payslip.employees'].sudo()
        for company in self.env['res.company'].sudo().browse(company_ids):
            vals = {
                'name': self.name,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'company_id': company.id,
                'group_id': self.id,
            }
            batch = Batch.create(vals)
            batches |= batch
            cmp_ctx = {
                'default_date_start': self.date_start,
                'default_date_end': self.date_end,
                'active_id': batch.id,
                'default_company_id': company.id,
            }
            payslip_wiz = GenPayslipWiz.with_context(**cmp_ctx).create({})
            payslip_wiz.with_context(**cmp_ctx).compute_sheet()
        action = self.env.ref('hr_payroll.action_hr_payslip_run_tree').read()[0]
        action.update({
            'domain': [('group_id', 'in', self.ids)]
        })
        return action


class Batch(models.Model):
    _inherit = 'hr.payslip.run'

    group_id = fields.Many2one("emp.payslip.group", string="Group")


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    group_id = fields.Many2one(related="payslip_run_id.group_id", string="Payslip Group")


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def _get_available_contracts_domain(self):
        cmp_id = self.env.context.get('default_company_id') or self.env.company.id
        return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', cmp_id)]

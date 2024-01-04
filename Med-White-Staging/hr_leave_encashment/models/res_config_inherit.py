from odoo import fields, models


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    employee_encashment_account = fields.Many2one('account.account', related='company_id.employee_encashment_account', readonly=False, string="Employee Encashment Account")


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    employee_encashment_account = fields.Many2one('account.account', string="Employee Encashment Account")


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_encashment_journal = fields.Boolean(string="Is Encashment Journal?")
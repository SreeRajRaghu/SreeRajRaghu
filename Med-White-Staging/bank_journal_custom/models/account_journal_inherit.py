from odoo import fields, models


class AccountJournalInherit(models.Model):
    _inherit = "account.journal"

    is_bank_charge = fields.Boolean('Bank Charge Applicable')
    charge_type = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')], string='Type')
    amount = fields.Float('Amount')
    percentage = fields.Float('Percentage', digits=(12, 4))
    bank_account = fields.Many2one('account.account', string="Bank Charge Account")

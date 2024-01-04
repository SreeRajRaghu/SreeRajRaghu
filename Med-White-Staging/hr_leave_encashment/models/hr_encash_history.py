from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class HrEncashmentHistory(models.Model):
    _name = 'hr.encashment.history'
    _description = 'Hr leave encash'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default="HR Encashment History", tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', tracking=True)
    branch_id = fields.Many2one(related='employee_id.contract_id.branch_id', string="Branch", tracking=True)
    journal_entry_id = fields.Many2one('account.move', string='Journal Entry', tracking=True)
    payment_entry_id = fields.Many2one('account.payment', string='Payment Entry', tracking=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type', tracking=True)
    date = fields.Date('Date', tracking=True)
    no_of_days = fields.Float(string='Leave Encashed', tracking=True)
    encashment_amount = fields.Float(string='Encashment Amount', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('paid', 'Paid')],
                             default='draft', tracking=True)
    
    def action_journal_entry(self):
        return {
            'name': 'Journal Entry',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.move',
            'res_id': self.journal_entry_id.id
        }

    def action_payment_journal(self):
        return {
            'name': 'Payment Entry',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.payment',
            'res_id': self.payment_entry_id.id
        }

    def action_encashment_post(self):
        if self.encashment_amount == 0:
            raise ValidationError(_('Amount should be greater than 0.'))
        if not self.env.user.company_id.employee_encashment_account.id and not self.env.user.company_id.employee_payable_account.id:
            raise ValidationError(_('Please select accounts in general settings'))
        journal_id = self.env['account.journal'].search([('is_encashment_journal', '=', True)], limit=1)
        if not journal_id:
            raise ValidationError(_('Please select a specific journal in journals'))
        debit_credit_lines = []
        debit_vals = {
            'name': self.employee_id.name,
            'partner_id': self.employee_id.user_id.partner_id.id,
            'branch_id': self.branch_id.id,
            'debit': abs(self.encashment_amount),
            'credit': 0.0,
            'account_id': self.env.user.company_id.employee_encashment_account.id,
        }

        credit_vals = {
            'name': self.employee_id.name,
            'partner_id': self.employee_id.user_id.partner_id.id,
            'branch_id': self.branch_id.id,
            'debit': 0.0,
            'credit': abs(self.encashment_amount),
            'account_id': self.env.user.company_id.employee_payable_account.id,
        }
        debit_credit_lines.append((0, 0, debit_vals))
        debit_credit_lines.append((0, 0, credit_vals))
        vals = {
            'journal_id': journal_id.id,
            'date': fields.Datetime.today(),
            'branch_id': self.branch_id.id,
            'state': 'draft',
            'ref': self.employee_id.name + "- Encashment",
            'line_ids': debit_credit_lines
        }
        move = self.env['account.move'].sudo().create(vals)
        move.post()
        self.journal_entry_id = move.id
        self.state = 'posted'
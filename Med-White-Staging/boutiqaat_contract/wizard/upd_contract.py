# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import fields, models


class UpdContract(models.TransientModel):
    _name = "update.contract"
    _description = "Update Contract"

    name = fields.Char("New Contract Name", required=True)
    contract_id = fields.Many2one('hr.contract', string="Contract", required=True)
    date_from = fields.Date("Effective Date", required=True, default=fields.Date.today)
    wage = fields.Float("New Basic Salary", required=True)

    def action_upd(self):
        self.ensure_one()
        contract = self.contract_id
        emp = contract.employee_id
        prev_contract_end_date = self.date_from - timedelta(days=1)

        contract.write({
            'date_end': prev_contract_end_date,
            'state': 'upd',
        })
        new_contract = contract.copy({
            'date_start': self.date_from,
            'date_end': False,
            'trial_date_end': False,
            'wage': self.wage,
            'name': self.name,
            'state': 'open',
            'prev_contract_id': contract.id,
        })
        contract.write({
            'next_contract_id': new_contract.id,
        })
        emp.contract_id = new_contract.id

        action = self.env.ref('hr_contract.action_hr_contract').read()[0]
        action.update({'domain': [('id', 'in', [new_contract.id, contract.id])]})
        return action

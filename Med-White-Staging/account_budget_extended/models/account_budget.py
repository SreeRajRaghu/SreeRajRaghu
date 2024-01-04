# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.osv import expression
from odoo import api, fields, models


class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    account_id = fields.Many2one('account.account', string='Account', required=True)
    account_ids = fields.Many2many('account.account', string='Accounts')

    @api.onchange('general_budget_id')
    def onchange_account_id(self):
        self.account_ids = False
        if self.general_budget_id:
            self.account_ids = self.general_budget_id.account_ids.ids

    def _compute_practical_amount(self):
        for line in self:
            # acc_ids = line.general_budget_id.account_ids.ids
            date_to = line.date_to
            date_from = line.date_from
            # if line.analytic_account_id.id:
            #     analytic_line_obj = self.env['account.analytic.line']
            #     domain = [('account_id', '=', line.analytic_account_id.id),
            #               ('date', '>=', date_from),
            #               ('date', '<=', date_to),
            #               ]
            #     if acc_ids:
            #         domain += [('general_account_id', 'in', acc_ids)]

            #     where_query = analytic_line_obj._where_calc(domain)
            #     analytic_line_obj._apply_ir_rules(where_query, 'read')
            #     from_clause, where_clause, where_clause_params = where_query.get_sql()
            #     select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause

            # else:
            aml_obj = self.env['account.move.line']
            domain = [
                ('account_id', '=', line.account_id.id),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
                ('move_id.state', '=', 'posted')
            ]
            if line.analytic_account_id:
                domain.append(('analytic_account_id', '=', line.analytic_account_id.id))
            where_query = aml_obj._where_calc(domain)
            aml_obj._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()
            select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause

            self.env.cr.execute(select, where_clause_params)
            line.practical_amount = self.env.cr.fetchone()[0] or 0.0

    def action_open_budget_entries(self):
        # if self.analytic_account_id:
        #     # if there is an analytic account, then the analytic items are loaded
        #     action = self.env['ir.actions.act_window'].for_xml_id('analytic', 'account_analytic_line_action_entries')
        #     action['domain'] = [('account_id', '=', self.analytic_account_id.id),
        #                         ('date', '>=', self.date_from),
        #                         ('date', '<=', self.date_to)
        #                         ]
        #     if self.general_budget_id:
        #         action['domain'] += [('general_account_id', 'in', self.general_budget_id.account_ids.ids)]
        # else:
        # otherwise the journal entries booked on the accounts of the budgetary postition are opened
        action = self.env['ir.actions.act_window'].for_xml_id('account', 'action_account_moves_all_a')
        domain = [
            ('account_id', '=', self.account_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]
        if self.analytic_account_id:
            domain.append(('analytic_account_id', '=', self.analytic_account_id.id))
        action['domain'] = domain
        return action

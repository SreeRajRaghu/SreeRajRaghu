# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _




class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    filter_branch = None

    @api.model
    def _init_filter_branch(self, options, previous_options=None):
        if not self.filter_branch:
            return
        options['branch'] = self.filter_branch
        options['branch_ids'] = previous_options and previous_options.get('branch_ids') or []
        selected_branch_ids = [int(partner) for partner in options['branch_ids']]
        selected_branches = selected_branch_ids and self.env['res.branch'].browse(selected_branch_ids) or self.env['res.branch']
        options['selected_branch_ids'] = selected_branches.mapped('name')
        return options

    @api.model
    def _get_options(self, previous_options=None):
        # OVERRIDE
        options = super(AccountReport, self)._get_options(previous_options)
        self._init_filter_branch(options, previous_options)
        return options


    def _set_context(self, options):
        ctx = super(AccountReport, self)._set_context(options)
        if options.get('branch_ids'):
            ctx['branch_ids'] = self.env['res.branch'].browse([int(branch) for branch in options.get('branch_ids',[])])
        return ctx


    def get_report_informations(self, options):
        '''
        return a dictionary of informations that will be needed by the js widget, manager_id, footnotes, html of report and searchview, ...
        '''
        options = self._get_options(options)

        searchview_dict = {'options': options, 'context': self.env.context}
        # Check if report needs analytic
        


        if options.get('analytic_accounts') is not None:
            options['selected_analytic_account_names'] = [self.env['account.analytic.account'].browse(int(account)).name for account in options['analytic_accounts']]
        if options.get('analytic_tags') is not None:
            options['selected_analytic_tag_names'] = [self.env['account.analytic.tag'].browse(int(tag)).name for tag in options['analytic_tags']]
        if options.get('partner'):
            options['selected_partner_ids'] = [self.env['res.partner'].browse(int(partner)).name for partner in options['partner_ids']]
            options['selected_partner_categories'] = [self.env['res.partner.category'].browse(int(category)).name for category in options['partner_categories']]

        if options.get('branch'):
            options['selected_branch_ids'] = [self.env['res.branch'].browse(int(branch)).name for branch in options['branch_ids']]

        # Check whether there are unposted entries for the selected period or not (if the report allows it)
        if options.get('date') and options.get('all_entries') is not None:
            date_to = options['date'].get('date_to') or options['date'].get('date') or fields.Date.today()
            period_domain = [('state', '=', 'draft'), ('date', '<=', date_to)]
            options['unposted_in_period'] = bool(self.env['account.move'].search_count(period_domain))

        if options.get('journals'):
            journals_selected = set(journal['id'] for journal in options['journals'] if journal.get('selected'))
            for journal_group in self.env['account.journal.group'].search([('company_id', '=', self.env.company.id)]):
                if journals_selected and journals_selected == set(self._get_filter_journals().ids) - set(journal_group.excluded_journal_ids.ids):
                    options['name_journal_group'] = journal_group.name
                    break

        report_manager = self._get_report_manager(options)
        info = {'options': options,
                'context': self.env.context,
                'report_manager_id': report_manager.id,
                'footnotes': [{'id': f.id, 'line': f.line, 'text': f.text} for f in report_manager.footnotes_ids],
                'buttons': self._get_reports_buttons_in_sequence(),
                'main_html': self.get_html(options),
                'searchview_html': self.env['ir.ui.view'].render_template(self._get_templates().get('search_template', 'account_report.search_template'), values=searchview_dict),
                }
        return info

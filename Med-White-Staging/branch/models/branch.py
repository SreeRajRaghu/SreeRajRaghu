# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Branch'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True)
    telephone = fields.Char(string='Telephone No')
    address = fields.Text('Address')
    analytic_account_id = fields.Many2one(comodel_name="account.analytic.account", string="Analytic Account", required=False, )
    analytic_account_tag_id = fields.Many2one(comodel_name="account.analytic.tag", string="Analytic Account Tag", required=False, )

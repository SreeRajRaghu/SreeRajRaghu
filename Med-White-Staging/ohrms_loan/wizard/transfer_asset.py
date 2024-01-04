from odoo import fields, models,api, _
from odoo.exceptions import ValidationError


class TransferAsset(models.TransientModel):
    _name = 'transfer.branch'

    @api.model
    def default_get(self, fields):
        res = super(TransferAsset, self).default_get(fields)
        asset = self.env['account.asset']
        asset_id = self.env.context.get('active_id')
        if asset_id:
            asset = asset.browse(asset_id)
            res['current_branch_id'] = asset.branch_id.id
            res['current_analytic_account'] = asset.account_analytic_id.id
            res['asset_id'] = asset.id
        return res

    date = fields.Date('Date', default=fields.Date.today())
    current_branch_id = fields.Many2one('res.branch', string='Current Branch')
    current_analytic_account = fields.Many2one('account.analytic.account', string='Current Analytic Account')
    branch_id = fields.Many2one('res.branch', string='Branch')
    analytic_account = fields.Many2one('account.analytic.account', related='branch_id.analytic_account_id', string='Analytic Account')
    asset_id = fields.Many2one('account.asset', string='Asset')

    def assets_branch_transfer(self):
        if not self.current_branch_id:
                raise ValidationError(_('Please set a branch'))
        for move in self.asset_id.depreciation_move_ids.filtered(lambda i: i.state == 'draft'):
            move.branch_id = self.branch_id.id
            for line in move.line_ids:
                line.branch_id = self.branch_id.id
                line.analytic_account_id = self.analytic_account.id
        asset = self.asset_id
        asset.branch_id = self.branch_id.id
        asset.account_analytic_id = self.analytic_account.id
        asset_move = self.env['account.move'].sudo().create({
            'journal_id': self.asset_id.journal_id.id,
            'branch_id': self.branch_id.id,
            'ref': self.asset_id.name + "- Asset",
            'date': self.date,
            'line_ids': [
                (0, 0, {
                    'account_id': asset.account_asset_id.id,
                    'branch_id': self.current_branch_id.id,
                    'analytic_account_id': self.current_analytic_account.id,
                    'debit': 0,
                    'credit': asset.book_value,
                    'name': self.asset_id.name,
                }),
                (0, 0, {
                    'account_id': asset.account_asset_id.id,
                    'branch_id': self.branch_id.id,
                    'analytic_account_id': self.analytic_account.id,
                    'debit': asset.book_value,
                    'credit': 0,
                    'name': self.asset_id.name,
                }),
            ],
        })
        asset_move.post()
        depreciation_move = self.env['account.move'].sudo().create({
            'journal_id': self.asset_id.journal_id.id,
            'branch_id': self.branch_id.id,
            'ref':  self.asset_id.name + "- Depreciation",
            'date': self.date,
            'line_ids': [
                (0, 0, {
                    'account_id': asset.account_depreciation_id.id,
                    'branch_id': self.current_branch_id.id,
                    'analytic_account_id': self.current_analytic_account.id,
                    'debit': abs(asset.original_value - asset.book_value),
                    'credit': 0,
                    'name': self.asset_id.name,
                }),
                (0, 0, {
                    'account_id': asset.account_depreciation_id.id,
                    'branch_id': self.branch_id.id,
                    'analytic_account_id': self.analytic_account.id,
                    'credit': abs(asset.original_value - asset.book_value),
                    'debit': 0,
                    'name': self.asset_id.name,
                }),
            ],
        })
        depreciation_move.post()

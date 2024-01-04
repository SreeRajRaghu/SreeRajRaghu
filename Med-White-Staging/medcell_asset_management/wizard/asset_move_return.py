from odoo import api, fields, models


class AssetMoveReturn(models.TransientModel):
    _name = 'asset.move.return'

    custodian_name = fields.Many2one('hr.employee', string="Custodian Name")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id,
                                 required=True)
    asset_issue_ids = fields.Many2many('asset.move.issue.details', string="Asset Issue")

    @api.onchange('custodian_name')
    def onchange_custodian_name(self):
        self.asset_issue_ids = False
        if self.custodian_name:
            asset_list = []
            custodian_obj = self.env['hr.employee'].search([('id', '=', self.custodian_name.id)])
            for asset in custodian_obj.asset_move_issue_ids:
                if not asset.return_date:
                    asset_list.append((0, 0, {
                        'product_id': asset.product_id.id,
                        'handover_date': asset.handover_date,
                        'return_date': asset.return_date
                    }))
            self.asset_issue_ids = asset_list

    @api.model
    def action_return_asset_move(self):
        for line in self.asset_issue_ids:
            for rec in self.custodian_name.asset_move_issue_ids:
                if rec.product_id == line.product_id:
                    rec.write({'return_date': line.return_date})
            product = self.env['asset.product'].search([('id', '=', line.product_id.id)])
            for asset in product.asset_move_return_ids:
                if line.product_id == product and asset.custodian_id == self.custodian_name:
                    product.state = 'instock'
                    asset.write({'returned_date': line.return_date})

    @api.model
    def generate_return_receipt(self):
        return self.env.ref('medcell_asset_management.employee_asset_return_report').report_action(self)

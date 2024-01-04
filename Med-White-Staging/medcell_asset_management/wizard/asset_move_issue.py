from odoo import api, fields, models
from odoo.exceptions import UserError


class AssetMoveIssue(models.TransientModel):
    _name = 'asset.move.issue'

    @api.onchange('custodian_name')
    def onchange_custodian_name(self):
        if self.custodian_name:
            self.manager_id = self.custodian_name.parent_id.id

    custodian_name = fields.Many2one('hr.employee', string="Custodian Name")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id,
                                 required=True)
    department_id = fields.Many2one('hr.department', string="Department", related="custodian_name.department_id")
    manager_id = fields.Many2one('hr.employee', string="Hod/Manager Name", readonly=True)
    handover_date = fields.Date(string="Handover Date")
    product_id = fields.Many2one('asset.product', string="Product Name", domain=[('state', '=', 'instock')])
    return_date = fields.Date(string="Return Date")

    @api.model
    def action_issue_asset_move(self, context=None):
        asset_move = []
        asset_move_issue = []
        # if self.custodian_name and self.product_id:
        asset_move.append((0, 0, {
            'product_id': self.product_id.id,
            'handover_date': self.handover_date,
        }))
        self.custodian_name.asset_move_issue_ids = asset_move
        asset_move_issue.append((0, 0, {
            'custodian_id': self.custodian_name.id,
            'issue_date': self.handover_date,
        }))
        self.product_id.asset_move_return_ids = asset_move_issue
        self.product_id.state = 'issued'
        self.custodian_name.message_post(
            body=str(self.product_id.product_code) + " " + "is issued on" + " " + str(self.handover_date),
            subtype='mt_comment',
            partner_ids=[(4, self.custodian_name.user_id.partner_id.id)],
            context=context)
        # else:
        #     raise UserError('Please Select Custodian Name and Product')

    @api.model
    def generate_issue_receipt(self):
        return self.env.ref('medcell_asset_management.employee_asset_issue_report').report_action(self)

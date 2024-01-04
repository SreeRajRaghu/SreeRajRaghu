from odoo import models, fields, api


class Category(models.Model):
    _inherit = "approval.category"

    is_coach_approver = fields.Boolean("Employee Coach")


class Request(models.Model):
    _inherit = "approval.request"

    is_coach_approver = fields.Boolean(related="category_id.is_coach_approver")

    @api.onchange('category_id', 'request_owner_id')
    def _onchange_category_id(self):
        current_users = self.approver_ids.mapped('user_id')
        new_users = self.category_id.user_ids
        employee = self.env['hr.employee'].sudo().sudo().search([('user_id', '=', self.request_owner_id.id)], limit=1)
        if employee:
            if self.category_id.is_coach_approver and employee.coach_id.user_id:
                new_users |= employee.coach_id.user_id
            if self.category_id.is_manager_approver and employee.parent_id.user_id:
                new_users |= employee.parent_id.user_id
        for user in new_users - current_users:
            self.approver_ids += self.env['approval.approver'].new({
                'user_id': user.id,
                'request_id': self.id,
                'status': 'new'})

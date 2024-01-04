from odoo import models, fields, api


class PurchaseAgreementsInherit(models.Model):
    _inherit = 'purchase.requisition'

    branch_id = fields.Many2one('res.branch', 'Branch')


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[('finance', 'Finance'), ('ceo_approval', 'CEO Approval')])

    @api.model
    def create(self, vals):
        purchase = super(PurchaseOrderInherit, self).create(vals)
        if purchase.requisition_id:
            purchase.branch_id = purchase.requisition_id.branch_id.id
        return purchase

    def action_to_finance(self):
        for rec in self:
            rec.state = 'finance'

    def action_to_cancel(self):
        for rec in self:
            rec.button_cancel()

    def action_to_cancel2(self):
        for rec in self:
            rec.button_cancel()

    def action_to_ceo_state(self):
        for rec in self:
            rec.state = 'ceo_approval'

    def confirm_order_button(self):
        for order in self:
            if order.state not in ['ceo_approval']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.company.currency_id._convert(
                        order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                        order.date_order or fields.Date.today())) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True


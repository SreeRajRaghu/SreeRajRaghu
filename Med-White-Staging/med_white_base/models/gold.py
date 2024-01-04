from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    company_code = fields.Selection([
        ('lab', 'Lab'), ('radiology', 'Radiology'),
        ('pcr', 'PCR'), ('gold', 'Gold'),('lab_medgray','Medgray Lab'),('medgray_derma','Medgray Derma'),('medmarine_lab','Medmarine Lab')
    ], string='Company Code', default="gold")
    dr_cost = fields.Text(tracking=True)


class ProductProduct(models.Model):
    _inherit = "product.product"

    company_code = fields.Selection([
        ('lab', 'Lab'), ('radiology', 'Radiology'),
        ('pcr', 'PCR'), ('gold', 'Gold'),('lab_medgray','Medgray Lab'),('medgray_derma','Medgray Derma'),('medmarine_lab','Medmarine Lab')
    ], string='Company Code', default="gold")


class StockLocation(models.Model):
    _inherit = "stock.location"

    company_code = fields.Selection([
        ('lab', 'Lab'), ('radiology', 'Radiology'),
        ('pcr', 'PCR'), ('gold', 'Gold'),('lab_medgray','Medgray Lab'),('medgray_derma','Medgray Derma'),('medmarine_lab','Medmarine Lab')
    ], string='Company Code', default=lambda self: self.env.company.company_code)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    company_code = fields.Selection([
        ('lab', 'Lab'), ('radiology', 'Radiology'),
        ('pcr', 'PCR'), ('gold', 'Gold'),('lab_medgray','Medgray Lab'),('medgray_derma','Medgray Derma'),('medmarine_lab','Medmarine Lab')
    ], string='Company Code', default=lambda self: self.env.company.company_code)

    @api.model
    def _prepare_picking(self):
        vals = super(PurchaseOrder, self)._prepare_picking()
        vals.update({
                'company_code': self.company_code
            })
        return vals


class StockPicking(models.Model):
    _inherit = "stock.picking"

    company_code = fields.Selection([
        ('lab', 'Lab'), ('radiology', 'Radiology'),
        ('pcr', 'PCR'), ('gold', 'Gold'),('lab_medgray','Medgray Lab'),('medgray_derma','Medgray Derma'),('medmarine_lab','Medmarine Lab')
    ], string='Company Code', default=lambda self: self.env.company.company_code)


class DashboardSettingsLine(models.Model):
    _inherit = 'dashboard.settings.line'

    visibility = fields.Selection(selection_add=[
        ('med_gold', 'Med Gold'),
    ])


class PatientBirthdayWizard(models.TransientModel):
    _name = 'patient.birthday.wizard'
    _description = 'Patients Birthday Wizard'

    start_date = fields.Date('Start Date', default=fields.Date.context_today, required=True)
    end_date = fields.Date('End Date', default=fields.Date.context_today, required=True)

    def action_confirm(self):
        list_of_ids = []
        for record in self.env['res.partner'].search([]):
            if record.birthday and self.start_date.day <= record.birthday.day <= self.end_date.day and self.start_date.month <= record.birthday.month <= self.end_date.month:
                list_of_ids.append(record.id)

        print("\n\n\n\n\n\n\n")
        print("List of id is : ", list_of_ids)
        print("\n\n\n\n\n\n\n")
        action = {
            'name': 'Patients Having Birthday',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', list_of_ids)],
        }
        return action

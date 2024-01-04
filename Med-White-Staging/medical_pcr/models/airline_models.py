from odoo import api, fields, models, _
from odoo.exceptions import UserError


class QuarantineStation(models.Model):
    _name = "quarantine.station"
    _description = "Quarantine Station"

    name = fields.Char(string='Name', required=True)
    street = fields.Char()
    street2 = fields.Char()
    zip_code = fields.Char(change_default=True)
    city = fields.Char()
    area_id = fields.Many2one("res.area", string="Area")
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=lambda self: self.env.company.country_id)
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()


class SwabLocation(models.Model):
    _name = "swab.location"
    _description = "Collection Center"

    name = fields.Char(string='Center Name', required=True)
    code = fields.Char("Code")
    street = fields.Char()
    street2 = fields.Char()
    zip_code = fields.Char(change_default=True)
    area_id = fields.Many2one("res.area", string="Area")
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=lambda self: self.env.company.country_id)
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()

    # pcr_center_name_en = fields.Char("Center Name (En)")
    name_ar = fields.Char("Center Name (Ar)")
    pcr_center_logo = fields.Binary("Center Logo")


class AirlineSelection(models.Model):
    _name = "airline.selection"
    _description = "Airline Selection"

    name = fields.Char(string='Name', required=True)


class MedicalContactList(models.Model):
    _name = "medical.contact.list"
    _description = "Medical Contact List"

    name = fields.Char(required=True)
    phone = fields.Char("Contact No.")
    medical_order_id = fields.Many2one("medical.order", string="Appointment")


class PCRConfiguration(models.Model):
    _name = "pcr.appointment.condition"
    _description = "PCR Appointment Condition"
    _order = "sequence"

    sequence = fields.Integer("Sequence", default=8)
    pcr_appointments_type = fields.Selection([
        ('arrival', 'Arrival'),
        ('departure', 'Departure')],
        string='Travel', tracking=True)

    pcr_type = fields.Selection([
        ('red', 'Red'),
        ('green', 'Green'),
        ('yellow', 'Yellow')],
        string='Immune Type', tracking=True)

    pcr_result = fields.Selection([
        ('negative', 'Negative'),
        ('positive', 'Positive'),
        ('equivocal', 'Equivocal'),
        ('rejected', 'Rejected')], string='PCR Result', copy=False, tracking=True)

    discount = fields.Float("Next Appointment Discount (%)")
    next_appointment = fields.Float("Next Appointment After (Days)")
    company_id = fields.Many2one("res.company", string="Company")

    _sql_constraints = [
        ('uniq_pcr_condition', 'unique (pcr_appointments_type, pcr_type, pcr_result, company_id)', 'Same condition repeated !')
    ]

    @api.constrains('pcr_appointments_type', 'pcr_type', 'pcr_result', 'discount')
    def check_pcr_line(self):
        for rec in self:
            if not (rec.pcr_appointments_type or rec.pcr_type or rec.pcr_result):
                raise UserError(_("Any one of the field Travel, Immune Type, PCR Result is required."))


class MedicalCategory(models.Model):
    _inherit = "medical.category"

    medical_type = fields.Selection([
        ('pcr', 'PCR'), ('vaccine', 'Vaccine')], string="Product Medical Type")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vaccine_dose = fields.Selection([
        ('first', 'First'), ('second', 'Second'), ('third', 'Third')], string="Dose")
    medical_type = fields.Selection(related="medical_categ_id.medical_type")
    manufacturer = fields.Char('Manufacturer')

    pcr_report_line_1 = fields.Text("PCR Result: Line 1")
    pcr_report_line_2 = fields.Text("PCR Result: Line 2")
    pcr_report_line_3 = fields.Text("PCR Result: Line 3")

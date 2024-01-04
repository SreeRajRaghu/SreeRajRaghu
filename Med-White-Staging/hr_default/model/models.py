# coding: utf-8

from odoo import fields, models


class ArticleType(models.Model):
    _name = "article.type"
    _description = "Article Type"

    name = fields.Char(required=True)


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    article_type_id = fields.Many2one('article.type', string="Attachment Type")

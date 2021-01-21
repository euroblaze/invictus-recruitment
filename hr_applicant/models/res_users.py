from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    applicant_cv_ids = fields.Many2many('hr.applicant', 'applicant_cv_ids')

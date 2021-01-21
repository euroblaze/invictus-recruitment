from odoo import api, fields, models


class RequestedChanges(models.Model):
    _name = 'requested.changes'

    applicant = fields.Many2one('hr.applicant', string='Applicant')
    recruiter = fields.Many2one('res.users', string='Recruiter')

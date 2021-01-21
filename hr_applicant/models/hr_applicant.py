# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from werkzeug import urls

from odoo import api, fields, models
from odoo.tools.translate import html_translate
import logging
from datetime import datetime, timedelta
from odoo.addons.http_routing.models.ir_http import slug



_logger = logging.getLogger(__name__)


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    applicant_cv_ids = fields.Many2many('res.users', 'applicant_cv_ids')
    date_cv_request = fields.Datetime()
    max_reminders = fields.Integer()
    update_cv_date = fields.Datetime()

    def cron_requested_changes(self):
        applicants = self.env['hr.applicant'].search([('date_cv_request', '!=', None), ('max_reminders', '>', 0)])
        for applicant in applicants:
            if datetime.now() >= applicant.date_cv_request:
                applicant.send_update_mail()
                applicant.write({
                    'date_cv_request': datetime.now() + timedelta(days=7),
                    'max_reminders': applicant.max_reminders - 1,
                })

    def cron_replay_requested(self):
        applicants = self.env['hr.applicant'].search([('update_cv_date', '!=', False)])
        for applicant in applicants:
            if applicant.update_cv_date > applicant.date_cv_request and datetime.now() >= applicant.update_cv_date + timedelta(
                    hours=2):
                rcs = self.env['requested.changes'].search([('applicant', '=', applicant.id)])
                for rc in rcs:
                    vals = {
                        'subject': 'Applicant:' + applicant.partner_name,
                        'body_html': 'The request for update Cv has been completed,Please check it <a href="' + applicant.sudo().get_url() + '">here</a>',

                        'email_to': rc.recruiter.partner_id.email,
                        'auto_delete': False,
                        'email_from': applicant.email_from,
                    }

                    mail_id = self.env['mail.mail'].sudo().create(vals)
                    mail_id.sudo().send()
                    rc.unlink()
                applicant.write({
                    'date_cv_request': None,
                    'max_reminders': 0,
                })


class HrApplicantSale(models.Model):
    _inherit = 'res.partner'

    def check_ids(self):
        applicants = self.env['hr.applicant'].sudo().search([('categ_ids.name', 'ilike', self.category_id.name)])
        for applicant in applicants:
            print(applicant)
        print(self.category_id.name)
        return applicants

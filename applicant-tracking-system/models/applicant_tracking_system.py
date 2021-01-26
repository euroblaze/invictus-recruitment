from odoo import models, fields, api
import os
import json
import logging
import datetime
import psycopg2

_logger = logging.getLogger(__name__)


def get_all_languages_data():
    path_all_languages = os.path.abspath(os.path.dirname(__file__))
    languages_json_file = os.path.join(path_all_languages, "../static/src/json/all_languages.json")
    with open(languages_json_file) as f:
        all_languages_dict = json.load(f)

    all_languages_data = []
    for key in all_languages_dict:
        all_lang_json = {"shortName": key, "longName": all_languages_dict[key]}
        all_languages_data.append(all_lang_json)

    return all_languages_data


def get_all_languages_tuples():
    list_of_languages_tuples = []
    all_languages = get_all_languages_data()
    for lang in all_languages:
        lang_tuple = (lang['longName'], lang['longName'])
        list_of_languages_tuples.append(lang_tuple)

    list_of_languages_tuples.sort()

    return list_of_languages_tuples


class ApplicantTrackingSystem(models.Model):
    _inherit = "hr.applicant"
    education = fields.One2many('hr.applicant.education', 'applicant_id', 'Education')

    certificates = fields.Text(string='Certificates', store=True)
    languages = fields.One2many('hr.applicant.language', 'applicant_id', string='Languages')
    key_skills = fields.Text(string='Key skills', store=True)
    experience_ids = fields.One2many('hr.applicant.experience', 'applicant_id', 'Experience')
    first_time = fields.Boolean(string="First time user", default=False)
    pdf_name_anonymous = fields.Char(compute="_get_default_name_anonymous")
    pdf_name_applicant = fields.Char(compute="_get_default_name_applicant")
    years_of_experience = fields.Integer(string='Years of experience', compute="_compute_years_of_experience",
                                         store=False)
    mounts_of_experience = fields.Integer(string='Years of experience', compute="_compute_years_of_experience",
                                          store=False)
    web_name = fields.Char(compute="_get_web_name")

    def date_difference_1(self, start):
        end = datetime.date.today()
        helper = end - start
        if type(helper) == int:
            experience = float(helper) / 365.0
        else:
            experience = round((end - start) / datetime.timedelta(365, 0, 0, 0), 2)
        return experience

    @api.depends('experience_ids')
    def _compute_years_of_experience(self):
        for p in self:
            experience = 0.0
            if p.experience_ids:
                list_start_date = []
                for exp in p.experience_ids:
                    if exp.start_date:
                        list_start_date.append(exp.start_date)
                if list_start_date:
                    _logger.info(list_start_date)
                    min_date = min(list_start_date)
                    experience = p.date_difference_1(min_date)
                    p.years_of_experience = int(experience)
                    p.mounts_of_experience = int((experience - int(experience)) * 12)
                else:
                    p.years_of_experience = 0
                    p.mounts_of_experience = 0
            else:
                p.years_of_experience = 0
                p.mounts_of_experience = 0

    @api.depends('partner_name')
    def _get_web_name(self):
        for p in self:
            name = str(p.partner_name).split()
            if len(name) >= 2:
                p.web_name = name[0] + " " + name[1][0]
            else:
                p.web_name = name[0]

    @api.model
    def _get_default_name_anonymous(self):

        helper = str(self.partner_name)
        print(self)
        stripped = helper.split()
        number = len(stripped)
        name = stripped[0]
        if number == 1:
            surname = str(" ")
        else:
            surname = stripped[1]
        surname_first = surname[:1]
        number = self.id
        number_six = "{0:06}".format(number)
        pdf_name_string = str(number_six) + "-" + name + "-" + surname_first
        self.pdf_name_anonymous = pdf_name_string

    @api.model
    def _get_default_name_applicant(self):

        helper = str(self.partner_name)
        print(self)
        stripped = helper.split()
        number = len(stripped)
        name = stripped[0]
        if number == 1:
            surname = str(" ")
        else:
            surname = stripped[1]
        pdf_name_string = name + "-" + surname
        self.pdf_name_applicant = pdf_name_string

    def encode(self, n):
        y = n * 14781
        alphabet0 = {"1": "Z", "2": "1", "3": "V", "4": "t", "5": "6", "6": "p", "7": "N", "8": "l", "9": "J", "0": "h"}
        alphabet1 = {"1": "a", "2": "C", "3": "0", "4": "G", "5": "i", "6": "K", "7": "m", "8": "O", "9": "6", "0": "S"}
        code = ""
        flag = 0
        while y:
            s = y % 10
            if flag == 0:
                code = code + alphabet0[str(s)]
                flag = 1
            else:
                code = code + alphabet1[str(s)]
                flag = 0
            y //= 10
        return code

    def json_data(self):
        r_data = {"certificates": self.certificates, "key_skills": self.key_skills, "email_from": self.email_from,
                  "partner_name": self.partner_name, "partner_phone": self.partner_phone,
                  "partner_mobile": self.partner_mobile, "url": "/updateCV/" + self.encode(self.id),
                  "description": self.description, "title_name": self.name}
        date_time_obj = self.write_date
        r_data["date_update"] = date_time_obj.date()

        helper = str(self.partner_name)
        stripped = helper.split()
        number = len(stripped)

        name = stripped[0]
        if number == 1:
            surname = str(" ")
        else:
            surname = stripped[1]
        surname_first = surname[:1]
        number = self.id
        "{0:06}".format(number)
        r_data["name"] = name + ' ' + surname_first

        experiences = self.env["hr.applicant.experience"].search([("applicant_id", "=", self.id)])
        experiences_data = []
        for experience in experiences:
            experience_json = {"id": str(experience.id), "title": experience.title, "start_date": experience.start_date,
                               "end_date": experience.end_date, "company": experience.company,
                               "location": experience.location, "projects": experience.projects,
                               "project_in_work": experience.project_in_work}
            experiences_data.append(experience_json)

        educations = self.env["hr.applicant.education"].search([("applicant_id", "=", self.id)])
        education_data = []
        for education in educations:
            education_json = {"id": str(education.id), 'type': education.type, 'university': education.university,
                              'faculty': education.faculty, 'school': education.school, 'degree': education.degree,
                              'field_of_study': education.field_of_study, 'grade': education.grade,
                              'from_date': education.from_date, 'to_date': education.to_date,
                              'education_in_progress': education.education_in_progress}
            education_data.append(education_json)

        languages = self.env["hr.applicant.language"].search([("applicant_id", "=", self.id)])

        language_data = []
        for language in languages:
            language_json = {'id': str(language.id), 'language': language.language, 'proficiency': language.proficiency}
            language_data.append(language_json)

        r_data["education"] = education_data
        r_data["experience"] = experiences_data
        r_data["language"] = language_data

        all_languages_data = get_all_languages_data()
        r_data["all_languages"] = all_languages_data

        return r_data

    def get_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + "/updateCV/" + self.encode(self.id)
        return url

    def send_update_mail(self):
        if self.first_time:
            template = self.env.ref('applicant_tracking_system.mail_updateCV_first_time')
            self.env['mail.template'].browse(template.id).send_mail(self.id)
            self.first_time = False
        else:
            template = self.env.ref('applicant_tracking_system.mail_updateCV')
            self.env['mail.template'].browse(template.id).send_mail(self.id)

    def send_recomend_mail(self):
        view_id = self.env.ref('applicant_tracking_system.suggest_view').id
        template = self.env.ref('applicant_tracking_system.mail_suggest')
        return {
            'name': 'suggest_view',
            'view_type': 'form',
            'views': [(view_id, 'form')],
            'res_model': 'mail.compose.message',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'applicant_id': self.id, 'default_template_id': template.id}
        }

    def get_interval(self):
        settings = self.env["hr.recruitment.automation.settings"].search([('id', '=', 1)])
        return settings.interval

    def send_update_mail_all(self):
        applicants = self.env["hr.applicant"].search([])
        for applicant in applicants:
            if applicant.active:
                applicant.send_update_mail()

    def multiple_update_cvs(self, ids):
        for id in ids:
            applicant = self.env["hr.applicant"].search([('id', '=', id)])
            applicant.send_update_mail()

    def report_button(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'applicant_tracking_system.applicantCV',
            'model': 'courses.courses',
            'report_type': "qweb-html",
            'name': "applicant_tracking_system.anonymousCV",
            'file': "applicant_tracking_system.anonymousCV"
        }


class ApplicantExperience(models.Model):
    _name = "hr.applicant.experience"
    _order = "start_date desc, end_date desc"
    _description = 'Hr applicant experience'
    applicant_id = fields.Many2one('hr.applicant')
    title = fields.Char(store=True)
    start_date = fields.Date(store=True)
    end_date = fields.Date(store=True)
    company = fields.Char(store=True)
    location = fields.Char(store=True)
    projects = fields.Text(store=True)
    project_in_work = fields.Boolean(store=True, default=False)

    @api.onchange('project_in_work')
    def change_end_date(self):
        if self.project_in_work:
            self.end_date = False


class AutomationSettings(models.Model):
    _name = "hr.recruitment.automation.settings"
    interval = fields.Integer(string="Update interval", store=True, default=6)
    name = fields.Char(default="Automation Settings")

    @api.model
    def create_default(self):
        self.create(dict())

    @api.onchange('interval')
    def change_interval(self):
        self.env.ref('applicant_tracking_system.send_update_mail_cron').write({'interval_number': self.interval})


class HrApplicantEducation(models.Model):
    _name = "hr.applicant.education"
    _order = "from_date desc, to_date desc"
    _description = 'Hr applicant education'
    applicant_id = fields.Many2one('hr.applicant')

    type = fields.Selection([('university', 'University'),
                             ('high_school', 'High School'),
                             ('course', 'Course')], string="Type of education")

    university = fields.Char(string="University")
    faculty = fields.Char(string="Faculty")

    school = fields.Char(string="School")
    degree = fields.Char(string="Degree")
    field_of_study = fields.Char(string="Field of study")
    grade = fields.Float(string="Grade")
    from_date = fields.Date(string="From")
    to_date = fields.Date(string="To(or expected)")
    education_in_progress = fields.Boolean(string="Education in progress", store=True)


class HrApplicantLanguages(models.Model):
    _name = 'hr.applicant.language'
    _description = 'Hr applicant languages'
    applicant_id = fields.Many2one('hr.applicant')

    language = fields.Selection(get_all_languages_tuples(), string="Language")

    proficiency = fields.Selection([('Elementary proficiency', 'Elementary proficiency'),
                                    ('Limited working proficiency', 'Limited working proficiency'),
                                    ('Professional working proficiency', 'Professional working proficiency'),
                                    ('Full professional proficiency', 'Full professional proficiency'),
                                    ('Native or bilingual proficiency', 'Native or bilingual proficiency')],
                                   string="Proficiency")

from odoo import http, api
import logging
import datetime

_logger = logging.getLogger(__name__)


class UpdateCV(http.Controller):

    def decode(self, n):
        alphabet0 = {"Z": "1", "1": "2", "V": "3", "t": "4", "6": "5", "p": "6", "N": "7", "l": "8", "J": "9", "h": "0"}
        alphabet1 = {"a": "1", "C": "2", "0": "3", "G": "4", "i": "5", "K": "6", "m": "7", "O": "8", "6": "9", "S": "0"}
        letters = list(n)
        flag = 0
        pos = 1
        y = 0
        for letter in letters:
            if flag == 0:
                try:
                    y = y + int(alphabet0[letter]) * pos
                    pos = pos * 10
                    flag = 1
                except KeyError:
                    _logger.error("Wrong Code")
                    return False
            else:
                try:
                    y = y + int(alphabet1[letter]) * pos
                    pos = pos * 10
                    flag = 0
                except KeyError:
                    _logger.error("Wrong Code")
                    return False

        y = y / 14781
        return y

    @http.route('/updateCV/<id>', type='http', auth='public', website=True, methods=['GET'])
    def render_cv_tempalte(self, id, **kw):
        id_decode = self.decode(id)

        if id_decode:
            applicant = http.request.env['hr.applicant'].sudo().search([('id', '=', int(id_decode))])
            data = applicant.json_data()
            if 'update' in kw:
                data['update'] = kw['update']

            return http.request.render('applicant_tracking_system.updateCV_page', data)

        else:
            return http.request.not_found(description=None)

    @http.route('/updateCV/<id>', type='http', auth="public", website=True, methods=['POST'])
    def update_applicant(self, **kw):
        data = kw
        id_decode = self.decode(data['id'])
        applicant = http.request.env['hr.applicant'].sudo().search([('id', '=', int(id_decode))])
        applicant.write({'update_cv_date': datetime.datetime.now()})

        if data['action'] == "update_contact":

            vals = {'email_from': data['email_from'],
                    'partner_mobile': data['partner_mobile'],
                    'partner_phone': data['partner_phone']
                    }
            applicant.write(vals)

        elif data['action'] == "update_education":

            applicant_educations = http.request.env["hr.applicant.education"].sudo().search(
                [("applicant_id", "=", applicant.id)])

            for education in applicant_educations:
                education_id = str(education.id)

                education_vals = {'university': data['university' + '-' + education_id],
                                  'faculty': data['faculty' + '-' + education_id],
                                  'school': data['school' + '-' + education_id],
                                  'degree': data['degree' + '-' + education_id],
                                  'field_of_study': data['field_of_study' + '-' + education_id],
                                  'from_date': data['from_date' + '-' + education_id],
                                  'to_date': data['to_date' + '-' + education_id],
                                  }
                education.write(education_vals)

        elif data['action'] == "update_experience":

            applicant_experience = http.request.env["hr.applicant.experience"].sudo().search(
                [("applicant_id", "=", applicant.id)])

            for experience in applicant_experience:
                experience_id = str(experience.id)

                experience_vals = {'title': data['title' + '-' + experience_id],
                                   'start_date': data['start_date' + '-' + experience_id],
                                   'end_date': data['end_date' + '-' + experience_id],
                                   'company': data['company' + '-' + experience_id],
                                   'location': data['location' + '-' + experience_id],
                                   'projects': data['projects' + '-' + experience_id]
                                   }

                experience.write(experience_vals)

        elif data['action'] == "update_accomplishments":

            vals = {'languages': data['languages'],
                    'certificates': data['certificates'],
                    'key_skills': data['key_skills'],
                    'description': data['description']
                    }
            applicant.write(vals)

        elif data['action'] == "new_experience":

            new_experience = http.request.env['hr.applicant.experience']

            experience_vals = {'applicant_id': int(id_decode),
                               'title': data['title'],
                               'start_date': data['start_date'],
                               'end_date': data['end_date'],
                               'company': data['company'],
                               'location': data['location'],
                               'projects': data['projects']
                               }

            new_experience.create(experience_vals)

            new_page = data['id']
            return self.render_cv_tempalte(new_page)

        elif data['action'] == "new_university":

            new_education = http.request.env['hr.applicant.education']

            uni_vals = {'applicant_id': int(id_decode),
                        'type': 'university',
                        'university': data['university'],
                        'faculty': data['faculty'],
                        'degree': data['degree'],
                        'from_date': data['from_date'],
                        'to_date': data['to_date']
                        }

            new_education.create(uni_vals)

            new_page = data['id']
            return self.render_cv_tempalte(new_page)

        elif data['action'] == "new_high_school":

            new_education = http.request.env['hr.applicant.education']

            uni_vals = {'applicant_id': int(id_decode),
                        'type': 'high_school',
                        'school': data['school'],
                        'field_of_study': data['field_of_study'],
                        'from_date': data['from_date'],
                        'to_date': data['to_date']
                        }

            new_education.create(uni_vals)

            new_page = data['id']
            return self.render_cv_tempalte(new_page)

        elif data['action'] == "new_course":

            new_education = http.request.env['hr.applicant.education']

            uni_vals = {'applicant_id': int(id_decode),
                        'type': 'course',
                        'school': data['school'],
                        'degree': data['degree'],
                        'field_of_study': data['field_of_study'],
                        'from_date': data['from_date'],
                        'to_date': data['to_date']
                        }

            new_education.create(uni_vals)

            new_page = data['id']
            return self.render_cv_tempalte(new_page)

        elif data['action'] == "update_languages":

            applicant_languages = http.request.env["hr.applicant.language"].sudo().search(
                [("applicant_id", "=", applicant.id)])

            for language in applicant_languages:
                id = str(language.id)

                language_vals = {'language': data['language' + '-' + id],
                                 'proficiency': data['proficiency' + '-' + id],
                                 }
                language.write(language_vals)

        elif data['action'] == "new_language":

            new_language = http.request.env["hr.applicant.language"]

            language_vals = {'applicant_id': int(id_decode),
                             'language': data['language'],
                             'proficiency': data['proficiency'],
                             }

            new_language.create(language_vals)

            new_page = data['id']
            return self.render_cv_tempalte(new_page)

        else:
            data["applicant_id"] = self.decode(data['id'])
            new_page = data['id']
            del data['id']
            del data['action']
            http.request.env['hr.applicant.experience'].sudo().create(data)
            return self.render_cv_tempalte(new_page)

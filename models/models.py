# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api, exceptions, _


class Course(models.Model):
    _name = 'openacademy.course'
    _description = 'Openacademy Courses'

    #user=fields.Char(string="User",default=lambda self:self.env.user)
    name = fields.Char(string="Title", required=True)
    description = fields.Text()
    responsible_id = fields.Many2one('res.users',ondelete='set null', string="Responsible", index=True)
    session_ids = fields.One2many('openacademy.session','course_id', string="Sessions")

    def copy(self, default=None):
        default = dict(default or {})
        copied_count = self.search_count(
         [('name', '=like', _(u"Copy of {}%").format(self.name))])

        if not copied_count:
            #new_name = u"Copy of {}".format(self.name)
            new_name = _(u"Copy of {}").format(self.name)
        else:
            #new_name = u"Copy of {} ({})".format(self.name, copied_count)
            new_name = _(u"Copy of {} ({})").format(self.name, copied_count)
        default['name'] = new_name #?????
        return super(Course, self).copy(default)#????//????/
    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "The title of the course should not be the description"),

        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
    ]

class Session(models.Model):
    _name = 'openacademy.session'
    _description = "OpenAcademy Sessions"

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    #degit mean 6=nbr total des chiffres apres la virgule et 2=nbr chiffre apres la virgule
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    color = fields.Integer()
    instructor_id = fields.Many2one('res.partner', string="Instructor",domain=['|', ('instructor', '=', True),('category_id.name', 'ilike', "Teacher")])
    course_id = fields.Many2one('openacademy.course',ondelete='cascade', string="Course", required=True)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')
    end_date = fields.Date(string="End Date", store=True, compute='_get_end_date', inverse='_set_end_date')
    attendees_count = fields.Integer(string="Attendees count", compute='_get_attendees_count', store=True)
    price_per_hour = fields.Integer(help="Price")
    total = fields.Integer(help="total", compute='calc_total')
    price_session = fields.Integer(string="Price for session")
    date = fields.Date(required=True, default=fields.Date.context_today)
    state = fields.Selection([
        ('draft', "DRAFT"),
        ('confirm', "CONFIRM"),
        ('validate', "VALIDATE"), ], default='draft', string='State')
    button_clicked = fields.Boolean(string='facturee')
    invoice_ids = fields.One2many("account.move", "session_id")#session_id??????
    invoice_count = fields.Integer(string="count invoice", compute="_compute_invoice_count")
    # This function is triggered when the user clicks on the button 'Set to started'

    def _compute_invoice_count(self):
        self.invoice_count = self.env['account.move'].search_count([('session_id', '=', self.id)])
# *************facture fournisseur=instructor***************************
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_invoice',
        }

        action['context'] = context
        return action
    #********************** facture client*************************

    def facturer(self):
        self.button_clicked = True
        #data= les donnes envoyes au facturaion
        data = {
            'session_id': self.id,
            'partner_id': self.instructor_id.id,
            'type': 'in_invoice',
            # 'partner_shipping_id': self.instructor_id.address,
            'invoice_date': self.date,
            "invoice_line_ids": [],
        }

        line = {
            "name": "session",
            "quantity": self.duration,
            "price_unit": self.price_per_hour,

        }
        data["invoice_line_ids"].append((0, 0, line))
        invoice = self.env['account.move'].create(data)


    # This function is triggered when the user clicks on the button 'Done'
    def valide_progressbar(self):
        self.write({
            'state': 'validate',
        })
    def confirm_progressbar(self):
        self.write({
            'state': 'confirm'
        })
    def calc_total(self):
        self.total = self.duration * self.price_per_hour
    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats
    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': _("Incorrect 'seats' value"),
                    'message': _("The number of available seats may not be negative"),

                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': _("Too many attendees"),
                    'message': _("Increase seats or remove excess attendees"),

                },
            }
    @api.depends('start_date', 'duration')
    def _get_end_date(self):
            for r in self:
                if not (r.start_date and r.duration):
                    r.end_date = r.start_date
                    continue

                # Add duration to start_date, but: Monday + 5 days = Saturday, so
                # subtract one second to get on Friday instead
                duration = timedelta(days=r.duration, seconds=-1)
                r.end_date = r.start_date + duration

    def _set_end_date(self):
            for r in self:
                if not (r.start_date and r.end_date):
                    continue

                # Compute the difference between dates, but: Friday - Monday = 4 days,
                # so add one day to get 5 days instead
                r.duration = (r.end_date - r.start_date).days + 1
    @api.depends('attendee_ids')
    def _get_attendees_count(self):
           for r in self:
               r.attendees_count = len(r.attendee_ids)
    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
            for r in self:
                if r.instructor_id and r.instructor_id in r.attendee_ids:
                    raise exceptions.ValidationError("A session's instructor can't be an attendee")

#

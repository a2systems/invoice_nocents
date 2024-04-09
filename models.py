from odoo import tools, models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime


class AccountMove(models.Model):
    _inherit = "account.move"

    def create_adjcents_payment(self):
        for rec in self:
            if rec.move_type == 'out_invoice' and rec.state == 'posted' and rec.amount_residual > 0:
                nocents_adj_parm = self.env['ir.config_parameter'].get_param('AJUSTE_CENTAVOS',1)
                if rec.currency_id.id == rec.company_id.currency_id.id and rec.amount_residual < float(nocents_adj_parm):
                    journal_id = self.env['account.journal'].search([('code','=','ADJCE')],limit=1)
                    if not journal_id:
                        raise ValidationError('No hay diario ADJCE')
                    vals_payment = {
                        'partner_id': rec.partner_id.id,
                        'journal_id': journal_id.id,
                        'date': str(date.today()),
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'amount': rec.amount_residual,
                        'ref': 'AJUSTE CENTAVOS %s'%(rec.display_name),
                        }
                    payment_id = self.env['account.payment'].create(vals_payment)
                    payment_id.action_post()
                    aml_obj = self.env['account.move.line']
                    for move_line in rec.line_ids:
                        if move_line.account_id.account_type == 'asset_receivable':
                            aml_obj += move_line
                    for move_line in payment_id.line_ids:
                        if move_line.account_id.account_type == 'asset_receivable':
                            aml_obj += move_line
                    aml_obj.reconcile()
        return True

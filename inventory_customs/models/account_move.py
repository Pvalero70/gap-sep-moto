# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
_log = logging.getLogger("___name: %s" % __name__)


class AccountMoveItt(models.Model):
    _inherit = "account.move"

    def _print_moto_details(self):
        """
        Check if this invoice is for moto product, and some rules (like only one product)
        only one product for this kind of product.
        :return: True if is an invoice for moto, False else.
        """
        # Only one line.
        # if self.invoice_line_ids and len(self.invoice_line_ids.ids) > 1:
        #     return False
        moto_lines = self.invoice_line_ids.filtered(lambda p: p.product_id.product_inv_categ in ["moto", "Moto"])
        if moto_lines and len(moto_lines.ids) == len(self.invoice_line_ids.ids):
            return True
        return False

    def _get_invoiced_lot_values_tt(self):
        # Poner aquí la restricción de la compañia.
        if self.move_type != "out_invoice" or self.state == 'draft':
            return False
        sale_lines = self.invoice_line_ids.sale_line_ids
        # Filter lines for specific product
        stock_move_lines = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids
        # Buscamos un stock.move.line que tenga el lot_id que buscamos. el stock.move.line tiene picking_id y
        # éste a su vez tiene el resto de campos que deben ser mostrados.
        data = []
        _log.info(" STOCK MOVE LINES from ACCOUNT MOVE ::: %s " % stock_move_lines)
        for line in stock_move_lines:
            if not line.product_id.product_inv_categ or not line.product_id.product_inv_categ in ["moto", "Moto"]:
                continue
            # Put: color; inv num,
            data.append({
                'product_name': line.lot_id.product_id.name,
                'serial': line.lot_id.name,
                'motor_num': line.lot_id.tt_number_motor,
                'color': line.lot_id.tt_color,
                'inv_num': line.lot_id.tt_inventory_number,
                'brand': line.product_id.brand_id.name,
                'model': line.product_id.moto_model,
                'moto_cil': line.product_id.moto_cilindros,
                'moto_motor': line.product_id.moto_motor,
                'moto_desp': line.product_id.moto_despl,
                'moto_line': line.product_id.categ_id.name,
                'clave': line.product_id.default_code,
                'aduana': line.picking_id.tt_aduana,
                'aduana_date': line.picking_id.tt_aduana_date_in
            })

        if len(data) > 0:
            return data
        # Si no se origina en sale.order, entonces pos.order:..
        if not self.pos_order_ids:
            return False
        pols = self.pos_order_ids.mapped('lines').mapped('pack_lot_ids')
        # Get all stock production lot  records in the same query.
        lot_domains = [
            ('name', 'in', pols.mapped('lot_name')),
            ('product_id', 'in', pols.mapped('product_id').ids),
        ]
        ori_lots = self.env['stock.production.lot'].search(lot_domains)
        _log.info("\nORI LOTS FOUND:::  %s " % ori_lots)
        if not ori_lots:
            return False
        sml_ids = self.env['stock.move.line'].search([('lot_id', 'in', ori_lots.ids)])
        _log.info("\nORI STOCK MOVE LINES  FOUND:::  %s " % sml_ids)
        for pol in pols:
            # lot_domain = [
            #     ('name', '=like', pol.lot_name),
            #     ('product_id', '=', pol.product_id.id),
            #     # ('company_id', '=', pol.company_id.id)
            # ]
            # ori_lot = self.env['stock.production.lot'].search(lot_domain)
            ori_lot = ori_lots.filtered(lambda x: x.name == pol.lot_name and x.product_id.id == pol.product_id.id)
            _log.info("\nLOT FOUND:: %s " % ori_lot)
            sml_id = sml_ids.filtered(lambda r: r.lot_id.id == ori_lot.id)
            _log.info("\nSTOCK MOVE LINE ONE FOUND:: %s " % sml_id)
            # BUscar un stock.move.line que tenga como lot_id el que se acaba de encontrar.
            # el stock.move.line ya tiene un picking asociado.
            if not ori_lot:
                continue
            data.append({
                'product_name': ori_lot.product_id.name,
                'serial': ori_lot.name,
                'motor_num': ori_lot.tt_number_motor,
                'color': ori_lot.tt_color,
                'inv_num': ori_lot.tt_inventory_number,
                'brand': ori_lot.product_id.brand_id.name,
                'model': ori_lot.product_id.moto_model,
                'moto_cil': ori_lot.product_id.moto_cilindros,
                'moto_motor': ori_lot.product_id.moto_motor,
                'moto_desp': ori_lot.product_id.moto_despl,
                'moto_line': ori_lot.product_id.categ_id.name,
                'clave': ori_lot.product_id.default_code,
                'aduana': sml_id.picking_id.tt_aduana,
                "aduana_date": sml_id.picking_id.tt_aduana_date_in,
            })

        if len(data) > 0:
            return data
        return False

    def _set_num_pedimento(self):
        # Filter by current company HERE.

        if self.move_type != "out_invoice" or self.state == 'draft':
            return False
        # From sale order
        if self.invoice_line_ids:
            sale_lines = self.invoice_line_ids.sale_line_ids
            lot_ids = sale_lines.move_ids.filtered(lambda r: r.state == 'done').move_line_ids.mapped('lot_id')

        # From pos order.
        elif self.pos_order_ids:
            lots = self.pos_order_ids.mapped('lines').mapped('pack_lot_ids')

            lot_domain = [
                ('name', 'in', lots.mapped('lot_name')),
                ('product_id', 'in', lots.mapped('product_id').ids),
            ]
            lot_ids = self.env['stock.production.lot'].search(lot_domain)

        for line in self.invoice_line_ids:
            lot = lot_ids.filtered(lambda x: x.product_id.id == line.product_id.id)[:1]

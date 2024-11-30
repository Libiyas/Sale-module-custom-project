from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    manager_reference = fields.Char(
        string='Manager Reference',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    )

    auto_workflow = fields.Boolean(string='Auto Workflow')

    picking_ids = fields.One2many(
        'stock.picking', 'sale_id',
        string='Pickings',
    )

    delivery_count = fields.Integer(
        string='Delivery Orders',
        compute='_compute_delivery_count',
        store=True
    )

    effective_date = fields.Date(
        string='Effective Date',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help="The date when this sale order becomes effective"
    )

    @api.constrains('amount_total')
    def _check_sale_order_limit(self):
        """
        Validate that the sale order amount doesn't exceed the configured limit
        for non-admin users.
        """
        if self.env.user.has_group('sale_admin_extension.group_sale_admin'):
            return
        limit = self.env['ir.config_parameter'].sudo().get_param('sale_order_limit', default=0.0)
        for order in self:
            if order.amount_total > float(limit):
                raise ValidationError(
                    _('You cannot confirm this Sale Order as it exceeds the Sale Order Limit.')
                )

    @api.depends('picking_ids')
    def _compute_delivery_count(self):
        """Compute the number of delivery orders associated with this sale order."""
        for order in self:
            order.delivery_count = len(order.picking_ids.filtered(lambda p: p.state != 'cancel'))

    def action_confirm(self):
        """Extend the standard confirmation to handle auto workflow if enabled."""
        super(SaleOrder, self).action_confirm()
        if self.auto_workflow:
            self._process_auto_workflow()

    def _process_auto_workflow(self):
        """
        Process automatic workflow for confirmed sales orders.
        Creates and validates delivery orders automatically.
        """
        self.ensure_one()
        picking_groups = {}
        for line in self.order_line:
            key = (line.product_id, line.warehouse_id)
            if key not in picking_groups:
                picking_groups[key] = self.env['stock.picking'].create({
                    'partner_id': self.partner_id.id,
                    'origin': self.name,
                    'picking_type_id': self.env.ref('stock.picking_type_out').id,
                    'location_id': self.warehouse_id.lot_stock_id.id,
                    'location_dest_id': self.partner_id.property_stock_customer.id,
                })
            self.env['stock.move'].create({
                'name': line.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'picking_id': picking_groups[key].id,
                'location_id': picking_groups[key].location_id.id,
                'location_dest_id': picking_groups[key].location_dest_id.id,
            })
        for picking in picking_groups.values():
            picking.action_confirm()
            picking.action_assign()
            picking.button_validate()

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_order_limit = fields.Float(
        string="Sale Order Limit",
        config_parameter='sale.sale_order_limit',
        help="Set the maximum sale order amount. Only Sale Admins can confirm orders exceeding this limit."
    )
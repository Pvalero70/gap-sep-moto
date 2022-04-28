odoo.define('pos_customs.OrderReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');

    const OrderReceipt2 = (OrderReceipt) =>
        class extends OrderReceipt {
        get sale_seller() {
//            Get the first line to get user of sale.order object.
            console.log(this);
            console.log(this.orderlines[0]);

            sale_order = this.orderlines[0].sale_order_origin_id;
            console.log(sale_order);
            so_user = this.orderlines[0].sale_order_origin_id.user_id;
            if(so_user == undefined){
                return "-";
            }
            else{
                console.log(so_user.[1]);
                var seller_name = this.orderlines[0].sale_order_origin_id.user_id[1];
                return seller_name;
            }
        }
    }

    Registries.Component.extend(OrderReceipt, OrderReceipt2);
});

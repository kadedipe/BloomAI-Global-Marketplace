# BloomAI commerce fulfillment workflow

This stage extends the marketplace order foundation with inventory, fulfillment, shipment tracking, receipts and refund controls.

## Inventory and availability

Vendors may optionally track inventory per listing. A blank inventory quantity means stock is not tracked. A quantity of `0` blocks checkout as sold out. Vendors may also pause a listing with `is_active=false` without deleting it.

Tracked inventory is reserved when checkout is initialized. Cancelling a pending order restores the reserved quantity. Checkout initialization is transactional: if Paystack initialization fails, the database transaction rolls back, including the inventory reservation.

## Fulfillment

Only paid orders may move through fulfillment. The supported lifecycle is:

`unfulfilled -> processing -> shipped -> delivered`

A carrier and tracking number are required when a vendor marks an order as shipped. Buyers receive in-app notifications when fulfillment changes.

Paid orders are not cancelled through the pending-order cancellation endpoint. They use the refund workflow instead.

## Refunds

The buyer may request a refund only after payment has been confirmed. The vendor may approve or reject the request. Approval does not directly alter payment records.

Actual provider refund execution is restricted to administrators and calls Paystack's refund API using the recorded provider transaction ID. The order is recorded as `processing` unless Paystack reports a terminal processed/refunded/success state. This prevents the application from claiming money has been returned before the payment provider confirms it.

## Receipts

Paid orders expose an authenticated receipt endpoint. Buyers, the selling vendor and administrators may access the receipt. The web UI renders a printable receipt using server-authoritative order totals and payment timestamps.

## Access controls

- Customers: buy products, inspect their orders, print receipts and request refunds.
- Vendors: all customer capabilities for other vendors' products, plus inventory controls, sales-order details, fulfillment updates and refund review for their own sales.
- Administrators: order oversight and provider refund execution.

A vendor cannot buy their own listing. Public administrator registration remains disabled.

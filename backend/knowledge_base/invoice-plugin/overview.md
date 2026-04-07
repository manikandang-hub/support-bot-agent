# Invoice Plugin - Overview

## About WebToffee Invoice, Packing Slip & Credit Note

WebToffee Invoice, Packing Slip & Credit Note is a comprehensive WooCommerce plugin for generating, managing, and emailing professional invoices, packing slips, and credit notes.

## Key Features

- Auto-generate invoices on order completion
- Professional PDF invoices
- Customizable invoice templates
- Automatic packing slip generation
- Credit notes for refunds
- Email automation
- Bulk operations
- Tax handling
- Sequential invoice numbering
- Multiple language support

## Hook System

The plugin provides hooks for customizing invoice content, items, and totals without modifying the core plugin.

## Common Customization Scenarios

### Modify Invoice Content
Use `wt_invoice_content` to customize the full invoice HTML:
```php
add_filter('wt_invoice_content', function($html, $invoice) {
    // Add custom header, footer, or styling
    return $html;
}, 10, 2);
```

### Filter Invoice Items
Use `wt_invoice_line_items` to modify items displayed:
```php
add_filter('wt_invoice_line_items', function($items, $order) {
    // Hide certain items, modify quantities, etc.
    return $items;
}, 10, 2);
```

### Customize Totals
Use `wt_invoice_totals` to modify subtotal, tax, shipping, and total:
```php
add_filter('wt_invoice_totals', function($totals, $invoice) {
    // Apply custom discounts, adjust taxes, etc.
    return $totals;
}, 10, 2);
```

### Customize Packing Slips
Use `wt_packing_slip_content` for packing slip modifications:
```php
add_filter('wt_packing_slip_content', function($html, $order) {
    // Custom packing instructions, branding, etc.
    return $html;
}, 10, 2);
```

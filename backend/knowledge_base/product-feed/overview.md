# Product Feed - Plugin Overview

## About WebToffee Product Feed Sync Manager Pro

WebToffee Product Feed Sync Manager Pro is a powerful WooCommerce plugin that allows merchants to sync their products to multiple sales channels including Amazon, eBay, Google Shopping, Facebook Catalog, and more.

## Key Features

- Multi-channel product synchronization
- Real-time inventory sync
- Automatic price updates
- Product mapping and field customization
- Feed scheduling and automation
- Channel-specific product filtering
- Bulk product operations
- Detailed sync reports

## Hook System

The plugin uses WordPress hooks to allow customization without modifying core plugin files. All customizations are done using `add_filter()` and `add_action()` functions in your theme's `functions.php` or a custom plugin.

## Common Customization Scenarios

### Filter Products Before Export
Use `wt_product_feed_filter_product` to modify product data:
```php
add_filter('wt_product_feed_filter_product', function($data, $product) {
    $data['description'] = 'Custom ' . $data['description'];
    return $data;
}, 10, 2);
```

### Skip Certain Products
Use `wt_product_feed_skip_product` to exclude products:
```php
add_filter('wt_product_feed_skip_product', function($skip, $product) {
    if ($product->get_price() < 10) {
        return true; // Skip cheap products
    }
    return $skip;
}, 10, 2);
```

### Run Actions Before/After Export
```php
add_action('wt_product_feed_before_export', function($feed_id) {
    // Prepare data, clear cache, etc.
});

add_action('wt_product_feed_after_export', function($feed_id, $feed_url) {
    // Send notification, log results, etc.
}, 10, 2);
```

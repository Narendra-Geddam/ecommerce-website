$ErrorActionPreference = 'Stop'

function Merge-Headers {
    param(
        [hashtable]$First,
        [hashtable]$Second
    )
    $merged = @{}
    if ($First) {
        foreach ($key in $First.Keys) { $merged[$key] = $First[$key] }
    }
    if ($Second) {
        foreach ($key in $Second.Keys) { $merged[$key] = $Second[$key] }
    }
    return $merged
}

function Invoke-JsonRequest {
    param(
        [string]$Method,
        [string]$Uri,
        [hashtable]$Headers = $null,
        $Body = $null
    )

    $params = @{
        Method = $Method
        Uri = $Uri
        TimeoutSec = 20
    }

    if ($Headers) {
        $params.Headers = $Headers
    }

    if ($null -ne $Body) {
        $params.ContentType = 'application/json'
        $params.Body = ($Body | ConvertTo-Json -Compress -Depth 8)
    }

    return Invoke-RestMethod @params
}

$csrf = (Invoke-RestMethod 'http://localhost/api/csrf-token').csrf_token

$adminEmail = 'admin@shopeasy.local'
$adminPassword = 'Admin1234'

try {
    $admin = Invoke-JsonRequest 'POST' 'http://localhost/api/register' @{ 'X-CSRF-Token' = $csrf } @{
        name = 'Admin User'
        email = $adminEmail
        password = $adminPassword
        phone = '9876543210'
        city = 'Bengaluru'
        state = 'Karnataka'
        pincode = '560001'
    }
} catch {
    $admin = Invoke-JsonRequest 'POST' 'http://localhost/api/login' @{ 'X-CSRF-Token' = $csrf } @{
        email = $adminEmail
        password = $adminPassword
    }
}

$userEmail = 'shopper-' + [guid]::NewGuid().ToString('N').Substring(0, 8) + '@example.com'
$userPassword = 'Shopper123'
$user = Invoke-JsonRequest 'POST' 'http://localhost/api/register' @{ 'X-CSRF-Token' = $csrf } @{
    name = 'Shopper User'
    email = $userEmail
    password = $userPassword
    phone = '9123456789'
    city = 'Mumbai'
    state = 'Maharashtra'
    pincode = '400001'
}

$adminAuth = @{ Authorization = "Bearer $($admin.access_token)" }
$userAuth = @{ Authorization = "Bearer $($user.access_token)" }
$csrfHeader = @{ 'X-CSRF-Token' = $csrf }

$adminMe = Invoke-RestMethod 'http://localhost/api/me' -Headers $adminAuth

$wishlistAdd = Invoke-JsonRequest 'POST' 'http://localhost/api/wishlist/add/1' (Merge-Headers $csrfHeader $userAuth) @{}
$wishlist = Invoke-RestMethod 'http://localhost/api/wishlist' -Headers $userAuth

$reviewPost = Invoke-JsonRequest 'POST' 'http://localhost/api/products/1/reviews' (Merge-Headers $csrfHeader $userAuth) @{
    rating = 5
    comment = 'Great phone and smooth checkout test.'
}
$reviews = Invoke-RestMethod 'http://localhost/api/products/1/reviews'

$cartAdd = Invoke-JsonRequest 'POST' 'http://localhost/api/cart/add/1' (Merge-Headers $csrfHeader $userAuth) @{
    quantity = 1
}
$coupon = Invoke-RestMethod 'http://localhost/api/coupons/validate?code=SAVE10&subtotal=69.99'
$productBefore = Invoke-RestMethod 'http://localhost/api/products/1'

$order = Invoke-JsonRequest 'POST' 'http://localhost/api/orders' (Merge-Headers $csrfHeader $userAuth) @{
    cart_id = $cartAdd.cart_id
    address = '42 Market Road'
    city = 'Mumbai'
    state = 'Maharashtra'
    pincode = '400001'
    phone = '9123456789'
    payment_method = 'cod'
    coupon_code = 'SAVE10'
}

$productAfterOrder = Invoke-RestMethod 'http://localhost/api/products/1'
$cancel = Invoke-JsonRequest 'POST' "http://localhost/api/orders/$($order.order_id)/cancel" (Merge-Headers $csrfHeader $userAuth) @{}
$productAfterCancel = Invoke-RestMethod 'http://localhost/api/products/1'

$adminOrders = Invoke-RestMethod 'http://localhost/api/admin/orders' -Headers $adminAuth
$inventoryList = Invoke-RestMethod 'http://localhost/api/admin/inventory' -Headers $adminAuth
$lowStock = Invoke-RestMethod 'http://localhost/api/admin/inventory/low-stock' -Headers $adminAuth
$restock = Invoke-JsonRequest 'POST' 'http://localhost/api/admin/inventory/restock' (Merge-Headers $csrfHeader $adminAuth) @{
    product_id = 1
    quantity = 2
    notes = 'Admin checkpoint restock'
}

[pscustomobject]@{
    admin_is_admin = $adminMe.is_admin
    wishlist_count = $wishlist.count
    review_count = $reviews.count
    coupon_valid = $coupon.valid
    order_total = $order.total
    order_discount = $order.discount
    product_stock_before = $productBefore.stock
    product_stock_after_order = $productAfterOrder.stock
    product_stock_after_cancel = $productAfterCancel.stock
    cancel_status = $cancel.status
    admin_orders_count = $adminOrders.orders.Count
    inventory_count = $inventoryList.count
    low_stock_count = $lowStock.count
    restock_added = $restock.quantity_added
} | ConvertTo-Json -Compress

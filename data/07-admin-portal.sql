-- Admin portal foundations: user moderation, product lifecycle, homepage banners, and offer blocks

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS is_banned BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS homepage_banners (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    subtitle TEXT,
    image_url VARCHAR(500),
    link_url VARCHAR(500),
    badge VARCHAR(100),
    background_color VARCHAR(50) DEFAULT '#1f3c88',
    text_color VARCHAR(50) DEFAULT '#ffffff',
    sort_order INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS homepage_offers (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    coupon_code VARCHAR(50),
    cta_label VARCHAR(100) DEFAULT 'Shop Now',
    cta_link VARCHAR(500) DEFAULT '/',
    highlight_text VARCHAR(100),
    sort_order INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_banned ON users(is_banned);
CREATE INDEX IF NOT EXISTS idx_homepage_banners_active_sort ON homepage_banners(active, sort_order);
CREATE INDEX IF NOT EXISTS idx_homepage_offers_active_sort ON homepage_offers(active, sort_order);

INSERT INTO homepage_banners (title, subtitle, image_url, link_url, badge, background_color, text_color, sort_order, active)
VALUES
    ('Big Savings Week', 'Upgrade your cart with curated picks and limited-time deals.', '/static/products/iphone12M1.jpg', '/?category=Mobiles', 'Up to 40% OFF', '#163b7a', '#ffffff', 1, TRUE),
    ('Style Store Refresh', 'New arrivals in fashion, beauty, and everyday essentials.', '/static/products/shirt.jpg', '/?category=Clothings', 'Fresh Finds', '#7a2f54', '#ffffff', 2, TRUE),
    ('Work From Home Picks', 'Desks, chairs, and laptops handpicked for productivity.', '/static/products/desk.jpg', '/?category=Furniture', 'Hot Right Now', '#24574f', '#ffffff', 3, TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO homepage_offers (title, description, coupon_code, cta_label, cta_link, highlight_text, sort_order, active)
VALUES
    ('Welcome Discount', 'Use a first-order offer at checkout and save instantly.', 'SAVE10', 'Use SAVE10', '/checkout.html', '10% OFF above $50', 1, TRUE),
    ('Premium Cart Bonus', 'Unlock a flat discount for larger baskets.', 'WELCOME25', 'Claim WELCOME25', '/checkout.html', '$25 OFF above $200', 2, TRUE),
    ('Track Fresh Deals', 'Browse recently updated catalog picks from every category.', NULL, 'Explore Products', '/', 'New drops daily', 3, TRUE)
ON CONFLICT DO NOTHING;

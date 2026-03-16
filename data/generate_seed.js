const fs = require('fs');
const data = JSON.parse(fs.readFileSync('C:/Users/don81/OneDrive/Desktop/demo/demo_data/data.json', 'utf8'));

// Map remote URLs to local paths
function getLocalImage(imgUrl) {
  const filename = imgUrl.split('/').pop();
  return '/static/products/' + filename;
}

// Generate SQL INSERT statements
let sql = `-- Products seed data for e-commerce
-- Run this after schema.sql to populate products

-- Clear existing products
DELETE FROM products;

-- Insert products from demo data
INSERT INTO products (name, description, price, image_url, category, stock) VALUES
`;

const values = data.products.map((p) => {
  const name = p.title.replace(/'/g, "''");
  // Handle specs - it might be an array or string
  let desc = p.title;
  if (p.specs && Array.isArray(p.specs) && p.specs.length > 0) {
    desc = p.specs.slice(0, 2).join(' | ');
  } else if (p.specs && typeof p.specs === 'string') {
    desc = p.specs.substring(0, 200);
  }
  desc = desc.replace(/'/g, "''").substring(0, 500); // Limit description length
  const price = p.price / 100; // Convert to dollars
  const img = getLocalImage(p.imgs[0]);
  const category = p.category;
  const stock = p.inStock || 100;

  return `('${name}', '${desc}', ${price.toFixed(2)}, '${img}', '${category}', ${stock})`;
});

sql += values.join(',\n') + '\nON CONFLICT (id) DO NOTHING;';

fs.writeFileSync('C:/Users/don81/OneDrive/Desktop/demo/data/seed_products.sql', sql);
console.log('Generated SQL for', data.products.length, 'products');
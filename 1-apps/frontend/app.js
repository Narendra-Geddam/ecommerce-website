/* ═══════════════════════════════════════════════
   MoreCraze — Shared Application Module
   ═══════════════════════════════════════════════ */

const APP = {
  name: 'MoreCraze',
  apiBase: '/api',
  user: null,
  cartCount: 0,
};

/* ── API Helper ── */
async function api(path, opts = {}) {
  const url = path.startsWith('/api') ? path : `${APP.apiBase}${path.startsWith('/') ? '' : '/'}${path}`;
  const res = await fetch(url, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, ...data };
  return data;
}

/* ── Toast Notifications ── */
function showToast(msg, type = 'info', duration = 3500) {
  let box = document.getElementById('toast-container');
  if (!box) {
    box = document.createElement('div');
    box.id = 'toast-container';
    document.body.appendChild(box);
  }
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerHTML = `<span>${msg}</span><button onclick="this.parentElement.remove()">&times;</button>`;
  box.appendChild(t);
  requestAnimationFrame(() => t.classList.add('show'));
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 400); }, duration);
}

/* ── Currency ── */
function formatPrice(n) { return '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }

/* ── Cart Badge ── */
async function updateCartBadge() {
  try {
    const d = await api('/cart/count');
    APP.cartCount = d.count || 0;
  } catch { APP.cartCount = 0; }
  document.querySelectorAll('.cart-badge').forEach(b => {
    b.textContent = APP.cartCount;
    b.style.display = APP.cartCount > 0 ? 'flex' : 'none';
  });
}

/* ── Auth Check ── */
async function checkAuth() {
  try {
    const d = await api('/me');
    if (d.authenticated) { APP.user = d; return d; }
  } catch {}
  APP.user = null;
  return null;
}

/* ── Add to Cart ── */
async function addToCart(id) {
  try {
    await api(`/cart/add/${id}`, { method: 'POST' });
    await updateCartBadge();
    showToast('Added to cart!', 'success');
  } catch { showToast('Failed to add', 'error'); }
}

/* ── Navbar ── */
function renderNavbar(activePage) {
  const nav = document.getElementById('main-nav');
  if (!nav) return;
  const user = APP.user;
  nav.innerHTML = `
    <div class="nav-inner">
      <a href="/" class="nav-logo">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#lg)" stroke-width="2"><defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#A855F7"/><stop offset="100%" stop-color="#F59E0B"/></linearGradient></defs><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>
        <span>More<em>Craze</em></span>
      </a>
      <div class="nav-links">
        <a href="/" class="${activePage==='home'?'active':''}">Home</a>
        ${user ? `<a href="/orders.html" class="${activePage==='orders'?'active':''}">Orders</a>` : ''}
        <a href="/monitor.html" class="${activePage==='monitor'?'active':''}">Monitor</a>
      </div>
      <div class="nav-actions">
        <a href="/cart.html" class="nav-cart ${activePage==='cart'?'active':''}">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>
          <span class="cart-badge" style="display:none">0</span>
        </a>
        ${user
          ? `<div class="nav-user-menu">
               <button class="nav-avatar">${user.name.charAt(0).toUpperCase()}</button>
               <div class="nav-dropdown">
                 <span class="dd-name">${user.name}</span>
                 <span class="dd-email">${user.email}</span>
                 <hr/>
                 <a href="/profile.html">Profile</a>
                 <a href="/orders.html">My Orders</a>
                 <button id="btn-logout">Logout</button>
               </div>
             </div>`
          : `<a href="/login.html" class="btn btn-sm btn-primary">Sign In</a>`}
      </div>
      <button class="nav-hamburger" onclick="document.getElementById('main-nav').classList.toggle('open')">
        <span></span><span></span><span></span>
      </button>
    </div>`;
  const lo = document.getElementById('btn-logout');
  if (lo) lo.addEventListener('click', async () => {
    await api('/logout', { method: 'POST' });
    APP.user = null;
    showToast('Logged out', 'info');
    window.location.href = '/';
  });
}

/* ── Footer ── */
function renderFooter() {
  const f = document.getElementById('main-footer');
  if (!f) return;
  f.innerHTML = `
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="nav-logo"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="url(#lg2)" stroke-width="2"><defs><linearGradient id="lg2" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#A855F7"/><stop offset="100%" stop-color="#F59E0B"/></linearGradient></defs><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg> More<em>Craze</em></span>
        <p>Premium e-commerce experience. Built with modern web technologies.</p>
      </div>
      <div class="footer-links">
        <h4>Shop</h4>
        <a href="/">All Products</a><a href="/?cat=Mobiles">Mobiles</a><a href="/?cat=Laptops">Laptops</a><a href="/?cat=Books">Books</a>
      </div>
      <div class="footer-links">
        <h4>Account</h4>
        <a href="/profile.html">Profile</a><a href="/orders.html">Orders</a><a href="/cart.html">Cart</a>
      </div>
      <div class="footer-links">
        <h4>System</h4>
        <a href="/monitor.html">Monitor</a><a href="/health">Health</a>
      </div>
    </div>
    <div class="footer-bottom"><p>&copy; 2026 MoreCraze. All rights reserved.</p></div>`;
}

/* ── Scroll Reveal ── */
function initScrollReveal() {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); obs.unobserve(e.target); } });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
}

/* ── Init ── */
async function initApp(activePage) {
  await checkAuth();
  renderNavbar(activePage);
  renderFooter();
  await updateCartBadge();
  initScrollReveal();
}

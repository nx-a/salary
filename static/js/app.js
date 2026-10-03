// Точка входа SPA: hash-роутер, загрузка форм (HTML + JS-модуль) через fetch.
import { api, session } from './api.js';
import { el, ROLE_LABELS } from './ui.js';

// Маршрут → форма. Каждой форме соответствуют forms/<form>.html и js/forms/<form>.js.
const ROUTES = {
  '/login':            { form: 'login',            access: 'guest', title: 'Вход' },
  '/register':         { form: 'register',         access: 'guest', title: 'Регистрация' },
  '/profile':          { form: 'profile',          access: 'auth',  title: 'Моя зарплата', nav: true },
  '/sick-leaves':      { form: 'sick-leaves',      access: 'auth',  title: 'Мои больничные', nav: true },
  '/admin/employees':  { form: 'admin-employees',  access: 'admin', title: 'Сотрудники', nav: true },
  '/admin/employee':   { form: 'admin-employee',   access: 'admin', title: 'Карточка сотрудника' },
  '/admin/sick-leaves':{ form: 'admin-sick-leaves',access: 'admin', title: 'Больничные', nav: true },
};

const view = document.getElementById('view');
const htmlCache = new Map();

function defaultRoute() {
  if (!session.token) return '/login';
  return session.isAdmin ? '/admin/employees' : '/profile';
}

function allowed(route) {
  if (route.access === 'guest') return !session.token;
  if (route.access === 'auth') return !!session.token;
  return session.isAdmin;
}

function parseHash() {
  const [path, query = ''] = location.hash.replace(/^#/, '').split('?');
  return { path: path || '/', params: new URLSearchParams(query) };
}

async function loadHtml(form) {
  if (!htmlCache.has(form)) {
    const response = await fetch(`/forms/${form}.html`);
    if (!response.ok) throw new Error(`Не удалось загрузить форму ${form}`);
    htmlCache.set(form, await response.text());
  }
  return htmlCache.get(form);
}

function renderChrome(currentPath) {
  const nav = document.getElementById('nav');
  nav.replaceChildren(
    ...Object.entries(ROUTES)
      .filter(([, r]) => r.nav && allowed(r))
      .map(([path, r]) => el('a', { href: `#${path}`, class: path === currentPath ? 'active' : null }, r.title)),
  );

  const box = document.getElementById('user-box');
  const user = session.user;
  box.replaceChildren(
    ...(user
      ? [
          el('span', {}, `${user.full_name} · ${ROLE_LABELS[user.role]}`),
          el('button', { class: 'small', onclick: logout }, 'Выйти'),
        ]
      : []),
  );
}

export function logout() {
  session.clear();
  navigate('/login');
}

export function navigate(path) {
  location.hash = `#${path}`;
}

let renderSeq = 0;
async function render() {
  const seq = ++renderSeq;
  const { path, params } = parseHash();
  const route = ROUTES[path];
  if (!route || !allowed(route)) {
    navigate(defaultRoute());
    return;
  }
  renderChrome(path);
  document.title = `${route.title} — Учёт зарплаты`;
  try {
    const [html, module] = await Promise.all([loadHtml(route.form), import(`./forms/${route.form}.js`)]);
    if (seq !== renderSeq) return; // пользователь уже ушёл на другой маршрут
    view.innerHTML = html; // разметка формы — статический файл приложения
    await module.init(view, params);
  } catch (error) {
    if (seq !== renderSeq) return;
    view.replaceChildren(el('div', { class: 'card' }, el('p', { class: 'error' }, error.message)));
  }
}

async function refreshSession() {
  if (!session.token) return;
  try {
    const user = await api('/auth/me');
    session.save(session.token, user);
  } catch {
    session.clear();
  }
}

window.addEventListener('hashchange', render);
await refreshSession();
render();

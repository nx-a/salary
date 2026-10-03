import { api } from '../api.js';
import { badge, el, fillTable, guard, money, ROLE_LABELS } from '../ui.js';

const STORE_KEY = 'salary.employees.status';

export async function init(root) {
  const filter = root.querySelector('#filter-form').elements.status;
  const tbody = root.querySelector('[data-employees]');
  try { filter.value = localStorage.getItem(STORE_KEY) ?? 'pending'; } catch { /* хранилище недоступно */ }

  const action = (label, cls, path, message) =>
    el('button', {
      class: `small ${cls}`,
      onclick: async () => { if (await guard(() => api(path, { method: 'POST' }), message)) await load(); },
    }, label);

  const row = u => el('tr', {},
    el('td', {}, el('a', { href: `#/admin/employee?id=${u.id}` }, u.full_name)),
    el('td', {}, u.login),
    el('td', {}, el('span', { class: `badge ${u.role}` }, ROLE_LABELS[u.role])),
    el('td', {}, badge(u.status)),
    el('td', { class: 'num' }, money(u.base_salary)),
    el('td', { class: 'actions' },
      u.status !== 'active' && action('Подтвердить', 'ok', `/admin/employees/${u.id}/verify`, 'Сотрудник подтверждён'),
      u.status !== 'rejected' && u.role !== 'admin'
        && action('Отклонить', 'danger', `/admin/employees/${u.id}/reject`, 'Сотрудник отклонён'),
      el('a', { class: 'btn small', href: `#/admin/employee?id=${u.id}` }, 'Открыть'),
    ),
  );

  async function load() {
    const query = filter.value ? `?status=${filter.value}` : '';
    const users = await guard(() => api(`/admin/employees${query}`));
    if (users) fillTable(tbody, users, row, 'Сотрудников нет');
  }

  filter.addEventListener('change', () => {
    try { localStorage.setItem(STORE_KEY, filter.value); } catch { /* хранилище недоступно */ }
    load();
  });
  await load();
}

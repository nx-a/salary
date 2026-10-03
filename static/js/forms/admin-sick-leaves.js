import { api } from '../api.js';
import { badge, dateRu, el, fillTable, guard } from '../ui.js';

export async function init(root) {
  const filter = root.querySelector('#filter-form').elements.status;
  const tbody = root.querySelector('[data-leaves]');

  const action = (label, cls, path, message) => el('button', {
    class: `small ${cls}`,
    onclick: async () => { if (await guard(() => api(path, { method: 'POST' }), message)) await load(); },
  }, label);

  const row = s => el('tr', {},
    el('td', {}, el('a', { href: `#/admin/employee?id=${s.user_id}` }, s.employee_name)),
    el('td', {}, `${dateRu(s.date_from)} — ${dateRu(s.date_to)}`),
    el('td', {}, s.comment),
    el('td', {}, badge(s.status)),
    el('td', { class: 'actions' },
      s.status === 'pending' && action('Подтвердить', 'ok', `/admin/sick-leaves/${s.id}/approve`, 'Больничный подтверждён'),
      s.status === 'pending' && action('Отклонить', 'danger', `/admin/sick-leaves/${s.id}/reject`, 'Больничный отклонён'),
    ),
  );

  async function load() {
    const query = filter.value ? `?status=${filter.value}` : '';
    const leaves = await guard(() => api(`/admin/sick-leaves${query}`));
    if (leaves) fillTable(tbody, leaves, row, 'Больничных нет');
  }

  filter.addEventListener('change', load);
  await load();
}

import { api } from '../api.js';
import { badge, dateRu, el, fillTable, formData, guard } from '../ui.js';

export async function init(root) {
  const form = root.querySelector('#sick-form');
  const tbody = root.querySelector('[data-leaves]');

  const load = async () => {
    const leaves = await guard(() => api('/me/sick-leaves'));
    if (!leaves) return;
    fillTable(tbody, leaves, s => el('tr', {},
      el('td', {}, `${dateRu(s.date_from)} — ${dateRu(s.date_to)}`),
      el('td', {}, s.comment),
      el('td', {}, badge(s.status)),
    ), 'Больничных нет');
  };

  form.elements.date_from.addEventListener('change', () => {
    if (!form.elements.date_to.value) form.elements.date_to.value = form.elements.date_from.value;
    form.elements.date_to.min = form.elements.date_from.value;
  });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    const created = await guard(
      () => api('/me/sick-leaves', { method: 'POST', body: formData(form) }),
      'Больничный отправлен на проверку',
    );
    if (created) {
      form.reset();
      await load();
    }
  });

  await load();
}

import { api } from '../api.js';
import { renderPayslip } from '../payslip.js';
import { badge, el, fillPeriodSelects, fillTable, formData, guard, KIND_LABELS, money, MONTHS, ROLE_LABELS } from '../ui.js';

export async function init(root, params) {
  const id = Number(params.get('id'));
  const base = `/admin/employees/${id}`;
  const salaryForm = root.querySelector('#salary-form');
  const bonusForm = root.querySelector('#bonus-form');
  const periodForm = root.querySelector('#period-form');
  fillPeriodSelects(bonusForm.elements.month, bonusForm.elements.year);
  fillPeriodSelects(periodForm.elements.month, periodForm.elements.year);

  function showEmployee(user) {
    root.querySelector('[data-name]').textContent = user.full_name;
    root.querySelector('[data-login]').textContent = `${user.login}, ${ROLE_LABELS[user.role]}`;
    root.querySelector('[data-status]').replaceChildren(badge(user.status));
    salaryForm.elements.base_salary.value = user.base_salary;

    const verifyActions = root.querySelector('[data-verify-actions]');
    const button = (label, cls, action, message) => el('button', {
      class: cls,
      onclick: async () => {
        const updated = await guard(() => api(`${base}/${action}`, { method: 'POST' }), message);
        if (updated) showEmployee(updated);
      },
    }, label);
    verifyActions.replaceChildren(
      ...[
        user.status !== 'active' && button('Подтвердить учётную запись', 'ok', 'verify', 'Сотрудник подтверждён'),
        user.status !== 'rejected' && user.role !== 'admin'
          && button('Отклонить', 'danger', 'reject', 'Сотрудник отклонён'),
      ].filter(Boolean),
    );
  }

  async function loadBonuses() {
    const bonuses = await guard(() => api(`${base}/bonuses`));
    if (!bonuses) return;
    fillTable(root.querySelector('[data-bonuses]'), bonuses, b => el('tr', {},
      el('td', {}, `${MONTHS[b.month - 1]} ${b.year}`),
      el('td', {}, KIND_LABELS[b.kind]),
      el('td', { class: 'num' }, money(b.amount)),
      el('td', {}, b.comment),
      el('td', {}, el('button', {
        class: 'small danger',
        onclick: async () => {
          if (!confirm('Удалить начисление?')) return;
          await guard(() => api(`/admin/bonuses/${b.id}`, { method: 'DELETE' }), 'Удалено');
          await Promise.all([loadBonuses(), loadPayslip()]);
        },
      }, 'Удалить')),
    ), 'Начислений нет');
  }

  async function loadPayslip() {
    const { year, month } = formData(periodForm);
    const slip = await guard(() => api(`${base}/payslip?year=${year}&month=${month}`));
    if (slip) renderPayslip(root.querySelector('[data-payslip]'), slip);
  }

  salaryForm.addEventListener('submit', async event => {
    event.preventDefault();
    const user = await guard(() => api(`${base}/salary`, { method: 'PUT', body: formData(salaryForm) }), 'Оклад сохранён');
    if (user) {
      showEmployee(user);
      await loadPayslip();
    }
  });

  bonusForm.addEventListener('submit', async event => {
    event.preventDefault();
    const body = formData(bonusForm);
    body.year = Number(body.year);
    body.month = Number(body.month);
    if (await guard(() => api(`${base}/bonuses`, { method: 'POST', body }), 'Начисление добавлено')) {
      bonusForm.elements.amount.value = '';
      bonusForm.elements.comment.value = '';
      await Promise.all([loadBonuses(), loadPayslip()]);
    }
  });

  periodForm.addEventListener('submit', event => { event.preventDefault(); loadPayslip(); });

  const user = await guard(() => api(base));
  if (!user) return;
  showEmployee(user);
  await Promise.all([loadBonuses(), loadPayslip()]);
}

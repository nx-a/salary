import { api, session } from '../api.js';
import { renderPayslip } from '../payslip.js';
import { el, fillPeriodSelects, fillTable, formData, guard, KIND_LABELS, money, MONTHS } from '../ui.js';

export async function init(root) {
  const user = session.user;
  root.querySelector('[data-name]').textContent = user.full_name;
  root.querySelector('[data-salary]').textContent = money(user.base_salary);

  const periodForm = root.querySelector('#period-form');
  fillPeriodSelects(periodForm.elements.month, periodForm.elements.year);

  const loadPayslip = async () => {
    const { year, month } = formData(periodForm);
    const slip = await guard(() => api(`/me/payslip?year=${year}&month=${month}`));
    if (slip) renderPayslip(root.querySelector('[data-payslip]'), slip);
  };
  periodForm.addEventListener('submit', event => { event.preventDefault(); loadPayslip(); });

  const bonuses = await guard(() => api('/me/bonuses'));
  if (bonuses) {
    fillTable(root.querySelector('[data-bonuses]'), bonuses, b => el('tr', {},
      el('td', {}, `${MONTHS[b.month - 1]} ${b.year}`),
      el('td', {}, KIND_LABELS[b.kind]),
      el('td', { class: 'num' }, money(b.amount)),
      el('td', {}, b.comment),
    ), 'Премий и надбавок пока нет');
  }
  await loadPayslip();
}

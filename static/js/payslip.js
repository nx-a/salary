// Отрисовка расчётного листка (используется в нескольких формах).
import { el, money } from './ui.js';

function stat(label, value, extraClass = '') {
  return el('div', { class: `stat ${extraClass}` },
    el('div', { class: 'label' }, label),
    el('div', { class: 'value' }, value));
}

export function renderPayslip(container, slip) {
  container.replaceChildren(
    stat('Оклад', money(slip.base_salary)),
    stat('Рабочих дней', slip.working_days),
    stat('Дневная ставка', money(slip.daily_rate)),
    stat('Отработано', `${money(slip.worked_pay)} (${slip.working_days - slip.sick_days} дн.)`),
    stat('Больничные (50 %)', `${money(slip.sick_pay)} (${slip.sick_days} дн.)`),
    stat('Премии', money(slip.bonuses_total)),
    stat('Надбавки', money(slip.allowances_total)),
    stat('Итого к начислению', money(slip.total), 'total'),
  );
}

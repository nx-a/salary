// Общие помощники интерфейса. Пользовательские строки выводятся только через textContent.

export const MONTHS = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

export const STATUS_LABELS = {
  pending: 'на проверке', active: 'подтверждён', rejected: 'отклонён', approved: 'подтверждён',
};
export const ROLE_LABELS = { admin: 'администратор', user: 'сотрудник' };
export const KIND_LABELS = { bonus: 'Премия', allowance: 'Надбавка' };

const moneyFormat = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' });
export const money = value => moneyFormat.format(Number(value));
export const dateRu = iso => new Date(`${iso}T00:00:00`).toLocaleDateString('ru-RU');

/** Создаёт элемент: el('td', {class: 'num'}, 'текст', childNode). */
export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null || value === false) continue;
    if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else if (key === 'class') node.className = value;
    else node.setAttribute(key, value === true ? '' : value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

export const badge = status => el('span', { class: `badge ${status}` }, STATUS_LABELS[status] ?? status);

/** Заполняет tbody строками или сообщением о пустом списке. */
export function fillTable(tbody, items, renderRow, emptyText = 'Нет данных') {
  const cols = tbody.closest('table').querySelectorAll('thead th').length;
  tbody.replaceChildren(
    ...(items.length ? items.map(renderRow) : [el('tr', {}, el('td', { colspan: cols, class: 'empty' }, emptyText))]),
  );
}

let toastTimer;
export function toast(message, isError = false) {
  const node = document.getElementById('toast');
  node.textContent = message;
  node.classList.toggle('error', isError);
  node.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.hidden = true; }, 3500);
}

/** Выполняет действие, показывая ошибку во всплывающем сообщении. */
export async function guard(action, successMessage) {
  try {
    const result = await action();
    if (successMessage) toast(successMessage);
    return result;
  } catch (error) {
    toast(error.message, true);
    return undefined;
  }
}

export function fillPeriodSelects(monthSelect, yearInput, date = new Date()) {
  monthSelect.replaceChildren(...MONTHS.map((name, i) => el('option', { value: i + 1 }, name)));
  monthSelect.value = String(date.getMonth() + 1);
  yearInput.value = String(date.getFullYear());
}

export const formData = form => Object.fromEntries(new FormData(form));

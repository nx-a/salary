# Учёт заработной платы

Сервис учёта зарплаты сотрудников: оклад + премии/надбавки, больничные (оплата 50 %), регистрация с подтверждением администратором, JWT-авторизация с ролями `admin` и `user`.

Стек: Python 3.14, FastAPI, SQLAlchemy 2, PostgreSQL, PyJWT, bcrypt, UI на чистом JavaScript (SPA).

## Быстрый старт

```bash
make setup   # uv sync, .env, создание БД, таблиц и администратора
make run     # http://localhost:8091  (Swagger: /docs)
```

Настройки — в `.env` (шаблон `.env.example`). Нужен запущенный PostgreSQL; при необходимости поднимите отдельный: `make docker-up` (порт 5433, поменяйте `DATABASE_URL`).

Администратор по умолчанию создаётся из `ADMIN_LOGIN` / `ADMIN_PASSWORD` (при старте и `make create-admin`).

`make help` — список всех команд.

## Архитектура (гексагональная)

```
src/salary/
├── domain/                 # ядро: сущности, правила, расчёт ЗП — без зависимостей от фреймворков
│   ├── models.py           # User, Bonus, SickLeave, роли и статусы
│   ├── payroll.py          # PayrollCalculator — чистый расчёт начислений
│   └── errors.py
├── application/
│   ├── ports/              # интерфейсы (ABC): репозитории, UnitOfWork, PasswordHasher, TokenService
│   └── services/           # use cases: AuthService, EmployeeService, SickLeaveService, PayrollService
├── adapters/
│   ├── inbound/http/       # FastAPI: роутеры, DTO, зависимости авторизации
│   └── outbound/
│       ├── persistence/    # SQLAlchemy ORM + репозитории + UnitOfWork (PostgreSQL)
│       └── security/       # bcrypt, JWT (HS256)
├── container.py            # composition root — связывает порты с адаптерами
├── config.py, main.py, cli.py
static/                     # SPA: index.html, js/app.js (роутер), forms/*.html + js/forms/*.js
tests/                      # домен, use cases и API на in-memory адаптерах
```

## Правила расчёта

* Дневная ставка = оклад / рабочие дни месяца (пн–пт).
* Рабочие дни на **подтверждённом** больничном оплачиваются по 50 % дневной ставки.
* Больничный, захватывающий несколько месяцев, учитывается в каждом месяце только своей частью.
* Итог = оплата отработанных дней + оплата больничных + премии + надбавки за месяц; округление до копеек (half-up).

## Роли

| Сотрудник (`user`) | Администратор (`admin`) |
|---|---|
| регистрация (вход после подтверждения) | подтверждение / отклонение сотрудников |
| просмотр своего оклада, премий, расчёта | установка оклада |
| заведение больничного (ждёт подтверждения) | начисление и удаление премий и надбавок |
| | подтверждение / отклонение больничных, расчёт по любому сотруднику |

## REST API (`/api`)

| Метод | Путь | Доступ |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | все |
| GET | `/auth/me` | авторизованные |
| GET | `/me/bonuses`, `/me/sick-leaves`, `/me/payslip?year=&month=` | авторизованные |
| POST | `/me/sick-leaves` | авторизованные |
| GET | `/admin/employees[?status=]`, `/admin/employees/{id}` | admin |
| POST | `/admin/employees/{id}/verify`, `/admin/employees/{id}/reject` | admin |
| PUT | `/admin/employees/{id}/salary` | admin |
| GET/POST | `/admin/employees/{id}/bonuses` | admin |
| DELETE | `/admin/bonuses/{id}` | admin |
| GET | `/admin/employees/{id}/payslip?year=&month=` | admin |
| GET | `/admin/sick-leaves[?status=]` | admin |
| POST | `/admin/sick-leaves/{id}/approve`, `/admin/sick-leaves/{id}/reject` | admin |

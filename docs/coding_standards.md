# Smart HRMS — Coding Standards & Conventions

## Python

- Follow **PEP 8** strictly. Use `black` (line length 100) + `isort` for auto-formatting.
- Use **type hints** on all function signatures (`str | None`, not `Optional[str]` for Python 3.10+).
- Every module, class, and public function must have a **docstring** (Google style).
- Maximum function length: **40 lines**. Split into helpers if exceeded.
- No bare `except:` — always catch a specific exception type.
- Never use `print()` in application code — use `logging.getLogger(__name__)`.

## Architecture Rules

| Layer | Can import from | Cannot import from |
|---|---|---|
| `routes.py` | services, forms, constants, utils | repositories, db, models directly |
| `services/` | repositories, utils, helpers, constants, extensions | blueprints, routes |
| `repositories/` | models, extensions.database | services, blueprints |
| `models/` | extensions.database, constants | services, repositories |
| `utils/` | stdlib only (no Flask context) | anything in app/ |

## Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Python files | `snake_case.py` | `employee_service.py` |
| Classes | `PascalCase` | `EmployeeService` |
| Functions/methods | `snake_case` | `get_by_department()` |
| Constants | `UPPER_SNAKE` | `MAX_FAILED_ATTEMPTS` |
| URL endpoints | `kebab-case` | `/employees/create-profile` |
| Template files | `snake_case.html` | `employee_detail.html` |
| CSS classes | `hrms-kebab-case` | `.hrms-stat-card` |
| JS variables | `camelCase` | `employeeList` |
| JS classes/namespaces | `PascalCase` | `EmployeesPage` |
| Database tables | `snake_case` plural | `employees`, `leave_requests` |
| Database columns | `snake_case` | `first_name`, `created_at` |

## Templates

- All templates **must extend** `layouts/base.html` or `layouts/auth_base.html`.
- No inline CSS (`style="..."`) — use CSS classes only.
- No inline JavaScript (`onclick="..."`) — use `data-*` attributes + JS files.
- Escape all user-supplied content: `{{ value | e }}` or use Jinja2 autoescaping.
- Use `{% include %}` for reusable components (sidebar, navbar, flash, pagination).

## CSS

- All class names prefixed with `.hrms-` to avoid Bootstrap conflicts.
- Define colors/sizes as CSS custom properties in `variables.css` — never hardcode hex values in component files.
- Mobile-first: base styles for mobile, media queries for larger screens.

## JavaScript

- Vanilla ES6+ only — no jQuery, no frameworks.
- Namespace everything under `window.HRMS.*` to avoid global pollution.
- Always escape user-generated content with `HRMS.Utils.escapeHtml()` before injecting into `innerHTML`.
- Use `HRMS.CSRF.headers()` on every `fetch()` call.
- Defer all non-critical scripts with the `defer` attribute.

## Git Workflow

- Branch naming: `feature/short-description`, `fix/issue-description`, `hotfix/critical-fix`
- Commit message format: `type(scope): short description` — e.g. `feat(employees): add profile photo upload`
- Never commit directly to `main` — always use a pull request.
- Never commit `.env`, `*.db`, `logs/*.log`, or `instance/` contents.
- Run `flake8`, `black --check`, and `pytest` before every commit.

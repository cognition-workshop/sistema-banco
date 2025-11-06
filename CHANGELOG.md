# Version: 2.0.0

## Session 5: Production & Quality (November 2024)

### Added
- Client-side and server-side form validation for all forms
- Custom validators for CPF, account numbers, and amounts (accounts/validators.py, transactions/validators.py)
- Custom error pages (404, 500, 403) with Brazilian Portuguese messages
- Health check endpoints (/health/, /readiness/) for monitoring
- Production settings file (settings_prod.py) with django-environ
- Environment variable management (.env.example)
- Custom exceptions for banking operations (core/exceptions.py)
- Error handling decorator for views (core/decorators.py)
- Comprehensive test suite with >80% coverage:
  - User model and authentication tests
  - Bank account and transaction tests
  - Form validation tests
  - Health check tests
  - Integration tests
- Migration management scripts (scripts/migrate.sh)
- Safe migration management command (python manage.py safe_migrate)
- API documentation (docs/API.md)
- Deployment documentation (docs/DEPLOYMENT.md)
- Security settings (SECURE_*, HSTS, SSL cookies)
- Logging configuration for production and development
- Django Crispy Forms integration with Tailwind CSS

### Fixed
- **Critical Bug:** Withdrawals can no longer create negative balances
- Form validation now properly checks account balance before withdrawal
- Error messages updated to Brazilian Portuguese

### Changed
- Updated all error messages to PT-BR
- Enhanced security with production-ready settings
- Updated README with production setup, testing, and deployment instructions
- Improved form validation with both client and server-side checks

### Dependencies Added
- django-crispy-forms==2.1
- crispy-tailwind==0.5.0
- django-environ==0.11.2
- coverage==7.3.2
- flake8==6.1.0
- black==23.12.0

### Notes
- This release focuses on production readiness of existing banking features
- PIX, IRPF, and admin_panel features mentioned in Sessions 1-4 were not found in codebase
- Test coverage achieved: >80% for all existing functionality
- All verification steps passed: tests, lint, health checks, error pages

---

# Version: 2.0.2

* [#46](https://github.com/saadmk11/banking-system/pull/46): Bump django from 3.1.8 to 3.1.9
* [#22](https://github.com/saadmk11/banking-system/pull/22): Bump django from 3.1.1 to 3.1.2
* [#26](https://github.com/saadmk11/banking-system/pull/26): Bump django from 3.1.2 to 3.1.3
* [#28](https://github.com/saadmk11/banking-system/pull/28): Bump django from 3.1.3 to 3.1.4
* [#24](https://github.com/saadmk11/banking-system/pull/24): Bump django-celery-beat from 2.0.0 to 2.1.0
* [#31](https://github.com/saadmk11/banking-system/pull/31): Bump django from 3.1.4 to 3.1.5
* [#34](https://github.com/saadmk11/banking-system/pull/34): Bump django from 3.1.5 to 3.1.7
* [#37](https://github.com/saadmk11/banking-system/pull/37): Bump django from 3.1.7 to 3.1.8
* [#40](https://github.com/saadmk11/banking-system/pull/40): Update GitHub Action Versions
* [#38](https://github.com/saadmk11/banking-system/pull/38): Add GitHub Actions Version Updater
* [#42](https://github.com/saadmk11/banking-system/pull/42): Update GitHub Action Versions
* [#39](https://github.com/saadmk11/banking-system/pull/39): Update GitHub Action Versions
* [#55](https://github.com/saadmk11/banking-system/pull/55): fixed page not found after login by registered user
* [#54](https://github.com/saadmk11/banking-system/pull/54): Bump django from 3.1.9 to 3.2.7
* [#52](https://github.com/saadmk11/banking-system/pull/52): Bump python-dateutil from 2.8.1 to 2.8.2


Version: 2.0.1
==============

* [#17](https://github.com/saadmk11/banking-system/pull/17): Create LICENSE
* [#16](https://github.com/saadmk11/banking-system/pull/16): Bump django from 3.1 to 3.1.1
* [#18](https://github.com/saadmk11/banking-system/pull/18): Add Changelog-ci

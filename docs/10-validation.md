# 10. Локальная проверка проекта — 20.11.2026

В отдельном checkout от base `e862c47900559767da195adf745528def38c48b5`:

- `python3 scripts/validate.py`: успешно, JSON/TOML/INI, адресный план, additive rules shape, Python AST, относительные ссылки, placeholders ключевых полей.
- `python3 -m unittest discover -s tests -v`: 7 тестов успешно. Проверены закрытые permissions и отказ overwrite/in-checkout, отсутствие сетевых/process API в scripts, отказ опасным rules, ограничения фильтрации, разделение server/client и shell syntax systemd-фрагментов (после `$$` unescape systemd).
- Все 21 уникальная внешняя HTTPS-ссылка в Markdown на момент проверки отвечали HTTP 200; ссылки на файлы внутри проекта разрешаются. Доступность ссылки не подтверждает authenticity бинарника и не заменяет проверку SHA/commit.
- `git diff --check`: без ошибок. Новые файлы и полный staged diff дополнительно проверены на адреса/домены исходного развертывания, ключи и присущие ему индивидуальные значения; реальные конфиги не добавлены.
- Pinned upstream AWG Go/tools/Realm получены из официальных GitHub repositories, теги сверены с commit; поля tools 3.1 и IPC paths просмотрены. Сборка нового набора бинарников и kernel применение rules в этой задаче не выполнялись.

Среда: непривилегированный по отношению к сети хоста контейнер с Python 3.12. В нем отсутствуют полный systemd/netfilter tooling и сборочный C/Go toolchain. Проверка systemd unit parser и iptables-restore kernel parser не имитировалась: выполнить на отдельном целевом стенде перед установкой. Сам `sh -n` не проверяет семантику systemd.

Работающие VPS использовались только read-only. Сервисные файлы, маршруты, firewall, peers и версии на них не изменялись; тестовых VPN peers в этой задаче не создавалось. Старый AWG 2.0 не удалялся. Никаких сетевых/нагрузочных тестов production не проводилось.

Обязательный следующий gate: чистые два VPS плюс внешний тестовый клиент, проверка всех вручную заполненных конфигов официальными tools, systemd/firewall parser, положительные и отрицательные E2E, Windows/iOS import, DNS/IPv6/WebRTC при подключении и аварийном разрыве, MTU/PMTU, автозапуск и отдельно согласованный reboot. Пока этот gate не пройден, шаблоны не считаются проверенным one-click deployment.

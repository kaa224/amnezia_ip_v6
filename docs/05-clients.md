# 5. Ключи, профили Windows и iOS

Используйте официальный `awg` из закрепленного tools. На доверенной машине с отключенным shell tracing создайте закрытый каталог **вне Git**. Не печатайте ключи, QR или полный конфиг:

```sh
umask 077
mkdir -m 700 /absolute/private/device-direct31
/opt/awg31/bin/awg genkey > /absolute/private/device-direct31/private.key
/opt/awg31/bin/awg pubkey < /absolute/private/device-direct31/private.key > /absolute/private/device-direct31/public.key
/opt/awg31/bin/awg genpsk > /absolute/private/device-direct31/peer.psk
```

Аналогично создайте отдельные серверные ключи Direct/Relay и четыре независимые пары Windows-Direct31, Windows-Relay31, iPhone-Direct31, iPhone-Relay31. PSK уникален для peer и совпадает только у соответствующих двух концов. Для HeaderProtectionKey используйте отдельный 32-byte ключ на экземпляр, генерируемый официальным `awg genpsk` в закрытый файл; это **не** peer PSK. Ключи не передаются в аргументах, env, stdout/monitor или Git. Не храните секреты в shell history.

`examples/client.conf.example` — шаблон для одной пары устройство/путь. PrivateKey клиента, PublicKey сервера и PSK заполняются закрытым редактором из файлов. На сервер добавляется только public key, PSK и точные `/32`,`/128` этого клиента. Не копировать клиентский private key в server config. Для Relay Endpoint = RELAY4:52012, для Direct = EXIT4:52010. На iOS назначьте следующий уникальный адрес из плана.

Блок `examples/protocol.conf.example` содержит **имена** полей 3.1 и непригодные для запуска `REPLACE_*`; реальных индивидуальных значений здесь нет. Параметры должны быть валидированы по закрепленному upstream и совпадать у сервера/его клиентов. [Официальная спецификация полей](https://docs.amnezia.org/documentation/amnezia-wg/) и `src/config.c` tools описывают типы. Не подбирайте параметры по массовым конфигам. Здесь не приводятся приемы маскировки и не обещается недетектируемость. Проверяйте ограничения совместимости, cookie protection и overhead; при HeaderProtectionKey соответствующие префиксы должны удовлетворять требованиям upstream. Не выключайте cookies без отдельного анализа.

DNS — выбранные официальные [Cloudflare resolver addresses](https://developers.cloudflare.com/1.1.1.1/ip-addresses/), внесенные в DNS_PRIMARY / DNS_SECONDARY. Full tunnel: `AllowedIPs = 0.0.0.0/0, ::/0`, адреса обеих семей назначены профилю. Сервер блокирует внутренний IPv6, но это **не доказательство клиентского kill switch**: он зависит от приложения и ОС, поведения при disconnect и исключений split tunneling. Не заявляйте отсутствие утечек до испытаний.

Перед импортом заполненные файлы — 0600; хранить вне Git. Передайте на Windows через существующий SSH alias своего VPS (с проверкой host key):

```sh
scp exit-vps:/root/vpn-profiles/Windows-Direct31.conf .
scp exit-vps:/root/vpn-profiles/Windows-Relay31.conf .
```

Для iPhone скачайте **отдельные** iPhone-Direct31.conf / iPhone-Relay31.conf и передайте доверенным способом в Files, избегая публичных ссылок и автоматической синхронизации секретов. В официальном AmneziaVPN выберите добавление/импорт конфигурационного файла, создайте два отдельных подключения, проверьте их имена и endpoints. Названия элементов GUI зависят от версии. Не запускайте функцию автоматической установки протокола на native сервере. Не преобразовывайте файл сторонними онлайн-конвертерами. Если официальный клиент отклоняет 3.1 поле, остановитесь и проверьте его версию; удаление поля ради импорта не подтверждает 3.1.

Для отзыва peer удалите его из закрытого серверного конфига и примените официальный `awg syncconf` с проверенным setconf-форматом без печати конфигурации (не `showconf` в терминал). Отзыв тестового peer должен быть live и persistent. Обычный `awg show` может раскрывать индивидуальные параметры: используйте только адресные команды/санитизированные счетчики в закрытой среде. Повторно выдайте новый профиль при утрате устройства, отзовите старый public key. Бэкап секретов — только шифрованный и вне репозитория.

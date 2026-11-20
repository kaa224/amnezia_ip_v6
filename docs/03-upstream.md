# 3. Официальные версии и проверка целостности

Срез исходников проверен 20.11.2026. Pin означает воспроизводимый исходный код; двоичная воспроизводимость требует фиксации toolchain, архитектуры и всех флагов. Не запускайте скачанные install scripts. Проверки SHA локального файла недостаточно для установления происхождения: нужен доверенный upstream, независимый digest/signature при наличии и проверка commit. Если релиз недоступен или не совпал — остановиться, а не подменять 3.1 на 2.0.

| Проект | Tag | Commit |
|---|---|---|
| AWG Go | v3.1.20261116 | 08fe3d33bbb116be09a6183d02609311b8b0c9e8 |
| AWG tools | v3.1.20260812 | ee0f0a9aa34ff0a0da4b3433b9512781cfe02843 |
| Realm | v2.9.6 | 7e9f44c4b6414079fdd7ed27eea155066df80dd9 |

Ссылки на теги — в README. В AWG Go подтверждены module `/v3` и поля UAPI 3.1, в tools — `HeaderProtectionKey`, `ContentPaddingAddition`, тайминги и флаги. Баннер версии AWG исторический и не является доказательством версии протокола. Не менять криптографическое ядро.

## Сборка на отдельной машине

Для AWG официальный `go.mod` требует Go >=1.25. Установите подходящий фиксированный Go из [официальных downloads](https://go.dev/dl/) с проверкой их SHA256. Не полагайтесь на автоматическое скачивание нового toolchain. Пример команд **вне VPS production**:

```sh
git clone --branch v3.1.20261116 --depth 1 https://github.com/amnezia-vpn/amneziawg-go.git awg-src
cd awg-src
test "$(git rev-parse HEAD)" = 08fe3d33bbb116be09a6183d02609311b8b0c9e8
export GOTOOLCHAIN=local
go mod download
go mod verify
GOTOOLCHAIN=local CGO_ENABLED=0 go build -trimpath -ldflags '-X github.com/amnezia-vpn/amneziawg-go/v3/ipc.socketDirectory=/run/personal-awg31/amneziawg' -o ../amneziawg-go .
cd ..
git clone --branch v3.1.20260812 --depth 1 https://github.com/amnezia-vpn/amneziawg-tools.git tools-src
test "$(git -C tools-src rev-parse HEAD)" = ee0f0a9aa34ff0a0da4b3433b9512781cfe02843
make -C tools-src/src RUNSTATEDIR=/run/personal-awg31
sha256sum amneziawg-go tools-src/src/awg > SHA256SUMS.local
```

Не запускать `make install` на общем сервере. Переносите только выбранные бинарники в собственный `/opt/awg31/bin/`, проверив их manifest, архитектуру и ABI. `awg` здесь собран с отдельным RUNSTATEDIR; он должен находить тот же IPC каталог, что Go. `awg-quick` не используется для управления хостом: он может добавлять full-tunnel маршруты и hooks.

Realm можно собрать из тега `cargo build --release --locked` после проверки `git rev-parse HEAD`, фиксируя Rust из upstream `rust-toolchain.toml`, Cargo.lock, target и features. Либо скачать соответствующий архитектуре asset из [официального релиза](https://github.com/zhboner/realm/releases/tag/v2.9.6). В предыдущем развертывании x86_64 musl archive имел SHA256 `b1cc335547bea8bb2a88178bef12ec7f2363e36200e7ea1d4e1e67627929bf65`, извлеченный binary — `6a1733bfc51e3d19743757ca08f4c81f36afe7972eab0607bef264fc99064208`. Это исторические измерения, **не подпись издателя** и не checksum произвольного asset/собственной сборки. Перепроверьте имя asset и digest перед использованием. Бинарники и toolchain в этот репозиторий не включены.

Клиентский формат ранее сверялся с [AmneziaVPN 5.1.1.10](https://github.com/amnezia-vpn/amnezia-client/releases/tag/5.1.1.10), commit `c71e65d9cd04cbfcd58de4f3df22d63808996c63`. Установите официальный поддерживаемый Windows/iOS клиент с явной поддержкой 3.1; совпадение версии пакета и совместимость формата проверить на устройстве. См. [официальную инструкцию self-hosted](https://docs.amnezia.org/documentation/instructions/new-amneziawg-selfhosted/). Ее автоматическая установка управляет своим контейнером; не применяйте ее поверх этих независимых native экземпляров.

Сохраните вне Git manifest: URL, tag, commit, дата, toolchain, target, команды сборки, SHA256 артефактов, результат проверки подписи (или ее отсутствие). Проект не утверждает, что сборка из этого руководства уже прошла полный чистый стенд.

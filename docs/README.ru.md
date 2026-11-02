# TorrServer Bunny — инструкция на русском

Это независимая интеграция с Bunny Magic Containers для оригинального [TorrServer от YouROK](https://github.com/YouROK/TorrServer). Спасибо авторам TorrServer за их работу.

## Установка на macOS/Linux

```bash
curl -fsSL https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh -o install-bunny.sh
sh ./install-bunny.sh
```

Потребуются Python 3, curl, Bunny API key и доступ к Magic Containers. Установщик предлагает выбрать регион, вводит логин и автоматически создаёт пароль. До подтверждения `CREATE` платные ресурсы не создаются.

После установки:

```bash
~/.local/bin/torrserver-bunny start
~/.local/bin/torrserver-bunny status
~/.local/bin/torrserver-bunny stop
```

В Lampa укажи HTTPS URL (из вывода `status` или панели Bunny), логин и пароль. Если адрес из API не был получен, сохрани настоящий URL из панели командой `torrserver-bunny set-url https://...`.

Для автоматического выключения спустя час без передачи видео включи GitHub Actions watchdog в **собственном** репозитории/форке (и только после проверки его workflow и публичности образа GHCR):

```bash
~/.local/bin/torrserver-bunny enable-github-watchdog --repo ТВОЙ-АККАУН/ТВОЙ-ФОРК
```

Этот механизм опрашивает статус раз в 10 минут и отправляет `undeploy` только после 60 минут без передачи видео. GitHub Actions может запускаться с задержкой; гарантии точного выключения нет. Вручную `stop` работает без Actions.

**Важно:** образ `ghcr.io/vbrekher/torrserver-bunny:main` ещё должен быть опубликован и открыт для скачивания. Без Bunny API key невозможно провести реальную проверку создания приложения и воспроизведения на Samsung Tizen. Примерные расходы на фильм 50 ГБ в Европе: $0.50 трафика + до $0.075 вычислений и RAM за три часа при условии 1 vCPU / 1 ГБ, плюс торрент-upload, 1 ГБ хранилища около $0.10/месяц и по желанию Anycast. Права на воспроизводимый контент пользователь обеспечивает самостоятельно.

### Если GitHub Actions недоступен

В распакованном архиве есть `bash build-local-image.sh`: локально собирает Linux/amd64 Docker-образ и публикует в GHCR. Требуется Docker, `gh auth login`, доступ `write:packages`, после публикации убедись, что пакет имеет публичную видимость (PUBLIC).

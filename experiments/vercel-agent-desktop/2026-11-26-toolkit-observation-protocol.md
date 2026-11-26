# Agent Desktop — чтение элементов Qt и Electron

Стенд использует исходники Vercel Agent Desktop на `b43ac4f6e892ef608f8851428613c4009f0e84c7`, Xvfb и отдельную шину D-Bus внутри одноразового контейнера. Тестовые окна написаны специально для прогона. Они показывают синтетический текст `SELECT 1` и кнопку. Подключений к БД нет.

Соберите образ в Linux с Docker и поддержкой BuildKit. Передайте Docker только архив закреплённого исходника.

```bash
fixture="$PWD/experiments/vercel-agent-desktop"
source=/absolute/path/to/agent-desktop-checkout
context=$(mktemp -d)
git -C "$source" archive b43ac4f6e892ef608f8851428613c4009f0e84c7 | tar -xf - -C "$context"
docker build -f "$fixture/Dockerfile" -t research-ad-toolkit:b43ac4f "$context"
```

Для Electron распакуйте оригинальный архив `electron-v44.7.0-linux-x64.zip`. Проверьте SHA-256 `3ae7d5bdad61c664486c6ab61361dd084d064c8c08af8d13a687096e18ce555a` по опубликованному `SHASUMS256.txt`. Сохраните право исполнения у `electron` и `chrome_crashpad_handler`. Загрузка публичных пакетов выполняется при подготовке. Сборка Rust после загрузки зависимостей и все прогоны отключают сеть. [Релиз Electron](https://github.com/electron/electron/releases/tag/v44.7.0)

```bash
bash "$fixture/run-observation.sh" research-ad-toolkit:b43ac4f qt
bash "$fixture/run-observation.sh" research-ad-toolkit:b43ac4f electron /absolute/path/to/electron
```

Скрипт наблюдения запускает по одному окну. Из списка приложений выбирает только PID созданного процесса и проверяет, что имя однозначно. Из снимка берёт имя, роль и наличие ссылки. Ожидаются ровно по одному `textfield` с именем `Fixture Query` и `button` с именем `Fixture Run`. Поле `Fixture Absent` должно отсутствовать. На каждый инструмент приходится три свежих контейнера. Монтируются только файлы стенда и, для Electron, файлы проверенной поставки. Дисплей, шина сообщений и домашний каталог хоста в контейнер не передаются.

Для собственного окна Electron явно включает доступность Chromium. Внешняя песочница Chromium отключена для этого окна внутри ограниченного контейнера. Результат применим к этой конфигурации; стенд не вызывает действий с элементами и не проверяет доставку ввода. [Скрипт наблюдения](observe-toolkit.py) · [Qt](qt-fixture.py) · [Electron](electron-fixture.cjs)

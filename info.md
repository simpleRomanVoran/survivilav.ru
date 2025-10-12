Проект survivilav.ru

image - изображения
styles - стили
scripts - скрипты

LICENSE - MIT
info.md файлы объясняют иерархию проекта и дают общую информацию.

Используемый стек FRONTEND'а проекта:
* html
* css
* js
* LiveServer (для запуска кода)
* Markdown (сводки и записи)
* Git
* RESET CSS

CURL
Создать инвайт (через header):
curl -X POST "http://127.0.0.1:8000/api/invite/create" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ТВОЙ_КЛЮЧ" \
  -d '{"ttl_seconds":86400,"author":"admin","max_uses":3}'

Получить список:
curl -H "X-API-Key: ТВОЙ_КЛЮЧ" "http://127.0.0.1:8000/api/invite/list"

Проверка приглашения (публично):
curl "http://127.0.0.1:8000/api/invite/validate?code=ТВОЙ КЛЮЧ"

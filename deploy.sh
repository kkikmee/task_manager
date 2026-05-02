#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'
log()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

DOMAIN="kkikmee.com.ru"
EMAIL=""

CMD=${1:-help}

compose() { docker compose "$@"; }

case "$CMD" in

  # ─── Первый запуск ────────────────────────────────────────
  init)
    log "=== Первый запуск TaskManager ==="

    # Проверяем .env
    [ -f ".env" ] || fail ".env не найден! Заполни его сначала."
    grep -q "замени" .env && fail "Заполни .env — там ещё заглушки!"

    # Шаг 1: временный nginx без SSL
    log "Шаг 1/4: Запуск с временным nginx (HTTP)..."
    cp nginx-temp.conf nginx.conf
    compose up -d --build
    sleep 5
    ok "Контейнеры запущены"

    # Шаг 2: получаем сертификат
    log "Шаг 2/4: Получение SSL сертификата..."
    [ -n "$EMAIL" ] || { echo -n "Введи email для Let's Encrypt: "; read -r EMAIL; }
    compose run --rm certbot certonly \
      --webroot \
      --webroot-path /var/www/certbot \
      --email "$EMAIL" \
      --agree-tos \
      --no-eff-email \
      -d "$DOMAIN" \
      -d "www.$DOMAIN"
    ok "Сертификат получен"

    # Шаг 3: финальный nginx с HTTPS
    log "Шаг 3/4: Переключение на HTTPS..."
    cp nginx.conf nginx-ssl-backup.conf
    # nginx.conf уже финальный — восстанавливаем из репо
    git checkout nginx.conf 2>/dev/null || cp /dev/stdin nginx.conf << 'NGINX'
# (будет восстановлен из файла nginx.conf в папке)
NGINX
    compose restart nginx
    ok "Nginx перезапущен с HTTPS"

    # Шаг 4: суперпользователь
    log "Шаг 4/4: Создание суперпользователя..."
    compose exec web python manage.py createsuperuser
    ok "=== Развёртывание завершено! ==="
    echo ""
    echo -e "  Сайт: ${BOLD}https://$DOMAIN${NC}"
    echo -e "  Админка: ${BOLD}https://$DOMAIN/admin${NC}"
    ;;

  # ─── Запуск (после первого раза) ──────────────────────────
  up|start)
    log "Запуск контейнеров..."
    compose up -d
    ok "Запущено"
    ;;

  # ─── Остановка ────────────────────────────────────────────
  down|stop)
    log "Остановка..."
    compose down
    ok "Остановлено"
    ;;

  # ─── Пересборка после изменений кода ──────────────────────
  rebuild)
    log "Пересборка web-контейнера..."
    compose build web
    compose up -d web
    ok "Готово"
    ;;

  # ─── Логи ─────────────────────────────────────────────────
  logs)
    SERVICE=${2:-}
    [ -n "$SERVICE" ] && compose logs -f "$SERVICE" || compose logs -f
    ;;

  # ─── Статус ───────────────────────────────────────────────
  status)
    compose ps
    ;;

  # ─── Django команды ───────────────────────────────────────
  manage)
    shift
    compose exec web python manage.py "$@"
    ;;

  createsuperuser)
    compose exec web python manage.py createsuperuser
    ;;

  shell)
    compose exec web bash
    ;;

  # ─── Бэкап БД ─────────────────────────────────────────────
  backup)
    TS=$(date +%Y%m%d_%H%M%S)
    FILE="backup_${TS}.sql"
    source .env
    compose exec db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$FILE"
    ok "Бэкап: $FILE"
    ;;

  # ─── Полная очистка ───────────────────────────────────────
  clean)
    warn "Удалит ВСЕ данные включая БД!"
    echo -n "Введи 'yes' для подтверждения: "
    read -r C
    [ "$C" = "yes" ] || { log "Отменено"; exit 0; }
    compose down -v --remove-orphans
    ok "Очищено"
    ;;

  # ─── Помощь ───────────────────────────────────────────────
  help|*)
    echo -e "${BOLD}Команды:${NC}"
    echo "  init              — Первый запуск (сборка + SSL + суперпользователь)"
    echo "  up / start        — Запустить (после первого раза)"
    echo "  down / stop       — Остановить"
    echo "  rebuild           — Пересобрать после изменений кода"
    echo "  logs [web|db|nginx] — Логи контейнеров"
    echo "  status            — Статус контейнеров"
    echo "  createsuperuser   — Создать суперпользователя"
    echo "  manage <команда>  — Выполнить manage.py"
    echo "  backup            — Дамп базы данных"
    echo "  shell             — Bash внутри контейнера"
    echo "  clean             — Удалить всё включая данные"
    ;;
esac

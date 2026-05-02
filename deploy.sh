#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
#  TaskManager — скрипт развёртывания
#  Работает на: Linux, macOS, Windows (Git Bash / WSL)
# ══════════════════════════════════════════════════════════════
set -euo pipefail

# ─── Цвета ────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ─── Баннер ───────────────────────────────────────────────────
echo -e "${BOLD}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║       TaskManager  Deployment        ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# ─── Проверка зависимостей ────────────────────────────────────
check_deps() {
    log "Проверка зависимостей..."
    command -v docker  >/dev/null 2>&1 || fail "Docker не установлен. https://docs.docker.com/get-docker/"
    command -v docker compose version >/dev/null 2>&1 || \
    command -v docker-compose >/dev/null 2>&1          || \
        fail "Docker Compose не найден"
    ok "Docker найден: $(docker --version)"
}

# ─── Определяем команду compose ───────────────────────────────
compose_cmd() {
    if docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    else
        echo "docker-compose"
    fi
}

# ─── Подготовка .env ──────────────────────────────────────────
setup_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            warn "Создан .env из .env.example — ОБЯЗАТЕЛЬНО проверь SECRET_KEY и пароль БД!"
            warn "Нажми Enter для продолжения или Ctrl+C для отмены..."
            read -r
        else
            fail ".env файл не найден и .env.example тоже отсутствует"
        fi
    else
        ok ".env найден"
    fi
}

# ─── Команды ──────────────────────────────────────────────────
CMD=${1:-help}
COMPOSE=$(compose_cmd)

case "$CMD" in

  # ── Первый запуск / полное развёртывание ──────────────────
  up|start|deploy)
    check_deps
    setup_env
    log "Собираем образ..."
    $COMPOSE build --no-cache
    log "Запускаем контейнеры..."
    $COMPOSE up -d
    log "Ждём готовности базы данных..."
    sleep 3
    ok "Развёртывание завершено!"
    echo ""
    echo -e "  ${BOLD}Приложение доступно:${NC} http://localhost:$(grep APP_PORT .env 2>/dev/null | cut -d= -f2 || echo 8000)"
    echo -e "  ${BOLD}Логи:${NC}               ./deploy.sh logs"
    echo -e "  ${BOLD}Остановить:${NC}         ./deploy.sh down"
    ;;

  # ── Пересборка после изменений кода ───────────────────────
  rebuild)
    check_deps
    log "Пересобираем web-контейнер..."
    $COMPOSE build web
    $COMPOSE up -d web
    ok "Готово"
    ;;

  # ── Остановка ─────────────────────────────────────────────
  down|stop)
    log "Останавливаем контейнеры..."
    $COMPOSE down
    ok "Остановлено"
    ;;

  # ── Полная очистка (включая volumes!) ─────────────────────
  clean)
    warn "Это удалит ВСЕ данные включая БД и медиафайлы!"
    echo -n "Продолжить? (yes/no): "
    read -r CONFIRM
    [ "$CONFIRM" = "yes" ] || { log "Отменено"; exit 0; }
    $COMPOSE down -v --remove-orphans
    ok "Всё очищено"
    ;;

  # ── Логи ──────────────────────────────────────────────────
  logs)
    SERVICE=${2:-}
    if [ -n "$SERVICE" ]; then
        $COMPOSE logs -f "$SERVICE"
    else
        $COMPOSE logs -f
    fi
    ;;

  # ── Django manage.py ──────────────────────────────────────
  manage)
    shift
    $COMPOSE exec web python manage.py "$@"
    ;;

  # ── Создать суперпользователя ─────────────────────────────
  createsuperuser)
    log "Создаём суперпользователя Django..."
    $COMPOSE exec web python manage.py createsuperuser
    ;;

  # ── Статус контейнеров ────────────────────────────────────
  status|ps)
    $COMPOSE ps
    ;;

  # ── Bash внутри контейнера ────────────────────────────────
  shell)
    $COMPOSE exec web bash
    ;;

  # ── Бэкап базы данных ─────────────────────────────────────
  backup)
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="backup_${TIMESTAMP}.sql"
    log "Создаём бэкап БД → $BACKUP_FILE"
    source .env 2>/dev/null || true
    $COMPOSE exec db pg_dump -U "${POSTGRES_USER:-taskuser}" "${POSTGRES_DB:-taskmanager}" > "$BACKUP_FILE"
    ok "Бэкап сохранён: $BACKUP_FILE"
    ;;

  # ── Восстановление из бэкапа ──────────────────────────────
  restore)
    BACKUP_FILE=${2:-}
    [ -f "$BACKUP_FILE" ] || fail "Укажи файл: ./deploy.sh restore backup_XXXXXXXX.sql"
    warn "Это перезапишет текущую БД!"
    echo -n "Продолжить? (yes/no): "
    read -r CONFIRM
    [ "$CONFIRM" = "yes" ] || { log "Отменено"; exit 0; }
    source .env 2>/dev/null || true
    $COMPOSE exec -T db psql -U "${POSTGRES_USER:-taskuser}" "${POSTGRES_DB:-taskmanager}" < "$BACKUP_FILE"
    ok "База восстановлена из $BACKUP_FILE"
    ;;

  # ── Помощь ────────────────────────────────────────────────
  help|*)
    echo -e "${BOLD}Использование:${NC} ./deploy.sh <команда> [аргументы]"
    echo ""
    echo -e "${BOLD}Команды:${NC}"
    echo "  up / deploy        — Первый запуск (сборка + старт)"
    echo "  rebuild            — Пересобрать после изменений кода"
    echo "  down / stop        — Остановить контейнеры"
    echo "  clean              — Удалить всё включая данные БД"
    echo "  logs [service]     — Показать логи (web / db)"
    echo "  status             — Статус контейнеров"
    echo "  shell              — Bash внутри web-контейнера"
    echo "  createsuperuser    — Создать суперпользователя Django"
    echo "  manage <команда>   — Выполнить manage.py команду"
    echo "  backup             — Создать дамп БД"
    echo "  restore <файл>     — Восстановить БД из дампа"
    echo ""
    echo -e "${BOLD}Примеры:${NC}"
    echo "  ./deploy.sh up"
    echo "  ./deploy.sh logs web"
    echo "  ./deploy.sh manage makemigrations"
    echo "  ./deploy.sh backup"
    ;;

esac

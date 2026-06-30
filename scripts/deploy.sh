#!/bin/bash
set -e

# ─── 嘉元瑞通工厂管理系统 一键部署/更新脚本 ───
# 用法:
#   首次部署:   sudo bash scripts/deploy.sh init
#   日常更新:   sudo bash scripts/deploy.sh update
#   查看日志:   docker compose logs -f
# ──────────────────────────────────────────

ENV_FILE=".env"
COMPOSE_FILE="docker-compose.yml"
MIGRATIONS=(
  "migrate_20260629_internal_confirm.py"
  "migrate_20260629_production_log_process_sheet.py"
  "migrate_20260630_process_sheet_fields.py"
  "migrate_20260630_role_permissions.py"
)

color_green='\033[0;32m'
color_yellow='\033[1;33m'
color_red='\033[0;31m'
color_reset='\033[0m'

info()  { echo -e "${color_green}[INFO]${color_reset} $1"; }
warn()  { echo -e "${color_yellow}[WARN]${color_reset} $1"; }
error() { echo -e "${color_red}[ERROR]${color_reset} $1"; }

check_prereqs() {
  if ! command -v docker &>/dev/null; then
    error "Docker 未安装，请先安装 Docker"
    echo "CentOS: sudo yum install -y yum-utils && sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo && sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin && sudo systemctl enable --now docker"
    exit 1
  fi

  if ! docker compose version &>/dev/null; then
    error "Docker Compose 不可用"
    exit 1
  fi
}

init_db() {
  info "初始化数据库表结构..."
  docker compose exec -T backend python init_db.py

  info "运行数据库迁移..."
  for m in "${MIGRATIONS[@]}"; do
    if docker compose exec -T backend test -f "$m" 2>/dev/null; then
      info "  执行迁移: $m"
      docker compose exec -T backend python "$m" || warn "  迁移 $m 可能已执行过，跳过"
    fi
  done
}

cmd_init() {
  check_prereqs

  if [ ! -f "$ENV_FILE" ]; then
    if [ -f ".env.example" ]; then
      cp .env.example .env
      warn ".env 文件已从 .env.example 创建，请编辑 .env 修改密码和密钥后再运行"
      info "执行: vi .env"
      exit 0
    else
      error "缺少 .env 文件"
      exit 1
    fi
  fi

  info "构建并启动所有服务..."
  docker compose up -d --build

  info "等待数据库就绪..."
  docker compose exec db bash -c "while ! mysqladmin ping -h localhost --silent 2>/dev/null; do sleep 1; done"

  init_db

  info ""
  info "部署完成!"
  info "  前端: http://服务器IP"
  info "  健康检查: curl http://服务器IP/api/health"
  info "  账号: admin / admin123"
  info ""
  warn "首次使用请在后台设置 → Webhook 中配置 system_base_url（当前服务器公网地址）"
}

cmd_update() {
  check_prereqs

  if [ -d ".git" ]; then
    info "拉取最新代码..."
    git pull
  else
    warn "不是 git 仓库，跳过 git pull"
  fi

  info "备份数据库..."
  local bak_file="backup_$(date +%Y%m%d_%H%M%S).sql"
  docker compose exec -T db mysqldump -uroot -p"${MYSQL_ROOT_PASSWORD}" huazhi > "$bak_file" 2>/dev/null || \
    warn "数据库备份失败，跳过"

  info "重新构建并重启服务..."
  docker compose up -d --build

  info "检查并运行新迁移..."
  init_db

  info "更新完成!"
}

case "${1:-}" in
  init)
    cmd_init
    ;;
  update)
    cmd_update
    ;;
  *)
    echo "用法: bash scripts/deploy.sh {init|update}"
    echo ""
    echo "  init   - 首次部署（构建、启动、初始化数据库）"
    echo "  update - 日常更新（git pull、备份、重建、迁移）"
    exit 1
    ;;
esac

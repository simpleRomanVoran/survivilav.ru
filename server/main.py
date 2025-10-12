#!/usr/bin/env python3
# main.py
import os
import sys
import json
import logging
import signal
import secrets
import random
import string
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request, Depends, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ----------------------------
# Конфигурация путей / констант
# ----------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

USER_REQUEST_PATH = os.path.join(DATA_DIR, "user_request.json")
INVITES_PATH = os.path.join(DATA_DIR, "invites.json")

# ----------------------------
# Логирование
# ----------------------------
log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")
log_path = os.path.join(LOG_DIR, log_filename)
log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
date_format = "%H:%M:%S"

logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    datefmt=date_format,
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

# Дополнительно: чтобы uvicorn/fastapi тоже логировали в тот же файл/консоль
for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "asyncio", "fastapi"]:
    log = logging.getLogger(logger_name)
    log.setLevel(logging.DEBUG)
    # добавим те же handlers
    log.handlers = [logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()]
    log.propagate = False

# ----------------------------
# Locks для атомарности записи
# ----------------------------
_user_lock = Lock()
_invites_lock = Lock()

# ----------------------------
# Настройка FastAPI
# ----------------------------
app = FastAPI(
    title="Survivilav API",
    version="0.1",
    description="Базовое API для Survivilav проекта",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # при необходимости указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Админ API-ключ
# ----------------------------
ADMIN_API_KEY = os.getenv("ADMIN_KEY") or "Serversurvivilav_2846"

if not ADMIN_API_KEY:
    # Если ключ не задан — генерируем временный и логируем (удобно для dev)
    ADMIN_API_KEY = secrets.token_urlsafe(24)
    logger.warning("SURVIVILAV_ADMIN_KEY not set. Generated temporary admin key (log output).")
    # Также печатаем в stdout, чтобы пользователь видел
    print(f"[WARN] SURVIVILAV_ADMIN_KEY not set. Generated API key: {ADMIN_API_KEY}")

def require_api_key(x_api_key: Optional[str] = Header(None), api_key: Optional[str] = Query(None)):
    """
    Проверяет X-API-Key header или query param api_key.
    """
    key = x_api_key or api_key
    if not key or key != ADMIN_API_KEY:
        logger.warning("Unauthorized access attempt to protected endpoint.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key.")
    return True

# ----------------------------
# Утилиты работы с файлами
# ----------------------------
def _ensure_json(path: str, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

_ensure_json(USER_REQUEST_PATH, [])
_ensure_json(INVITES_PATH, [])

def load_requests() -> list:
    with _user_lock:
        try:
            with open(USER_REQUEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("load_requests error: %s", e)
            return []

def save_requests(data: list):
    with _user_lock:
        with open(USER_REQUEST_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def load_invites() -> list:
    with _invites_lock:
        try:
            with open(INVITES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("load_invites error: %s", e)
            return []

def save_invites(data: list):
    with _invites_lock:
        with open(INVITES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------
# Модели
# ----------------------------
class UserRequestModel(BaseModel):
    nickname: Optional[str] = ""
    invite: Optional[str] = ""
    about: Optional[str] = ""
    telegram: Optional[str] = ""
    email: Optional[str] = ""
    source: Optional[str] = ""
    expectations: Optional[str] = ""
    age: Optional[str] = ""

class InviteCreateModel(BaseModel):
    code: Optional[str] = None
    ttl_seconds: Optional[int] = None  # TTL в секундах
    author: Optional[str] = ""
    max_uses: Optional[int] = 1
    note: Optional[str] = ""

# ----------------------------
# Invite utilities
# ----------------------------
def gen_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))

def find_invite(code: str) -> Optional[dict]:
    invites = load_invites()
    for inv in invites:
        if inv.get("code") == code:
            return inv
    return None

def is_invite_expired(inv: dict) -> bool:
    expires = inv.get("expires_at")
    if not expires:
        return False
    try:
        exp_dt = datetime.fromisoformat(expires)
        return datetime.utcnow() > exp_dt
    except Exception:
        return False

# ----------------------------
# API endpoints
# ----------------------------
@app.get("/api/ping")
async def ping():
    logger.info("Ping received")
    return {"status": "pong"}

@app.post("/api/request")
async def send_request(request: Request, user: UserRequestModel):
    """
    Отправка заявки.
    - валидация: нужно хотя бы nickname или invite
    - max 1 заявка с одного IP
    - если указан invite: проверка и занесение записи used_by
    """
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Request received from IP={client_host} nickname='{user.nickname}' invite='{user.invite}'")

    # Валидация: хотя бы одно из обязательных полей должно быть непустым
    if not (user.nickname and user.nickname.strip()) and not (user.invite and user.invite.strip()):
        logger.warning("Validation failed: neither nickname nor invite provided")
        raise HTTPException(status_code=400, detail="Заполните хотя бы ник или приглашение.")

    if user.about and len(user.about) > 3000:
        logger.warning("Validation failed: about too long")
        raise HTTPException(status_code=400, detail="Поле 'О вас' слишком длинное (макс 3000 символов).")

    # Ограничение: одна заявка на IP
    data = load_requests()
    if any(r.get("ip") == client_host for r in data):
        logger.warning("Duplicate request from same IP blocked: %s", client_host)
        raise HTTPException(status_code=400, detail="С этого IP уже была отправлена заявка.")

    # Если указан invite - проверяем
    if user.invite and user.invite.strip():
        inv = find_invite(user.invite.strip())
        if not inv:
            logger.info("Invite not found: %s", user.invite)
            raise HTTPException(status_code=400, detail="Приглашение не найдено.")
        if is_invite_expired(inv):
            logger.info("Invite expired: %s", inv.get("code"))
            raise HTTPException(status_code=400, detail="Приглашение просрочено.")
        uses = len(inv.get("used_by", []))
        max_uses = inv.get("max_uses")
        if max_uses is not None and uses >= max_uses:
            logger.info("Invite uses exhausted: %s (uses=%s max=%s)", inv.get("code"), uses, max_uses)
            raise HTTPException(status_code=400, detail="Приглашение исчерпало лимит использований.")

        # Добавление использования в invites.json
        use_record = {
            "nickname": user.nickname or "",
            "ip": client_host,
            "created_at": datetime.utcnow().isoformat()
        }
        # update invites atomically
        invites_all = load_invites()
        for idx, ii in enumerate(invites_all):
            if ii.get("code") == inv.get("code"):
                invites_all[idx].setdefault("used_by", []).append(use_record)
                break
        save_invites(invites_all)
        logger.info("Invite %s used by %s (%s)", inv.get("code"), use_record["nickname"], client_host)

    # Сохраняем заявку
    user_obj = user.dict()
    user_obj["ip"] = client_host
    user_obj["created_at"] = datetime.utcnow().isoformat()
    data.append(user_obj)
    save_requests(data)
    logger.info("Saved request: %s (ip=%s)", user_obj.get("nickname"), client_host)

    return {"success": True, "message": "Заявка успешно отправлена."}

@app.post("/api/cancel")
async def cancel_request(nickname: str = Query(..., description="Nickname to cancel")):
    logger.info("Cancel request called for nickname=%s", nickname)
    data = load_requests()
    new = [r for r in data if r.get("nickname") != nickname]
    if len(new) == len(data):
        logger.warning("Cancel failed: nickname not found: %s", nickname)
        raise HTTPException(status_code=404, detail="Заявка не найдена.")
    save_requests(new)
    logger.info("Canceled request for nickname=%s", nickname)
    return {"success": True, "message": f"Заявка {nickname} удалена."}

# ----------------------------
# Invite endpoints (protected)
# ----------------------------
@app.post("/api/invite/create")
async def create_invite(inv: InviteCreateModel, _auth: bool = Depends(require_api_key)):
    invites = load_invites()

    code = (inv.code or "").strip() or gen_code()
    if any(i.get("code") == code for i in invites):
        logger.warning("Attempt to create existing invite code: %s", code)
        raise HTTPException(status_code=400, detail="Код приглашения уже существует.")

    created_at = datetime.utcnow()
    expires_at = None
    if inv.ttl_seconds and inv.ttl_seconds > 0:
        expires_at = (created_at + timedelta(seconds=int(inv.ttl_seconds))).isoformat()

    new_invite = {
        "code": code,
        "author": inv.author or "",
        "created_at": created_at.isoformat(),
        "ttl_seconds": int(inv.ttl_seconds) if inv.ttl_seconds else None,
        "expires_at": expires_at,
        "max_uses": int(inv.max_uses) if inv.max_uses else 1,
        "used_by": [],
        "note": inv.note or ""
    }
    invites.append(new_invite)
    save_invites(invites)
    logger.info("Created invite %s author=%s ttl=%s max_uses=%s", code, new_invite["author"], new_invite["ttl_seconds"], new_invite["max_uses"])
    return {"success": True, "invite": {"code": code, "expires_at": expires_at, "max_uses": new_invite["max_uses"]}}

@app.get("/api/invite/validate")
async def validate_invite(code: str = Query(..., description="Invite code to validate")):
    logger.info("Validate invite called for code=%s", code)
    inv = find_invite(code)
    if not inv:
        logger.info("Invite not found: %s", code)
        raise HTTPException(status_code=404, detail="Приглашение не найдено.")
    if is_invite_expired(inv):
        logger.info("Invite expired: %s", code)
        raise HTTPException(status_code=400, detail="Приглашение просрочено.")
    uses = len(inv.get("used_by", []))
    max_uses = inv.get("max_uses")
    if max_uses is not None and uses >= max_uses:
        logger.info("Invite exhausted: %s", code)
        raise HTTPException(status_code=400, detail="Приглашение исчерпано.")
    return {"success": True, "message": "Приглашение действительно.", "invite": {
        "code": inv.get("code"),
        "author": inv.get("author"),
        "created_at": inv.get("created_at"),
        "expires_at": inv.get("expires_at"),
        "max_uses": inv.get("max_uses"),
        "uses": uses,
        "note": inv.get("note", "")
    }}

@app.post("/api/invite/delete")
async def delete_invite(code: str = Query(..., description="Invite code to delete"), _auth: bool = Depends(require_api_key)):
    logger.info("Delete invite called for code=%s", code)
    invites = load_invites()
    new = [i for i in invites if i.get("code") != code]
    if len(new) == len(invites):
        logger.warning("Delete failed: invite not found: %s", code)
        raise HTTPException(status_code=404, detail="Приглашение не найдено.")
    save_invites(new)
    logger.info("Invite deleted: %s", code)
    return {"success": True, "message": f"Приглашение {code} удалено."}

@app.get("/api/invite/list")
async def list_invites(_auth: bool = Depends(require_api_key)):
    invites = load_invites()
    out = []
    for i in invites:
        out.append({
            "code": i.get("code"),
            "author": i.get("author"),
            "created_at": i.get("created_at"),
            "expires_at": i.get("expires_at"),
            "max_uses": i.get("max_uses"),
            "uses": len(i.get("used_by", [])),
            "note": i.get("note", ""),
            # при желании можно вернуть used_by, но осторожно с приватностью
            "used_by": i.get("used_by", [])
        })
    logger.info("List invites called (count=%s)", len(out))
    return {"success": True, "invites": out}

# ----------------------------
# Graceful shutdown / signals
# ----------------------------
def close_logging_handlers():
    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        try:
            h.flush()
            h.close()
        except Exception:
            pass
        root_logger.removeHandler(h)
    # try to clean named loggers too
    for name in ["main", "uvicorn", "uvicorn.error", "uvicorn.access", "asyncio", "fastapi"]:
        log = logging.getLogger(name)
        for h in list(log.handlers):
            try:
                h.flush()
                h.close()
            except Exception:
                pass
            log.removeHandler(h)
    logging.shutdown()

def _graceful_exit(signame: str):
    logger.info("Received %s signal — graceful shutdown", signame)
    try:
        # любые финализации можно добавить здесь
        close_logging_handlers()
    finally:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

# Регистрация signal handlers
def _register_signal_handlers():
    for sig_name in ("SIGINT", "SIGTERM", "SIGTSTP"):
        if hasattr(signal, sig_name):
            sig = getattr(signal, sig_name)
            if sig_name == "SIGTSTP":
                # SIGTSTP обычно ставит процесс на паузу; мы логируем
                def _handle_tstp(signum, frame):
                    logger.info("SIGTSTP received (usually Ctrl+Z) - process suspended/continued by terminal.")
                signal.signal(sig, _handle_tstp)
            else:
                def _make_handler(name):
                    return lambda s, f: _graceful_exit(name)
                signal.signal(sig, _make_handler(sig_name))

_register_signal_handlers()

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("FastAPI shutdown event triggered")
    close_logging_handlers()

# ----------------------------
# Запуск
# ----------------------------
if __name__ == "__main__":
    logger.info("Starting Survivilav API (uvicorn)...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None
    )

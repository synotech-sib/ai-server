# config/security_cfg.py

ADMIN_PASSWORD = "synotech0773!"
WHITELIST_IDS = ["wschoi", "admin_syno"]

# 보안 모드 상태
SECURITY_MODE = "Active"

def check_admin(pw):
    return pw == ADMIN_PASSWORD
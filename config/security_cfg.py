# config/security_cfg.py

# 허가된 관리자 ID 리스트 (화이트리스트)
WHITELIST_IDS = ["wschoi", "syno_admin", "seoyeon_choi"]

ADMIN_PASSWORD = "synotech0773!"

# 보안 모드 설정
SECURITY_MODE = "Enforced (ID+PW)"

def verify_admin_access(user_id, password):
    """ID가 화이트리스트에 있고 비밀번호가 일치하는지 검증"""
    if user_id in WHITELIST_IDS and password == ADMIN_PASSWORD:
        return True
    return False
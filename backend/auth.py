from fastapi import Request


# simple session check helper
def require_login(request: Request):
    if "user" not in request.session:
        return False
    return True

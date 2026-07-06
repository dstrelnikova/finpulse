def can_create_multiple_chats(user_roles: set[str]) -> bool:
    return "admin" in user_roles or "pro" in user_roles

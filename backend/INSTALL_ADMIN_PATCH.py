from pathlib import Path
p=Path(__file__).resolve().parent/"main.py"
s=p.read_text(encoding="utf-8")
if "from admin_router import router as admin_router" not in s:
    lines=s.splitlines()
    insert_at=0
    for i,line in enumerate(lines):
        if "from auth_router import router as auth_router" in line:
            insert_at=i+1
            break
    lines.insert(insert_at,"from admin_router import router as admin_router")
    s="\n".join(lines)+("\n" if s.endswith("\n") else "")
if "app.include_router(admin_router)" not in s:
    marker="app.include_router(auth_router)"
    if marker in s: s=s.replace(marker,marker+"\napp.include_router(admin_router)",1)
    else: s += "\napp.include_router(admin_router)\n"
p.write_text(s,encoding="utf-8")
print("ADMIN ROUTER PATCHED: main.py")

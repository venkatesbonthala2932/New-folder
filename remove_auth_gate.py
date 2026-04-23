import re

with open('hospital_page.html', 'r') as f:
    content = f.read()

# Remove CSS for authGate
content = re.sub(r'/\* ── AUTH GATE ──.*?</style>', '</style>', content, flags=re.DOTALL)

# Remove HTML for authGate
content = re.sub(r'<!-- ╔═══.*?END AUTH GATE -->', '<!-- Auth Gate Removed -->', content, flags=re.DOTALL)

# Modify checkSession so it doesn't show authGate
content = content.replace('showAuthGate(); // no token = definitely not logged in, show the wall', 'setLoggedOut();')
content = content.replace('showAuthGate(); // force login again', 'setLoggedOut();')
content = content.replace('showAuthGate(); // server unreachable → keep gate up (security first)', 'setLoggedOut();')

# Remove hideAuthGate from setLoggedIn
content = content.replace('hideAuthGate();', '')

# Remove showAuthGate from setLoggedOut
content = content.replace('showAuthGate();', '')

with open('hospital_page.html', 'w') as f:
    f.write(content)

print("Removed AuthGate successfully.")

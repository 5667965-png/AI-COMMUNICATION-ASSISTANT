# Headless test of the Streamlit app's core logic.
# Mocks the streamlit module so the app file can be imported
# outside a Streamlit run, then tests the real functions.
import sys
from unittest.mock import MagicMock


class SS(dict):
    def __getattr__(self, k):
        return self.get(k)

    def __setattr__(self, k, v):
        self[k] = v


fake = MagicMock()
fake.cache_resource = lambda **kw: (lambda f: f)
fake.session_state = SS()
fake.sidebar.radio = lambda *a, **k: "Home"
fake.columns = lambda n: [MagicMock() for _ in range(n)]
sys.modules["streamlit"] = fake

import importlib.util

spec = importlib.util.spec_from_file_location(
    "app", "streamlit_app/streamlit_app.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# --- Command engine ---
assert mod.run_command("hello")["command"] == "GREETING"
assert mod.run_command("thank_you")["message"] == "You're welcome!"
assert mod.run_command("unknown_sign")["success"] is False
print("command engine: OK")

# --- Sentence builder ---
assert mod.build_natural_sentence(["me", "water"]) == "I want water."
assert mod.build_natural_sentence(["thank_you"]) == "Thank you."
assert mod.build_natural_sentence(["hello"]) == "Hello."
assert mod.build_natural_sentence(["go", "school"]) == "I want to go to school."
assert mod.build_natural_sentence(["mother", "home"]) == "Mother is at home."
assert mod.build_natural_sentence([]) == ""
print("sentence builder: OK")

# --- Sign detection (synthetic image, no hand) ---
import numpy as np

img = np.zeros((480, 640, 3), dtype=np.uint8)
model = mod.load_sign_model()
hands = mod.get_hands()
r = mod.detect_sign(img, model, hands)
assert r["sign"] == "No hand detected", r
print("sign detection: OK")

print("model classes sample:", [str(c) for c in model.classes_][:12])
print("ALL CORE TESTS PASSED")

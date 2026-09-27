import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Linking,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { CameraView, useCameraPermissions } from "expo-camera";
import { StatusBar } from "expo-status-bar";

const DEFAULT_API = "http://192.168.1.10:8000";
const TOKEN_KEY = "aca_mobile_token";
const API_KEY = "aca_mobile_api";

const COLORS = {
  bg: "#070B16",
  panel: "#10182A",
  panel2: "#151F34",
  border: "#263653",
  text: "#F5F7FB",
  muted: "#91A0BA",
  primary: "#6C7CFF",
  secondary: "#9B6CFF",
  success: "#35D07F",
  danger: "#FF5D73",
};

const single = {
  hello: "Hello.", goodbye: "Goodbye.", thank_you: "Thank you.",
  sorry: "Sorry.", please: "Please.", yes: "Yes.", no: "No.", okay: "Okay.",
  help: "I need help.", stop: "Please stop.", eat: "I want to eat.",
  drink: "I want to drink.", water: "I want water.", food: "I want food.",
  tea: "I want tea.", come: "Please come.", go: "Please go.", sit: "Please sit.",
  stand: "Please stand.", read: "I want to read.", write: "I want to write.",
  today: "Today.", where: "Where?", what: "What?", when: "When?", me: "Me.",
  you: "You.", he: "He.", she: "She.", mother: "Mother.", father: "Father.",
  brother: "Brother.", sister: "Sister.", friend: "Friend.", teacher: "Teacher.",
  student: "Student.", home: "Home.", school: "School.", hospital: "Hospital.",
  market: "Market."
};

function buildSentence(signs) {
  const a = [...new Set(signs.map((x) => String(x).toLowerCase()))];
  const has = (x) => a.includes(x);
  if (!a.length) return "";
  if (a.length === 1) return single[a[0]] || `${a[0].replace(/_/g, " ")}.`;
  if (has("me") && has("water")) return "I want water.";
  if (has("me") && has("food")) return "I want food.";
  if (has("me") && has("tea")) return "I want tea.";
  if (has("me") && has("eat")) return "I want to eat.";
  if (has("me") && has("drink")) return "I want to drink.";
  if (has("me") && has("go") && has("school")) return "I want to go to school.";
  if (has("go") && has("market")) return "I want to go to the market.";
  if (has("go") && has("hospital")) return "I want to go to the hospital.";
  if (has("help") && has("hospital")) return "I need help at the hospital.";
  if (has("where") && has("school")) return "Where is the school?";
  if (has("where") && has("hospital")) return "Where is the hospital?";
  if (has("teacher") && has("school")) return "The teacher is at school.";
  if (has("student") && has("school")) return "The student is at school.";
  if (has("mother") && has("home")) return "Mother is at home.";
  if (has("father") && has("home")) return "Father is at home.";
  if (has("friend") && has("home")) return "My friend is at home.";
  return a.map((x) => x.replace(/_/g, " ")).join(" ").replace(/^./, (m) => m.toUpperCase()) + ".";
}

export default function App() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [api, setApi] = useState(DEFAULT_API);
  const [apiDraft, setApiDraft] = useState(DEFAULT_API);
  const [authMode, setAuthMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState("camera");
  const [history, setHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [message, setMessage] = useState("");
  const [signs, setSigns] = useState([]);
  const [detected, setDetected] = useState("");
  const [confidence, setConfidence] = useState(0);
  const [cameraOn, setCameraOn] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef(null);
  const timerRef = useRef(null);
  const predictionRef = useRef([]);
  const lastCommitRef = useRef("");
  const lastCommitTimeRef = useRef(0);

  const sentence = useMemo(() => buildSentence(signs), [signs]);

  useEffect(() => {
    (async () => {
      const [savedToken, savedApi] = await Promise.all([
        AsyncStorage.getItem(TOKEN_KEY),
        AsyncStorage.getItem(API_KEY),
      ]);
      if (savedApi) {
        setApi(savedApi);
        setApiDraft(savedApi);
      }
      if (savedToken) {
        setToken(savedToken);
        try {
          const r = await fetch(`${savedApi || DEFAULT_API}/api/auth/me`, {
            headers: { Authorization: `Bearer ${savedToken}` },
          });
          const d = await r.json();
          if (r.ok) setUser(d.user);
          else await AsyncStorage.removeItem(TOKEN_KEY);
        } catch (_) {}
      }
      setLoading(false);
    })();
  }, []);

  useEffect(() => {
    if (token) loadUserData();
  }, [token, api]);

  useEffect(() => () => stopDetection(), []);

  async function request(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (options.body && !(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
    const r = await fetch(`${api}${path}`, { ...options, headers });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.detail || "Request failed");
    return d;
  }

  async function loadUserData() {
    try {
      const [h, f, c] = await Promise.all([
        request("/api/user/history"),
        request("/api/user/favorites"),
        request("/api/user/emergency-contacts"),
      ]);
      setHistory(h.items || []);
      setFavorites(f.items || []);
      setContacts(c.items || []);
    } catch (_) {}
  }

  async function auth() {
    if (!email.trim() || !password.trim() || (authMode === "register" && !name.trim())) {
      Alert.alert("Missing details", "Please fill all required fields.");
      return;
    }
    setBusy(true);
    try {
      const path = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
      const body = authMode === "login" ? { email, password } : { name, email, password };
      const r = await fetch(`${api}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Authentication failed");
      await AsyncStorage.setItem(TOKEN_KEY, d.token);
      setToken(d.token);
      setUser(d.user);
      setPassword("");
    } catch (e) {
      Alert.alert("Login/Register failed", e.message);
    } finally { setBusy(false); }
  }

  async function logout() {
    try { await request("/api/auth/logout", { method: "POST" }); } catch (_) {}
    stopDetection();
    await AsyncStorage.removeItem(TOKEN_KEY);
    setToken(null); setUser(null); setHistory([]); setFavorites([]); setContacts([]);
  }

  async function addHistory(type, value) {
    if (!token || !value?.trim()) return;
    try {
      await request("/api/user/history", { method: "POST", body: JSON.stringify({ type, value }) });
      setHistory((old) => [{ type, value, time: new Date().toISOString() }, ...old]);
    } catch (_) {}
  }

  async function toggleFavorite(value) {
    const clean = value.trim();
    if (!clean) return;
    try {
      if (favorites.includes(clean)) {
        await request(`/api/user/favorites/${encodeURIComponent(clean)}`, { method: "DELETE" });
        setFavorites((old) => old.filter((x) => x !== clean));
      } else {
        await request("/api/user/favorites", { method: "POST", body: JSON.stringify({ value: clean }) });
        setFavorites((old) => [clean, ...old]);
      }
    } catch (e) { Alert.alert("Favorite error", e.message); }
  }

  async function addContact() {
    Alert.prompt("Emergency contact", "Enter phone number", async (value) => {
      const clean = value?.trim();
      if (!clean) return;
      try {
        await request("/api/user/emergency-contacts", { method: "POST", body: JSON.stringify({ contact: clean }) });
        setContacts((old) => old.includes(clean) ? old : [...old, clean]);
      } catch (e) { Alert.alert("Contact error", e.message); }
    }, "plain-text");
  }

  async function removeContact(contact) {
    try {
      await request(`/api/user/emergency-contacts/${encodeURIComponent(contact)}`, { method: "DELETE" });
      setContacts((old) => old.filter((x) => x !== contact));
    } catch (e) { Alert.alert("Contact error", e.message); }
  }

  async function clearHistory() {
    try {
      await request("/api/user/history", { method: "DELETE" });
      setHistory([]);
    } catch (e) { Alert.alert("History error", e.message); }
  }

  function speak(value) {
    // Mobile speech can be added with expo-speech without changing the backend.
    // Keeping the app dependency-light for the first Android build.
    if (value) Alert.alert("Message", value);
  }

  async function detectOnce() {
    if (!cameraRef.current) return;
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.55, skipProcessing: true });
      if (!photo?.uri) return;
      const form = new FormData();
      form.append("file", { uri: photo.uri, name: "camera.jpg", type: "image/jpeg" });
      const r = await fetch(`${api}/api/sign-camera`, { method: "POST", body: form, headers: token ? { Authorization: `Bearer ${token}` } : {} });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Detection failed");
      if (d.sign === "No hand detected") {
        setDetected("No hand detected"); setConfidence(0); predictionRef.current = [];
        return;
      }
      setDetected(d.sign || "Unknown");
      setConfidence(Number(d.confidence || 0));
      const sign = d.sign;
      predictionRef.current = [...predictionRef.current, sign].slice(-3);
      if (predictionRef.current.length === 3 && predictionRef.current.every((x) => x === sign)) {
        const now = Date.now();
        if (sign !== lastCommitRef.current || now - lastCommitTimeRef.current > 1600) {
          lastCommitRef.current = sign;
          lastCommitTimeRef.current = now;
          setSigns((old) => [...old, sign].slice(-12));
          setMessage(sign);
          await addHistory("SIGN", sign);
        }
        predictionRef.current = [];
      }
    } catch (e) {
      setDetected("Detection error");
    }
  }

  function startDetection() {
    if (timerRef.current) return;
    setCameraOn(true);
    timerRef.current = setInterval(detectOnce, 1400);
  }

  function stopDetection() {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    setCameraOn(false);
  }

  function clearSentence() {
    setSigns([]); setMessage(""); setDetected(""); setConfidence(0); predictionRef.current = []; lastCommitRef.current = "";
  }

  async function saveApi() {
    const value = apiDraft.trim().replace(/\/$/, "");
    if (!value) return;
    await AsyncStorage.setItem(API_KEY, value);
    setApi(value);
    Alert.alert("Saved", "Backend address saved.");
  }

  function sendEmergency() {
    if (!contacts.length) { Alert.alert("No contact", "Add an emergency contact first."); return; }
    const body = encodeURIComponent(message || "I need help. Please contact me.");
    Linking.openURL(`sms:${contacts[0]}?body=${body}`);
  }

  if (loading) return <SafeAreaView style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></SafeAreaView>;

  if (!token || !user) {
    return (
      <SafeAreaView style={styles.root}>
        <StatusBar style="light" />
        <ScrollView contentContainerStyle={styles.authWrap}>
          <View style={styles.logo}><Text style={styles.logoText}>🤟</Text></View>
          <Text style={styles.title}>AI Communication Assistant</Text>
          <Text style={styles.sub}>ISL • Voice • Text • Emergency</Text>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{authMode === "login" ? "Welcome back" : "Create account"}</Text>
            {authMode === "register" && <TextInput style={styles.input} placeholder="Full name" placeholderTextColor={COLORS.muted} value={name} onChangeText={setName} />}
            <TextInput style={styles.input} placeholder="Email" placeholderTextColor={COLORS.muted} autoCapitalize="none" keyboardType="email-address" value={email} onChangeText={setEmail} />
            <TextInput style={styles.input} placeholder="Password" placeholderTextColor={COLORS.muted} secureTextEntry value={password} onChangeText={setPassword} />
            <TouchableOpacity style={styles.primary} onPress={auth} disabled={busy}><Text style={styles.primaryText}>{busy ? "Please wait..." : authMode === "login" ? "Login" : "Register"}</Text></TouchableOpacity>
            <TouchableOpacity onPress={() => setAuthMode(authMode === "login" ? "register" : "login")}><Text style={styles.link}>{authMode === "login" ? "Create a new account" : "I already have an account"}</Text></TouchableOpacity>
          </View>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Backend address</Text>
            <TextInput style={styles.input} placeholder="http://192.168.x.x:8000" placeholderTextColor={COLORS.muted} value={apiDraft} onChangeText={setApiDraft} autoCapitalize="none" />
            <TouchableOpacity style={styles.secondary} onPress={saveApi}><Text style={styles.secondaryText}>Save Backend URL</Text></TouchableOpacity>
            <Text style={styles.help}>Android phone आणि PC same Wi‑Fi वर असणे आवश्यक आहे.</Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  const nav = [
    ["camera", "🤟", "Camera"], ["conversation", "💬", "Chat"], ["history", "🕘", "History"],
    ["favorites", "⭐", "Favorites"], ["emergency", "🚨", "Emergency"], ["settings", "⚙️", "Settings"]
  ];

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="light" />
      <View style={styles.header}><View><Text style={styles.headerTitle}>AI Communication</Text><Text style={styles.headerSub}>{user.name}</Text></View><TouchableOpacity onPress={logout}><Text style={styles.logout}>Logout</Text></TouchableOpacity></View>

      <ScrollView contentContainerStyle={styles.content}>
        {page === "camera" && (
          <>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>🤟 ISL Camera</Text>
              <View style={styles.cameraBox}>
                {permission?.granted && cameraOn ? <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="front" /> : <View style={styles.cameraEmpty}><Text style={styles.cameraEmoji}>📷</Text><Text style={styles.help}>{permission?.granted ? "Start camera detection" : "Camera permission required"}</Text></View>}
                <View style={styles.overlay}><Text style={styles.detected}>{detected || "Waiting for sign..."}</Text><Text style={styles.conf}>{Math.round(confidence * 100)}%</Text></View>
              </View>
              <View style={styles.row}>
                <TouchableOpacity style={styles.primarySmall} onPress={async () => { if (!permission?.granted) await requestPermission(); startDetection(); }}><Text style={styles.primaryText}>Start Detection</Text></TouchableOpacity>
                <TouchableOpacity style={styles.secondarySmall} onPress={stopDetection}><Text style={styles.secondaryText}>Stop</Text></TouchableOpacity>
              </View>
            </View>
            <View style={styles.card}><Text style={styles.cardTitle}>📝 AI Sentence</Text><Text style={styles.sentence}>{sentence || "Detected signs will become a sentence here."}</Text><View style={styles.row}><TouchableOpacity style={styles.secondarySmall} onPress={() => toggleFavorite(sentence)} disabled={!sentence}><Text style={styles.secondaryText}>{favorites.includes(sentence) ? "★ Saved" : "☆ Favorite"}</Text></TouchableOpacity><TouchableOpacity style={styles.secondarySmall} onPress={clearSentence}><Text style={styles.secondaryText}>Clear</Text></TouchableOpacity></View></View>
          </>
        )}

        {page === "conversation" && <View style={styles.card}><Text style={styles.cardTitle}>💬 Two-Way Conversation</Text><Text style={styles.label}>ISL user</Text><Text style={styles.sentence}>{sentence || "No sign message yet."}</Text><Text style={styles.label}>Speaking user</Text><TextInput style={[styles.input, styles.messageInput]} multiline placeholder="Type a message..." placeholderTextColor={COLORS.muted} value={message} onChangeText={setMessage} /><TouchableOpacity style={styles.primary} onPress={() => addHistory("TEXT", message)}><Text style={styles.primaryText}>Save Message</Text></TouchableOpacity></View>}

        {page === "history" && <View style={styles.card}><View style={styles.spaceRow}><Text style={styles.cardTitle}>🕘 History</Text><TouchableOpacity onPress={clearHistory}><Text style={styles.dangerText}>Clear</Text></TouchableOpacity></View>{history.length === 0 ? <Text style={styles.help}>No history yet.</Text> : history.map((x, i) => <View style={styles.listRow} key={`${x.id || i}-${i}`}><Text style={styles.listType}>{x.type}</Text><Text style={styles.listValue}>{x.value}</Text><Text style={styles.time}>{x.time ? new Date(x.time).toLocaleString() : ""}</Text></View>)}</View>}

        {page === "favorites" && <View style={styles.card}><Text style={styles.cardTitle}>⭐ Favorites</Text>{favorites.length === 0 ? <Text style={styles.help}>No favorites yet.</Text> : favorites.map((x) => <View style={styles.listRow} key={x}><Text style={styles.listValue}>{x}</Text><TouchableOpacity onPress={() => toggleFavorite(x)}><Text style={styles.dangerText}>Remove</Text></TouchableOpacity></View>)}</View>}

        {page === "emergency" && <View style={styles.card}><Text style={styles.cardTitle}>🚨 Emergency Center</Text><TextInput style={[styles.input, styles.messageInput]} multiline value={message} onChangeText={setMessage} placeholder="Emergency message" placeholderTextColor={COLORS.muted} /><TouchableOpacity style={styles.dangerButton} onPress={sendEmergency}><Text style={styles.primaryText}>Open Emergency SMS</Text></TouchableOpacity><TouchableOpacity style={styles.secondary} onPress={addContact}><Text style={styles.secondaryText}>Add Emergency Contact</Text></TouchableOpacity>{contacts.map((c) => <View style={styles.listRow} key={c}><Text style={styles.listValue}>{c}</Text><TouchableOpacity onPress={() => removeContact(c)}><Text style={styles.dangerText}>Remove</Text></TouchableOpacity></View>)}</View>}

        {page === "settings" && <View style={styles.card}><Text style={styles.cardTitle}>⚙️ Settings</Text><Text style={styles.label}>Backend URL</Text><TextInput style={styles.input} value={apiDraft} onChangeText={setApiDraft} autoCapitalize="none" /><TouchableOpacity style={styles.primary} onPress={saveApi}><Text style={styles.primaryText}>Save</Text></TouchableOpacity><Text style={styles.label}>Account</Text><Text style={styles.help}>{user.name} • {user.email}</Text><Text style={styles.label}>Database</Text><Text style={styles.help}>History, Favorites and Emergency Contacts are stored per account in the FastAPI SQLite database.</Text></View>}
      </ScrollView>

      <View style={styles.nav}>{nav.map(([id, icon, label]) => <TouchableOpacity key={id} style={[styles.navItem, page === id && styles.navActive]} onPress={() => setPage(id)}><Text style={styles.navIcon}>{icon}</Text><Text style={styles.navText}>{label}</Text></TouchableOpacity>)}</View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: COLORS.bg },
  center: { flex: 1, backgroundColor: COLORS.bg, alignItems: "center", justifyContent: "center" },
  authWrap: { padding: 24, paddingTop: 50, alignItems: "stretch" },
  logo: { alignSelf: "center", width: 84, height: 84, borderRadius: 24, backgroundColor: COLORS.panel2, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: COLORS.border },
  logoText: { fontSize: 42 },
  title: { color: COLORS.text, fontSize: 28, fontWeight: "800", textAlign: "center", marginTop: 18 },
  sub: { color: COLORS.muted, textAlign: "center", marginTop: 8, marginBottom: 24 },
  header: { paddingHorizontal: 18, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: COLORS.border, flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  headerTitle: { color: COLORS.text, fontSize: 20, fontWeight: "800" },
  headerSub: { color: COLORS.muted, marginTop: 2 },
  logout: { color: COLORS.danger, fontWeight: "700" },
  content: { padding: 16, paddingBottom: 100 },
  card: { backgroundColor: COLORS.panel, borderWidth: 1, borderColor: COLORS.border, borderRadius: 18, padding: 16, marginBottom: 14 },
  cardTitle: { color: COLORS.text, fontSize: 18, fontWeight: "800", marginBottom: 14 },
  input: { backgroundColor: COLORS.panel2, borderWidth: 1, borderColor: COLORS.border, color: COLORS.text, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, marginBottom: 12 },
  messageInput: { minHeight: 100, textAlignVertical: "top" },
  primary: { backgroundColor: COLORS.primary, borderRadius: 12, paddingVertical: 13, alignItems: "center", marginBottom: 12 },
  primarySmall: { flex: 1, backgroundColor: COLORS.primary, borderRadius: 12, paddingVertical: 12, alignItems: "center", marginRight: 6 },
  secondary: { backgroundColor: COLORS.panel2, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, paddingVertical: 13, alignItems: "center", marginBottom: 12 },
  secondarySmall: { flex: 1, backgroundColor: COLORS.panel2, borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, paddingVertical: 12, alignItems: "center", marginHorizontal: 4 },
  dangerButton: { backgroundColor: COLORS.danger, borderRadius: 12, paddingVertical: 13, alignItems: "center", marginBottom: 12 },
  primaryText: { color: "#fff", fontWeight: "800" },
  secondaryText: { color: COLORS.text, fontWeight: "700" },
  link: { color: "#AAB4FF", textAlign: "center", marginTop: 4, fontWeight: "700" },
  help: { color: COLORS.muted, lineHeight: 20 },
  label: { color: COLORS.muted, fontSize: 12, fontWeight: "800", textTransform: "uppercase", marginBottom: 8, marginTop: 8 },
  cameraBox: { height: 390, borderRadius: 18, overflow: "hidden", backgroundColor: "#050811", position: "relative", marginBottom: 12 },
  cameraEmpty: { flex: 1, alignItems: "center", justifyContent: "center" },
  cameraEmoji: { fontSize: 50, marginBottom: 10 },
  overlay: { position: "absolute", left: 12, right: 12, bottom: 12, backgroundColor: "rgba(0,0,0,.65)", borderRadius: 14, padding: 12 },
  detected: { color: COLORS.text, fontSize: 20, fontWeight: "800" },
  conf: { color: COLORS.success, marginTop: 4, fontWeight: "700" },
  row: { flexDirection: "row", alignItems: "center", marginTop: 4 },
  sentence: { color: COLORS.text, fontSize: 22, fontWeight: "700", lineHeight: 30, marginBottom: 14 },
  listRow: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: COLORS.border, flexDirection: "row", alignItems: "center", gap: 10 },
  listType: { color: COLORS.primary, fontSize: 11, fontWeight: "800", width: 70 },
  listValue: { color: COLORS.text, flex: 1 },
  time: { color: COLORS.muted, fontSize: 10, maxWidth: 90 },
  dangerText: { color: COLORS.danger, fontWeight: "800" },
  spaceRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  nav: { position: "absolute", left: 8, right: 8, bottom: 8, backgroundColor: COLORS.panel2, borderWidth: 1, borderColor: COLORS.border, borderRadius: 18, flexDirection: "row", padding: 5 },
  navItem: { flex: 1, alignItems: "center", paddingVertical: 8, borderRadius: 13 },
  navActive: { backgroundColor: "#27345A" },
  navIcon: { fontSize: 18 },
  navText: { color: COLORS.muted, fontSize: 9, marginTop: 2 },
});

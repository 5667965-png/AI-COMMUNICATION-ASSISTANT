import { useEffect, useRef, useState } from "react";
import "./App.css";
import "./Auth.css";
import "./QuickFeatures.css";
import QuickFeatures from "./QuickFeatures.jsx";

// Android emulators reach the development computer through 10.0.2.2.
// Physical devices should set VITE_API_URL to the computer's LAN address.
const getDefaultApiUrl = () => {
  if (window.location.protocol === "capacitor:" ||
      window.location.protocol === "file:") {
    // Android emulator -> development computer.
    return "http://10.0.2.2:8000";
  }

  // Browser on the laptop or another device on the same Wi-Fi.
  // This automatically uses the same host that served the frontend.
  const host = window.location.hostname || "127.0.0.1";
  return `http://${host}:8000`;
};

const API = import.meta.env.VITE_API_URL || getDefaultApiUrl();

const AUTH_TOKEN_KEY = "aca_auth_token";

const EMERGENCY_MESSAGES = [
  "I need help.",
  "Please call my family.",
  "Please call an ambulance.",
  "Please take me to a hospital.",
];

function App() {
  // ============================================================
  // AUTHENTICATION
  // ============================================================

  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authMode, setAuthMode] = useState("login");
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [adminUser, setAdminUser] = useState(null);
  const [adminStats, setAdminStats] = useState(null);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminHistory, setAdminHistory] = useState([]);
  const [adminContacts, setAdminContacts] = useState([]);
  const ADMIN_TOKEN_KEY = "aca_admin_token";

  // ============================================================
  // CORE COMMUNICATION STATE
  // ============================================================

  const [text, setText] = useState("");
  const [sentence, setSentence] = useState("");
  const [listening, setListening] = useState(false);

  // ============================================================
  // CAMERA STATE
  // ============================================================

  const [cameraOn, setCameraOn] = useState(false);
  const [autoDetect, setAutoDetect] = useState(false);

  // ============================================================
  // VOICE
  // ============================================================

  const [autoRead, setAutoRead] = useState(true);

  // ============================================================
  // BACKEND
  // ============================================================

  const [backendStatus, setBackendStatus] = useState("Checking...");

  // ============================================================
  // DETECTION
  // ============================================================

  const [detectedSign, setDetectedSign] = useState("");
  const [detectedConfidence, setDetectedConfidence] = useState(0);
  const [signResult, setSignResult] = useState("");

  // ============================================================
  // COMMAND ENGINE
  // ============================================================

  const [lastCommand, setLastCommand] = useState(null);

  // ============================================================
  // APP FEATURES
  // ============================================================

  const [activePage, setActivePage] = useState("home");
  const [conversationMode, setConversationMode] = useState(false);

  const [history, setHistory] = useState([]);
  const [favorites, setFavorites] = useState([]);

  const [language, setLanguage] = useState("English");
  const [fontScale, setFontScale] = useState(1);

  // ============================================================
  // EMERGENCY
  // ============================================================

  const [emergencyContacts, setEmergencyContacts] = useState([]);

  const [emergencyMessage, setEmergencyMessage] = useState(
    "I need help. Please contact me."
  );

  const [locationEnabled, setLocationEnabled] = useState(false);
  const [emergencyTap, setEmergencyTap] = useState(false);

  // ============================================================
  // REFS
  // ============================================================

  const videoRef = useRef(null);

  const predictionHistory = useRef([]);
  const confidenceHistory = useRef([]);

  const committedSign = useRef("");
  const lastCommitTime = useRef(0);

  const noHandCount = useRef(0);

  const detectingRef = useRef(false);

  const handWasRemoved = useRef(false);

  const autoReadRef = useRef(autoRead);

  const emergencyTimer = useRef(null);

  // Keeps the original detected sign sequence separate from the natural sentence text.
  // This prevents phrases such as thank_you from being split into normal words.
  const sentenceSignsRef = useRef([]);

  // ============================================================
  // KEEP AUTO READ REF UPDATED
  // ============================================================

  useEffect(() => {
    autoReadRef.current = autoRead;
  }, [autoRead]);

  // ============================================================
  // SPEECH
  // ============================================================

  const speakTextValue = (value) => {
    if (!value || !value.trim()) return;

    if (!("speechSynthesis" in window)) {
      alert("Text to speech is not supported in this browser.");
      return;
    }

    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(value);

    speech.lang =
      language === "Marathi"
        ? "mr-IN"
        : language === "Hindi"
        ? "hi-IN"
        : "en-US";

    speech.rate = 0.9;
    speech.pitch = 1;

    window.speechSynthesis.speak(speech);
  };

  // ============================================================
  // START CAMERA
  // ============================================================

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
      });

      if (!videoRef.current) return;

      videoRef.current.srcObject = stream;

      setCameraOn(true);
      setSignResult("Camera started. Show a hand sign.");
      setDetectedSign("Waiting for sign...");
      setDetectedConfidence(0);

      predictionHistory.current = [];
      confidenceHistory.current = [];

      committedSign.current = "";
      noHandCount.current = 0;
      handWasRemoved.current = false;
    } catch (error) {
      console.error("Camera error:", error);
      alert("Could not access camera.");
    }
  };

  // ============================================================
  // STOP CAMERA
  // ============================================================

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject
        .getTracks()
        .forEach((track) => track.stop());

      videoRef.current.srcObject = null;
    }

    setAutoDetect(false);
    setCameraOn(false);

    predictionHistory.current = [];
    confidenceHistory.current = [];

    committedSign.current = "";
    noHandCount.current = 0;
    handWasRemoved.current = false;

    setDetectedSign("");
    setDetectedConfidence(0);
    setSignResult("Camera stopped.");
  };

  // ============================================================
  // AUTO DETECT
  // ============================================================

  const toggleAutoDetect = () => {
    if (!cameraOn) {
      alert("Please start the camera first.");
      return;
    }

    setAutoDetect((value) => !value);
  };

  // ============================================================
  // COMMAND HISTORY
  // ============================================================

  const addCommandHistory = (data, sign) => {
    const item = {
      id: Date.now() + Math.random(),
      sign,
      command: data.command || "UNKNOWN",
      message: data.message || "No message",
      time: new Date().toLocaleTimeString(),
    };

    setLastCommand(item);

    return item;
  };

  // ============================================================
  // SAVE COMMUNICATION HISTORY
  // ============================================================

  const authFetch = async (path, options = {}) => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    return fetch(`${API}${path}`, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token
          ? { Authorization: `Bearer ${token}` }
          : {}),
      },
    });
  };

  // ============================================================
  // SAVE COMMUNICATION HISTORY
  // ============================================================

  const addHistory = async (type, value) => {
    if (!value?.trim()) return;

    const item = {
      id: Date.now() + Math.random(),
      type,
      value: value.trim(),
      time: new Date().toLocaleString(),
    };

    setHistory((old) => [item, ...old].slice(0, 100));

    try {
      await authFetch("/api/user/history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: type,
          message: value.trim(),
        }),
      });
    } catch (error) {
      console.error("History save error:", error);
    }
  };

  // ============================================================
  // LOAD USER DATA FROM DATABASE
  // ============================================================

  useEffect(() => {
    if (!user) return;

    const loadUserData = async () => {
      try {
        const [historyResponse, favoritesResponse, contactsResponse] =
          await Promise.all([
            authFetch("/api/user/history"),
            authFetch("/api/user/favorites"),
            authFetch("/api/user/emergency-contacts"),
          ]);

        if (historyResponse.ok) {
          const data = await historyResponse.json();
          const rows = Array.isArray(data.history) ? data.history : [];
          setHistory(
            rows.map((row) => ({
              id: row.id ?? Date.now() + Math.random(),
              type: row.source || "COMMUNICATION",
              value: row.message || "",
              time: row.created_at
                ? new Date(row.created_at).toLocaleString()
                : "",
            }))
          );
        }

        if (favoritesResponse.ok) {
          const data = await favoritesResponse.json();
          const rows = Array.isArray(data.favorites) ? data.favorites : [];
          setFavorites(
            rows
              .map((row) =>
                typeof row === "string" ? row : row?.message
              )
              .filter(Boolean)
          );
        }

        if (contactsResponse.ok) {
          const data = await contactsResponse.json();
          const rows = Array.isArray(data.contacts) ? data.contacts : [];
          // Keep the existing UI/state simple: emergencyContacts stores phone strings.
          setEmergencyContacts(
            rows
              .map((row) =>
                typeof row === "string" ? row : row?.phone
              )
              .filter(Boolean)
          );
        }
      } catch (error) {
        console.error("User data load error:", error);
      }
    };

    loadUserData();
  }, [user]);

  // ============================================================
  // FAVORITES
  // ============================================================

  const toggleFavorite = async (value) => {
    if (!value?.trim()) return;

    const cleanValue = value.trim();
    const exists = favorites.includes(cleanValue);

    setFavorites((old) =>
      exists
        ? old.filter((item) => item !== cleanValue)
        : [cleanValue, ...old]
    );

    try {
      if (exists) {
        await authFetch(
          `/api/user/favorites/${encodeURIComponent(cleanValue)}`,
          { method: "DELETE" }
        );
      } else {
        await authFetch("/api/user/favorites", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: cleanValue }),
        });
      }
    } catch (error) {
      console.error("Favorite save error:", error);
    }
  };
   // ============================================================
// AI NATURAL SENTENCE BUILDER
// ============================================================

const buildNaturalSentence = (words) => {
  if (!Array.isArray(words) || words.length === 0) return "";

  const cleanWords = words
    .map((word) => String(word || "").toLowerCase().trim())
    .filter(Boolean);

  if (cleanWords.length === 0) return "";

  // Remove only consecutive duplicate detections. The camera stability layer
  // already filters most duplicates, but this keeps the sentence clean too.
  const uniqueSequence = cleanWords.filter(
    (word, index) => index === 0 || word !== cleanWords[index - 1]
  );

  const key = uniqueSequence.join("|");
  const has = (word) => uniqueSequence.includes(word);
  const contains = (a, b) => has(a) && has(b);

  // Exact natural phrases. Order is respected where it makes the phrase clearer.
  const exactPhrases = {
    "hello": "Hello.",
    "goodbye": "Goodbye.",
    "thank_you": "Thank you.",
    "sorry": "Sorry.",
    "please": "Please.",
    "yes": "Yes.",
    "no": "No.",
    "okay": "Okay.",
    "help": "I need help.",
    "stop": "Please stop.",
    "eat": "I want to eat.",
    "drink": "I want to drink.",
    "water": "I want water.",
    "food": "I want food.",
    "tea": "I want tea.",
    "come": "Please come.",
    "go": "Please go.",
    "sit": "Please sit.",
    "stand": "Please stand.",
    "read": "I want to read.",
    "write": "I want to write.",
    "today": "Today.",
    "where": "Where?",
    "what": "What?",
    "when": "When?",
    "me": "Me.",
    "you": "You.",
    "he": "He.",
    "she": "She.",
    "mother": "Mother.",
    "father": "Father.",
    "brother": "Brother.",
    "sister": "Sister.",
    "friend": "Friend.",
    "teacher": "Teacher.",
    "student": "Student.",
    "home": "Home.",
    "school": "School.",
    "hospital": "Hospital.",
    "market": "Market.",
  };

  if (uniqueSequence.length === 1) {
    return exactPhrases[key] || capitalizeFirst(uniqueSequence[0].replace(/_/g, " ")) + ".";
  }

  // Common first-person requests.
  if (contains("me", "water")) return "I want water.";
  if (contains("me", "food")) return "I want food.";
  if (contains("me", "tea")) return "I want tea.";
  if (contains("me", "eat")) return "I want to eat.";
  if (contains("me", "drink")) return "I want to drink.";
  if (contains("me", "read")) return "I want to read.";
  if (contains("me", "write")) return "I want to write.";
  if (contains("me", "go") && has("school")) return "I want to go to school.";
  if (contains("me", "go") && has("market")) return "I want to go to the market.";
  if (contains("me", "go") && has("hospital")) return "I want to go to the hospital.";
  if (contains("me", "go")) return "I want to go.";
  if (contains("me", "come")) return "I want to come.";

  // Requests involving another person.
  if (contains("you", "come")) return "Please come.";
  if (contains("you", "go") && has("school")) return "Please go to school.";
  if (contains("you", "go") && has("market")) return "Please go to the market.";
  if (contains("you", "go")) return "Please go.";
  if (contains("you", "sit")) return "Please sit.";
  if (contains("you", "stand")) return "Please stand.";

  // Location / people combinations.
  if (contains("mother", "home")) return "Mother is at home.";
  if (contains("father", "home")) return "Father is at home.";
  if (contains("brother", "home")) return "Brother is at home.";
  if (contains("sister", "home")) return "Sister is at home.";
  if (contains("friend", "home")) return "My friend is at home.";
  if (contains("teacher", "school")) return "The teacher is at school.";
  if (contains("student", "school")) return "The student is at school.";

  // Need / emergency combinations.
  if (contains("help", "hospital")) return "I need help at the hospital.";
  if (contains("help", "friend")) return "I need help from my friend.";
  if (contains("help", "teacher")) return "I need help from my teacher.";
  if (contains("help", "mother")) return "I need help from my mother.";
  if (contains("help", "father")) return "I need help from my father.";
  if (contains("stop", "please")) return "Please stop.";

  // Question combinations.
  if (contains("where", "home")) return "Where is home?";
  if (contains("where", "school")) return "Where is the school?";
  if (contains("where", "hospital")) return "Where is the hospital?";
  if (contains("where", "market")) return "Where is the market?";
  if (contains("what", "food")) return "What is the food?";
  if (contains("what", "drink")) return "What should I drink?";
  if (contains("when", "school")) return "When is school?";
  if (contains("when", "today")) return "When today?";

  // Time / activity combinations.
  if (contains("today", "school")) return "I have school today.";
  if (contains("today", "home")) return "I am at home today.";
  if (contains("today", "go") && has("school")) return "I want to go to school today.";
  if (contains("today", "go") && has("market")) return "I want to go to the market today.";
  if (contains("today", "go") && has("hospital")) return "I want to go to the hospital today.";

  // Direct action + destination combinations.
  if (contains("go", "school")) return "I want to go to school.";
  if (contains("go", "market")) return "I want to go to the market.";
  if (contains("go", "hospital")) return "I want to go to the hospital.";
  if (contains("come", "home")) return "Please come home.";
  if (contains("sit", "home")) return "Please sit at home.";
  if (contains("stand", "school")) return "Please stand at school.";

  // Polite action phrases.
  if (contains("please", "eat")) return "Please eat.";
  if (contains("please", "drink")) return "Please drink.";
  if (contains("please", "come")) return "Please come.";
  if (contains("please", "go")) return "Please go.";
  if (contains("please", "sit")) return "Please sit.";
  if (contains("please", "stand")) return "Please stand.";
  if (contains("please", "help")) return "Please help me.";

  // Food / drink combinations.
  if (contains("food", "tea")) return "I want food and tea.";
  if (contains("water", "tea")) return "I want water and tea.";
  if (contains("eat", "food")) return "I want to eat food.";
  if (contains("drink", "water")) return "I want to drink water.";
  if (contains("drink", "tea")) return "I want to drink tea.";

  // Relationships.
  if (contains("mother", "father")) return "Mother and father.";
  if (contains("brother", "sister")) return "Brother and sister.";
  if (contains("friend", "teacher")) return "My friend and teacher.";

  // Final safe fallback. Keep multi-word signs readable.
  const result = uniqueSequence
    .map((word) => word.replace(/_/g, " "))
    .join(" ");

  return capitalizeFirst(result) + ".";
};

// ============================================================
// CAPITALIZE FIRST LETTER
// ============================================================

const capitalizeFirst = (value) => {
  if (!value) return "";

  return (
    value.charAt(0).toUpperCase() +
    value.slice(1)
  );
};
  // ============================================================
  // COMMIT SIGN
  // ============================================================

  const commitSign = async (sign) => {
    const now = Date.now();

    if (
      committedSign.current === sign &&
      !handWasRemoved.current
    ) {
      return;
    }

    if (
      now - lastCommitTime.current < 1000 &&
      !handWasRemoved.current
    ) {
      return;
    }

    committedSign.current = sign;
    lastCommitTime.current = now;
    handWasRemoved.current = false;

    setDetectedSign(sign);
    setText(sign);

    // Keep raw signs so the AI builder receives the real sign sequence.
    // This avoids turning "thank_you" into separate words such as "thank" and "you".
    sentenceSignsRef.current = [
      ...sentenceSignsRef.current,
      sign,
    ].slice(-12);

    setSentence(buildNaturalSentence(sentenceSignsRef.current));

    addHistory("ISL", sign);

    // Command Engine
    try {
      const response = await fetch(`${API}/api/command`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          sign,
        }),
      });

      if (!response.ok) {
        throw new Error("Command Engine request failed");
      }

      const data = await response.json();

      const commandItem = addCommandHistory(data, sign);

      if (data.success) {
        setSignResult(
          `🟢 ${sign} → ${data.command} | ${data.message}`
        );
      } else {
        setSignResult(`✅ Confirmed: ${sign}`);
      }

      if (autoReadRef.current) {
        setTimeout(() => {
          setSentence((currentSentence) => {
            speakTextValue(currentSentence);
            return currentSentence;
          });
        }, 150);
      }

      console.log("COMMAND ENGINE:", commandItem);
    } catch (error) {
      console.error("Command Engine error:", error);

      setSignResult(`✅ Confirmed: ${sign}`);

      setLastCommand({
        id: Date.now(),
        sign,
        command: "NOT_CONNECTED",
        message: "Command Engine unavailable",
        time: new Date().toLocaleTimeString(),
      });
    }
  };

  // ============================================================
  // CAMERA DETECTION
  // ============================================================

  const captureAndDetectSign = async () => {
    if (detectingRef.current) return;

    if (!videoRef.current) return;

    if (
      videoRef.current.videoWidth === 0 ||
      videoRef.current.videoHeight === 0
    ) {
      return;
    }

    detectingRef.current = true;

    try {
      const canvas = document.createElement("canvas");

      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;

      const context = canvas.getContext("2d");

      context.drawImage(
        videoRef.current,
        0,
        0,
        canvas.width,
        canvas.height
      );

      const blob = await new Promise((resolve) => {
        canvas.toBlob(resolve, "image/jpeg", 0.85);
      });

      if (!blob) return;

      const formData = new FormData();

      formData.append(
        "file",
        blob,
        "camera.jpg"
      );

      const response = await fetch(
        `${API}/api/sign-camera`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      const data = await response.json();

      // --------------------------------------------------------
      // NO HAND
      // --------------------------------------------------------

      if (data.sign === "No hand detected") {
        noHandCount.current += 1;

        setDetectedSign("No hand detected");
        setDetectedConfidence(0);
        setSignResult("🔴 No hand detected");

        predictionHistory.current = [];
        confidenceHistory.current = [];

        if (noHandCount.current >= 2) {
          committedSign.current = "";
          handWasRemoved.current = true;
        }

        return;
      }

      noHandCount.current = 0;

      // --------------------------------------------------------
      // UNCERTAIN
      // --------------------------------------------------------

      if (
        !data.sign ||
        data.sign === "Uncertain"
      ) {
        predictionHistory.current = [];
        confidenceHistory.current = [];

        setDetectedSign("Uncertain");
        setDetectedConfidence(0);
        setSignResult("🟡 Uncertain prediction");

        return;
      }

      const currentSign = String(data.sign);
      const currentConfidence = Number(data.confidence);

      if (!Number.isFinite(currentConfidence)) {
        return;
      }

      // --------------------------------------------------------
      // LIVE UI
      // --------------------------------------------------------

      setDetectedSign(currentSign);

      setDetectedConfidence(
        Math.round(currentConfidence * 100)
      );

      // --------------------------------------------------------
      // LOW CONFIDENCE
      // --------------------------------------------------------

      if (currentConfidence < 0.45) {
        predictionHistory.current = [];
        confidenceHistory.current = [];

        setSignResult(
          `🟡 Low Confidence | ${currentSign} | ${Math.round(
            currentConfidence * 100
          )}%`
        );

        return;
      }

      // --------------------------------------------------------
      // HISTORY
      // --------------------------------------------------------

      predictionHistory.current.push(currentSign);
      confidenceHistory.current.push(currentConfidence);

      if (predictionHistory.current.length > 7) {
        predictionHistory.current.shift();
      }

      if (confidenceHistory.current.length > 7) {
        confidenceHistory.current.shift();
      }

      // --------------------------------------------------------
      // MAJORITY
      // --------------------------------------------------------

      const counts = {};

      predictionHistory.current.forEach((value) => {
        counts[value] = (counts[value] || 0) + 1;
      });

      let majoritySign = currentSign;
      let majorityCount = 0;

      Object.entries(counts).forEach(
        ([value, count]) => {
          if (count > majorityCount) {
            majoritySign = value;
            majorityCount = count;
          }
        }
      );

      // --------------------------------------------------------
      // AVERAGE CONFIDENCE
      // --------------------------------------------------------

      const averageConfidence =
        confidenceHistory.current.reduce(
          (sum, value) => sum + value,
          0
        ) /
        confidenceHistory.current.length;

      // --------------------------------------------------------
      // STABILITY
      // --------------------------------------------------------

      const requiredVotes = 4;

      if (
        majorityCount < requiredVotes ||
        averageConfidence < 0.55
      ) {
        setSignResult(
          `🟠 Stabilizing | ${majoritySign} | Votes: ${majorityCount}/${requiredVotes} | Avg: ${Math.round(
            averageConfidence * 100
          )}%`
        );

        return;
      }

      // --------------------------------------------------------
      // EXTRA CONSISTENCY
      // --------------------------------------------------------

      const recentHistory =
        predictionHistory.current.slice(-4);

      const recentSameCount =
        recentHistory.filter(
          (value) => value === majoritySign
        ).length;

      if (recentSameCount < 3) {
        setSignResult(
          `🟠 Checking stability | ${majoritySign}`
        );

        return;
      }

      // --------------------------------------------------------
      // READY
      // --------------------------------------------------------

      setDetectedSign(majoritySign);

      setDetectedConfidence(
        Math.round(averageConfidence * 100)
      );

      setSignResult(
        `🟢 Stable: ${majoritySign} | ${Math.round(
          averageConfidence * 100
        )}%`
      );

      commitSign(majoritySign);
    } catch (error) {
      console.error("Camera sign error:", error);

      setSignResult(
        "🔴 Could not connect to backend."
      );
    } finally {
      detectingRef.current = false;
    }
  };

  // ============================================================
  // AUTO DETECTION LOOP
  // ============================================================

  useEffect(() => {
    if (!autoDetect || !cameraOn) return;

    const interval = setInterval(() => {
      captureAndDetectSign();
    }, 500);

    return () => clearInterval(interval);
  }, [autoDetect, cameraOn]);

  // ============================================================
  // BACKEND HEALTH
  // ============================================================

  useEffect(() => {
    fetch(`${API}/api/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Backend unavailable");
        }

        return response.json();
      })
      .then((data) => {
        setBackendStatus(
          data.status === "ok"
            ? "Connected"
            : "Backend Error"
        );
      })
      .catch(() => {
        setBackendStatus("Disconnected");
      });
  }, []);

  // ============================================================
  // SPEECH TO TEXT
  // ============================================================

  const startSpeechRecognition = () => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert(
        "Speech recognition is not supported in this browser."
      );
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang =
      language === "Marathi"
        ? "mr-IN"
        : language === "Hindi"
        ? "hi-IN"
        : "en-US";

    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setListening(true);
    };

    recognition.onresult = (event) => {
      const result =
        event.results[0][0].transcript;

      setText(result);

      addHistory("VOICE", result);

      setListening(false);
    };

    recognition.onerror = () => {
      setListening(false);
      alert("Could not recognize speech.");
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognition.start();
  };

  // ============================================================
  // SEND TEXT
  // ============================================================

  const sendMessageToBackend = async () => {
    if (!text.trim()) {
      alert("Please enter a message.");
      return;
    }

    try {
      const response = await fetch(
        `${API}/api/message`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Message failed");
      }

      addHistory("TEXT", text);
    } catch (error) {
      console.error(error);
      alert("Could not connect to backend.");
    }
  };

  // ============================================================
  // TEXT TO SPEECH
  // ============================================================

  const speakText = () => {
    const value = sentence || text;

    if (!value.trim()) {
      alert("Please enter a message.");
      return;
    }

    speakTextValue(value);
  };

  // ============================================================
  // CLEAR SENTENCE
  // ============================================================

  const clearSentence = () => {
    setSentence("");
    sentenceSignsRef.current = [];
    setText("");
    setSignResult("");
    setDetectedSign("");
    setDetectedConfidence(0);
    setLastCommand(null);

    predictionHistory.current = [];
    confidenceHistory.current = [];

    committedSign.current = "";
    lastCommitTime.current = 0;
    noHandCount.current = 0;
    handWasRemoved.current = false;

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  };

  // ============================================================
  // EMERGENCY DOUBLE TAP
  // ============================================================

  const emergencyDoubleTap = () => {
    if (emergencyTimer.current) {
      clearTimeout(emergencyTimer.current);
      emergencyTimer.current = null;

      setEmergencyTap(true);

      setTimeout(() => {
        setEmergencyTap(false);
      }, 2000);

      sendEmergency();
      return;
    }

    emergencyTimer.current = setTimeout(() => {
      emergencyTimer.current = null;
    }, 700);
  };

  // ============================================================
  // SEND EMERGENCY
  // ============================================================

  const sendEmergency = async () => {
    const message = emergencyMessage.trim();
    if (!message) {
      alert("Please enter an emergency message.");
      return;
    }

    if (emergencyContacts.length === 0) {
      alert("No emergency contacts saved. Add contacts in Settings.");
      return;
    }

    const confirmed = window.confirm(
      `Send this emergency message to ${emergencyContacts[0]}?\n\n${message}`
    );

    if (!confirmed) return;

    let finalMessage = message;
    if (locationEnabled && navigator.geolocation) {
      finalMessage += "\n\nLocation: requesting...";
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const maps = `https://maps.google.com/?q=${latitude},${longitude}`;
          const body = encodeURIComponent(`${message}\n\nMy location: ${maps}`);
          window.location.href = `sms:${emergencyContacts[0].phone || emergencyContacts[0]}?body=${body}`;
        },
        () => {
          window.location.href = `sms:${emergencyContacts[0].phone || emergencyContacts[0]}?body=${encodeURIComponent(finalMessage)}`;
        },
        { enableHighAccuracy: true, timeout: 8000 }
      );
    } else {
      const body = encodeURIComponent(finalMessage);
      window.location.href = `sms:${emergencyContacts[0].phone || emergencyContacts[0]}?body=${body}`;
    }
    addHistory("EMERGENCY", message);
  };

  // ============================================================
  // SAVE CONTACT
  // ============================================================

  const addEmergencyContact = async () => {
    const contact = window.prompt(
      "Enter emergency contact number:"
    );

    if (!contact?.trim()) return;

    const cleanContact = contact.trim();

    if (emergencyContacts.includes(cleanContact)) return;

    setEmergencyContacts((old) =>
      [...old, cleanContact].slice(0, 5)
    );

    try {
      await authFetch("/api/user/emergency-contacts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Emergency", phone: cleanContact, contact: cleanContact }),
      });
    } catch (error) {
      console.error("Emergency contact save error:", error);
    }
  };

  // ============================================================
  // REMOVE CONTACT
  // ============================================================

  const removeEmergencyContact = async (contact) => {
    setEmergencyContacts((old) =>
      old.filter((item) => item !== contact)
    );

    try {
      await authFetch(
        `/api/user/emergency-contacts/${encodeURIComponent(contact)}`,
        { method: "DELETE" }
      );
    } catch (error) {
      console.error("Emergency contact remove error:", error);
    }
  };

  // ============================================================
  // PAGE EXIT CLEANUP
  // ============================================================

  useEffect(() => {
    return () => {
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject
          .getTracks()
          .forEach((track) => track.stop());
      }

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // ============================================================
  // AUTH CHECK / LOGIN / REGISTER
  // ============================================================

  useEffect(() => {
    const adminToken = localStorage.getItem(ADMIN_TOKEN_KEY);
    if (adminToken) {
      fetch(`${API}/api/admin/me`, {
        headers: { Authorization: `Bearer ${adminToken}` },
      })
        .then(async (response) => {
          if (!response.ok) throw new Error("Admin session expired");
          return response.json();
        })
        .then((data) => setAdminUser(data.admin))
        .catch(() => {
          localStorage.removeItem(ADMIN_TOKEN_KEY);
          setAdminUser(null);
        });
    }

    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    if (!token) {
      setAuthLoading(false);
      return;
    }

    fetch(`${API}/api/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Session expired");
        return response.json();
      })
      .then((data) => {
        setUser(data.user);
      })
      .catch(() => {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setUser(null);
      })
      .finally(() => {
        setAuthLoading(false);
      });
  }, []);

  const submitAuth = async (event) => {
    event.preventDefault();
    setAuthError("");

    if (authMode === "register" && authName.trim().length < 2) {
      setAuthError("Please enter your full name.");
      return;
    }

    if (!authEmail.trim()) {
      setAuthError("Please enter your email.");
      return;
    }

    if (authPassword.length < 6) {
      setAuthError("Password must contain at least 6 characters.");
      return;
    }

    setAuthBusy(true);

    try {
      if (authMode === "admin") {
        const response = await fetch(`${API}/api/admin/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: authEmail.trim(), password: authPassword }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || "Admin authentication failed.");
        localStorage.setItem(ADMIN_TOKEN_KEY, data.token);
        setAdminUser(data.admin);
        setAuthPassword("");
        return;
      }

      const endpoint =
        authMode === "register"
          ? "/api/auth/register"
          : "/api/auth/login";

      const payload =
        authMode === "register"
          ? {
              name: authName.trim(),
              email: authEmail.trim(),
              password: authPassword,
            }
          : {
              email: authEmail.trim(),
              password: authPassword,
            };

      const response = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || "Authentication failed.");
      }

      localStorage.setItem(AUTH_TOKEN_KEY, data.token);
      setUser(data.user);
      setAuthPassword("");
      setAuthError("");
    } catch (error) {
      setAuthError(error.message || "Could not connect to the backend.");
    } finally {
      setAuthBusy(false);
    }
  };

  const adminFetch = async (path, options = {}) => {
    const token = localStorage.getItem(ADMIN_TOKEN_KEY);
    return fetch(`${API}${path}`, {
      ...options,
      headers: {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  };

  const loadAdminDashboard = async () => {
    try {
      const [statsRes, usersRes, historyRes, contactsRes] = await Promise.all([
        adminFetch("/api/admin/stats"),
        adminFetch("/api/admin/users"),
        adminFetch("/api/admin/history"),
        adminFetch("/api/admin/emergency-contacts"),
      ]);
      if (statsRes.ok) setAdminStats(await statsRes.json());
      if (usersRes.ok) setAdminUsers((await usersRes.json()).users || []);
      if (historyRes.ok) setAdminHistory((await historyRes.json()).history || []);
      if (contactsRes.ok) setAdminContacts((await contactsRes.json()).contacts || []);
    } catch (error) {
      console.error("Admin dashboard error:", error);
    }
  };

  useEffect(() => {
    if (adminUser) loadAdminDashboard();
  }, [adminUser]);

  const adminLogout = async () => {
    try {
      await adminFetch("/api/admin/logout", { method: "POST" });
    } catch {}
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    setAdminUser(null);
    setAuthMode("login");
    setAuthEmail("");
    setAuthPassword("");
  };

  const deleteAdminUser = async (id) => {
    if (!window.confirm("Delete this user and their saved data?")) return;
    const response = await adminFetch(`/api/admin/users/${id}`, { method: "DELETE" });
    if (response.ok) loadAdminDashboard();
  };

  const deleteAdminHistory = async (id) => {
    const response = await adminFetch(`/api/admin/history/${id}`, { method: "DELETE" });
    if (response.ok) loadAdminDashboard();
  };

  const logout = async () => {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    try {
      if (token) {
        await fetch(`${API}/api/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      setUser(null);
      setAuthMode("login");
      setAuthName("");
      setAuthEmail("");
      setAuthPassword("");
      setAuthError("");
    }
  };

  // ============================================================
  // NAVIGATION
  // ============================================================

  const navItems = [
    ["home", "🏠", "Home"],
    ["communication", "🤟", "ISL Communication"],
    ["quick", "⚡", "Quick Help"],
    ["conversation", "💬", "Conversation"],
    ["favorites", "⭐", "Favorites"],
    ["history", "🕘", "History"],
    ["emergency", "🚨", "Emergency"],
    ["settings", "⚙️", "Settings"],
    ...(adminUser ? [["admin", "🛡️", "Admin"]] : []),
  ];

  // ============================================================
  // AUTH UI
  // ============================================================

  if (authLoading) {
    return (
      <div className="auth-page">
        <div className="auth-loading-card">
          <div className="auth-logo">🤟</div>
          <h1>AI Communication Assistant</h1>
          <p>Loading your secure session...</p>
          <div className="auth-spinner" />
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="auth-page">
        <div className="auth-background-orb orb-one" />
        <div className="auth-background-orb orb-two" />

        <div className="auth-shell">
          <div className="auth-brand-panel">
            <div className="auth-brand-icon">🤟</div>
            <span className="auth-eyebrow">AI COMMUNICATION PLATFORM</span>
            <h1>Communicate<br />without barriers.</h1>
            <p>
              Indian Sign Language, voice and text in one intelligent communication assistant.
            </p>

            <div className="auth-feature-list">
              <div><span>✓</span> Real ISL sign detection</div>
              <div><span>✓</span> AI natural sentence builder</div>
              <div><span>✓</span> Voice & text communication</div>
              <div><span>✓</span> Emergency communication tools</div>
            </div>
          </div>

          <div className="auth-card">
            <div className="auth-card-top">
              <span className="auth-mini-badge">SECURE ACCESS</span>
              <span className="auth-lock">🔐</span>
            </div>

            <h2>{authMode === "admin" ? "Admin Portal" : authMode === "login" ? "Welcome back" : "Create your account"}</h2>
            <p className="auth-subtitle">
              {authMode === "admin"
                ? "Secure administration for the communication platform."
                : authMode === "login"
                ? "Sign in to continue to your communication dashboard."
                : "Create an account to save your communication workspace."}
            </p>

            <form onSubmit={submitAuth} className="auth-form">
              {authMode === "register" && (
                <label>
                  Full name
                  <input
                    value={authName}
                    onChange={(event) => setAuthName(event.target.value)}
                    placeholder="Enter your name"
                    autoComplete="name"
                  />
                </label>
              )}

              <label>
                Email address
                <input
                  type="email"
                  value={authEmail}
                  onChange={(event) => setAuthEmail(event.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                />
              </label>

              <label>
                Password
                <input
                  type="password"
                  value={authPassword}
                  onChange={(event) => setAuthPassword(event.target.value)}
                  placeholder="Minimum 6 characters"
                  autoComplete={authMode === "login" ? "current-password" : "new-password"}
                />
              </label>

              {authError && (
                <div className="auth-error">⚠ {authError}</div>
              )}

              <button
                type="submit"
                className="auth-submit"
                disabled={authBusy}
              >
                {authBusy
                  ? "Please wait..."
                  : authMode === "admin"
                  ? "Admin Sign In →"
                  : authMode === "login"
                  ? "Sign In →"
                  : "Create Account →"}
              </button>
            </form>

            <div className="auth-divider"><span>OR</span></div>

            <button
              type="button"
              className="auth-switch"
              onClick={() => {
                setAuthMode((mode) =>
                  mode === "login" ? "register" : "login"
                );
                setAuthError("");
              }}
            >
              {authMode === "login"
                ? "New here? Create an account"
                : "Already have an account? Sign in"}
            </button>

            <button
              type="button"
              className="auth-switch admin-entry"
              onClick={() => { setAuthMode(authMode === "admin" ? "login" : "admin"); setAuthError(""); }}
            >
              {authMode === "admin" ? "← Back to User Login" : "🛡️ Admin Portal"}
            </button>

            <p className="auth-security-note">
              🔒 Your password is handled by the backend authentication service.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // ADMIN DASHBOARD
  // ============================================================

  if (adminUser) {
    return (
      <div className="admin-app">
        <header className="admin-topbar">
          <div><span className="auth-mini-badge">ADMIN CONTROL CENTER</span><h1>🛡️ AI Communication Assistant</h1><p>Platform administration & monitoring</p></div>
          <button className="backend-button" onClick={adminLogout}>Logout</button>
        </header>
        <main className="admin-content">
          <section className="admin-stat-grid">
            <div className="admin-stat"><span>USERS</span><strong>{adminStats?.users ?? "—"}</strong></div>
            <div className="admin-stat"><span>MESSAGES</span><strong>{adminStats?.history ?? "—"}</strong></div>
            <div className="admin-stat"><span>FAVORITES</span><strong>{adminStats?.favorites ?? "—"}</strong></div>
            <div className="admin-stat"><span>EMERGENCY CONTACTS</span><strong>{adminStats?.emergency_contacts ?? "—"}</strong></div>
          </section>
          <section className="admin-card">
            <div className="section-header"><div><h2>👥 Users</h2><p className="section-subtitle">Registered accounts</p></div><button className="backend-button" onClick={loadAdminDashboard}>↻ Refresh</button></div>
            {adminUsers.map((u) => <div className="admin-row" key={u.id}><div><strong>{u.name}</strong><small>{u.email}</small></div><button className="backend-button danger" onClick={() => deleteAdminUser(u.id)}>Delete</button></div>)}
          </section>
          <section className="admin-card">
            <div className="section-header"><div><h2>🕘 Recent Communication</h2><p className="section-subtitle">Platform activity</p></div></div>
            {adminHistory.slice(0,30).map((h) => <div className="admin-row" key={h.id}><div><strong>{h.message}</strong><small>{h.source} • User #{h.user_id} • {h.created_at}</small></div><button className="backend-button danger" onClick={() => deleteAdminHistory(h.id)}>Delete</button></div>)}
          </section>
          <section className="admin-card">
            <div className="section-header"><div><h2>🚨 Emergency Contacts</h2><p className="section-subtitle">Saved by users</p></div></div>
            {adminContacts.map((c) => <div className="admin-row" key={c.id}><div><strong>{c.name}</strong><small>{c.phone} • User #{c.user_id}</small></div></div>)}
          </section>
        </main>
      </div>
    );
  }

  // ============================================================
  // UI
  // ============================================================

  return (
    <div
      className="app"
      style={{
        fontSize: `${fontScale}em`,
      }}
    >
      {/* ========================================================
          SIDEBAR
      ========================================================= */}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">🤟</div>

          <div>
            <h1>AI Communication</h1>
            <span>Assistant</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(
            ([id, icon, label]) => (
              <button
                key={id}
                className={
                  activePage === id
                    ? "nav-item active"
                    : "nav-item"
                }
                onClick={() => setActivePage(id)}
              >
                <span>{icon}</span>
                {label}
              </button>
            )
          )}
        </nav>

        <div className="sidebar-status">
          <span
            className={
              backendStatus === "Connected"
                ? "status-dot connected"
                : "status-dot"
            }
          />

          <span>
            Backend {backendStatus}
          </span>
        </div>
      </aside>

      {/* ========================================================
          MAIN
      ========================================================= */}

      <main className="main-content">

        {/* ======================================================
            TOP BAR
        ====================================================== */}

        <header className="topbar">
          <div>
            <h2>
              {activePage === "home" &&
                "Communication Dashboard"}

              {activePage === "communication" &&
                "ISL Communication"}

              {activePage === "quick" &&
                "Quick Help - Handicapped Support"}

              {activePage === "conversation" &&
                "Two-Way Conversation"}

              {activePage === "favorites" &&
                "Favorite Messages"}

              {activePage === "history" &&
                "Communication History"}

              {activePage === "emergency" &&
                "Emergency Center"}

              {activePage === "settings" &&
                "Settings"}

              {activePage === "admin" &&
                "Admin Control Center"}
            </h2>

            <p>
              Intelligent communication powered by AI
            </p>
          </div>

          <div className="topbar-actions">
            <div className="language-selector">
              <span>Language</span>

              <select
                value={language}
                onChange={(event) =>
                  setLanguage(event.target.value)
                }
              >
                <option>English</option>
                <option>Hindi</option>
                <option>Marathi</option>
              </select>
            </div>

            <div className="user-menu">
              <div className="user-avatar">
                {(user?.name || "U").charAt(0).toUpperCase()}
              </div>
              <div className="user-info">
                <strong>{user?.name || "User"}</strong>
                <span>{user?.email || ""}</span>
              </div>
              <button className="logout-button" onClick={logout}>
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* ======================================================
            HOME
        ====================================================== */}

        {activePage === "home" && (
          <>
            <section className="hero-card">
              <div>
                <span className="eyebrow">
                  AI COMMUNICATION PLATFORM
                </span>

                <h1>
                  Communicate without barriers.
                </h1>

                <p>
                  Use Indian Sign Language, voice and
                  text together in one intelligent
                  communication assistant.
                </p>

                <button
                  className="primary-button"
                  onClick={() =>
                    setActivePage("communication")
                  }
                >
                  🤟 Start Communication
                </button>
              </div>

              <div className="hero-visual">
                🤟
              </div>
            </section>

            <section className="dashboard-grid">
              <button
                className="feature-card"
                onClick={() =>
                  setActivePage("communication")
                }
              >
                <span>🤟</span>
                <h3>ISL Communication</h3>
                <p>
                  Detect signs using the real ISL model.
                </p>
              </button>

              <button
                className="feature-card"
                onClick={() =>
                  setActivePage("conversation")
                }
              >
                <span>💬</span>
                <h3>Two-Way Conversation</h3>
                <p>
                  Combine sign, voice and text.
                </p>
              </button>

              <button
                className="feature-card"
                onClick={() =>
                  setActivePage("history")
                }
              >
                <span>🕘</span>
                <h3>Communication History</h3>
                <p>
                  Review recent communication.
                </p>
              </button>

              <button
                className="feature-card emergency-feature"
                onClick={() =>
                  setActivePage("emergency")
                }
              >
                <span>🚨</span>
                <h3>Emergency</h3>
                <p>
                  Quickly contact a saved emergency contact.
                </p>
              </button>
            </section>

            <section className="card">
              <div className="section-header">
                <div>
                  <h2>System Overview</h2>
                  <p className="section-subtitle">
                    Current platform status
                  </p>
                </div>
              </div>

              <div className="system-info-grid">
                <div>
                  <span>AI MODEL</span>
                  <strong>Real ISL Model</strong>
                </div>

                <div>
                  <span>COMMAND ENGINE</span>
                  <strong>
                    {lastCommand
                      ? "Active"
                      : "Ready"}
                  </strong>
                </div>

                <div>
                  <span>BACKEND</span>
                  <strong>{backendStatus}</strong>
                </div>

                <div>
                  <span>LANGUAGE</span>
                  <strong>{language}</strong>
                </div>
              </div>
            </section>
          </>
        )}

        {/* ======================================================
            ISL COMMUNICATION
        ====================================================== */}

        {activePage === "communication" && (
          <>
            <section className="card ai-detection-card">
              <div className="section-header">
                <div>
                  <h2>🤟 AI Sign Detection</h2>
                  <p className="section-subtitle">
                    Real ISL model powered sign recognition
                  </p>
                </div>

                <div
                  className={
                    cameraOn
                      ? "live-status active"
                      : "live-status"
                  }
                >
                  <span className="live-dot" />
                  {cameraOn ? "LIVE" : "OFF"}
                </div>
              </div>

              <div className="detection-layout">
                <div className="camera-panel">
                  <div className="camera-panel-header">
                    <span>📷 Camera Preview</span>

                    <span>
                      {cameraOn
                        ? "● Active"
                        : "● Offline"}
                    </span>
                  </div>

                  <div
                    className="camera-container"
                    style={{
                      display: cameraOn
                        ? "block"
                        : "none",
                    }}
                  >
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="camera-video"
                    />

                    <div className="camera-overlay">
                      <div className="camera-status">
                        {signResult ||
                          "Waiting for hand..."}
                      </div>
                    </div>
                  </div>

                  {!cameraOn && (
                    <div className="camera-placeholder">
                      <div className="camera-icon">
                        📷
                      </div>

                      <h3>Camera Ready</h3>

                      <p>
                        Start the camera to begin
                        ISL sign detection.
                      </p>
                    </div>
                  )}
                </div>

                <div className="detection-info">
                  <div className="detection-box">
                    <span className="detection-label">
                      CURRENT DETECTION
                    </span>

                    <div className="detected-sign">
                      {detectedSign ||
                        "Waiting for sign..."}
                    </div>

                    <div className="detection-state">
                      {cameraOn
                        ? "● AI Monitoring"
                        : "● Camera Off"}
                    </div>
                  </div>

                  <div className="confidence-box">
                    <div className="confidence-header">
                      <span>Confidence</span>
                      <strong>
                        {detectedConfidence}%
                      </strong>
                    </div>

                    <div className="confidence-track">
                      <div
                        className="confidence-fill"
                        style={{
                          width: `${Math.min(
                            detectedConfidence,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>

                  {lastCommand && (
                    <div className="command-preview">
                      <span>COMMAND</span>
                      <strong>
                        {lastCommand.command}
                      </strong>

                      <p>
                        {lastCommand.message}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <div className="camera-controls">
                <button
                  className="primary-button"
                  onClick={startCamera}
                  disabled={cameraOn}
                >
                  📷 Start Camera
                </button>

                <button
                  className="backend-button"
                  onClick={stopCamera}
                  disabled={!cameraOn}
                >
                  🛑 Stop Camera
                </button>

                <button
                  className={
                    autoDetect
                      ? "auto-detect-active"
                      : "backend-button"
                  }
                  onClick={toggleAutoDetect}
                >
                  {autoDetect
                    ? "⏹️ Stop Auto Detect"
                    : "▶️ Start Auto Detect"}
                </button>

                <button
                  className="backend-button"
                  onClick={captureAndDetectSign}
                  disabled={!cameraOn}
                >
                  ✋ Detect Sign
                </button>
              </div>
            </section>

            <section className="card">
              <div className="section-header">
                <div>
                  <h2>📝 Communication Sentence</h2>
                  <p className="section-subtitle">
                    Build a sentence from detected signs
                  </p>
                </div>

                <button
                  className={
                    autoRead
                      ? "auto-read-status active"
                      : "auto-read-status"
                  }
                  onClick={() =>
                    setAutoRead((value) => !value)
                  }
                >
                  🔊 Auto Read{" "}
                  {autoRead ? "ON" : "OFF"}
                </button>
              </div>

              <div className="sentence-display">
                {sentence ||
                  "Your detected sentence will appear here..."}
              </div>

              <div className="ai-sentence-card">
                <div className="ai-sentence-header">
                  <span>🤖 AI Generated Sentence</span>
                  <span className="ai-badge">AI</span>
                </div>

                <div className="ai-sentence-text">
                  {sentence || "Waiting for signs..."}
                </div>
              </div>

              <div className="buttons">
                <button
                  className="speak-button"
                  onClick={speakText}
                  disabled={!sentence}
                >
                  🔊 Speak Sentence
                </button>

                <button
                  className="backend-button"
                  onClick={() =>
                    toggleFavorite(sentence)
                  }
                  disabled={!sentence}
                >
                  ⭐ Favorite
                </button>

                <button
                  className="backend-button"
                  onClick={clearSentence}
                >
                  🗑️ Clear
                </button>
              </div>
            </section>

            <section className="card">
              <h2>💬 Text & Voice Communication</h2>

              <textarea
                value={text}
                onChange={(event) =>
                  setText(event.target.value)
                }
                placeholder="Type your message here..."
              />

              <div className="buttons">
                <button
                  className="speech-button"
                  onClick={startSpeechRecognition}
                >
                  {listening
                    ? "🎤 Listening..."
                    : "🎤 Voice → Text"}
                </button>

                <button
                  className="speak-button"
                  onClick={speakText}
                >
                  🔊 Text → Voice
                </button>

                <button
                  className="primary-button"
                  onClick={sendMessageToBackend}
                >
                  📤 Send Message
                </button>
              </div>
            </section>
          </>
        )}

        {/* ======================================================
            TWO WAY CONVERSATION
        ====================================================== */}

        {activePage === "conversation" && (
          <section className="card conversation-card">
            <div className="section-header">
              <div>
                <h2>💬 Two-Way Conversation Mode</h2>
                <p className="section-subtitle">
                  One screen for both people
                </p>
              </div>

              <button
                className={
                  conversationMode
                    ? "auto-detect-active"
                    : "backend-button"
                }
                onClick={() =>
                  setConversationMode(
                    (value) => !value
                  )
                }
              >
                {conversationMode
                  ? "● Conversation ON"
                  : "○ Conversation OFF"}
              </button>
            </div>

            <div className="conversation-grid">
              <div className="conversation-person">
                <span>🤟</span>
                <h3>ISL User</h3>

                <div className="conversation-message">
                  {sentence ||
                    "Detected sign message will appear here."}
                </div>

                <button
                  className="speak-button"
                  onClick={() =>
                    speakTextValue(sentence)
                  }
                >
                  🔊 Speak
                </button>
              </div>

              <div className="conversation-person">
                <span>🗣️</span>
                <h3>Speaking User</h3>

                <textarea
                  value={text}
                  onChange={(event) =>
                    setText(event.target.value)
                  }
                  placeholder="Type or use voice..."
                />

                <div className="buttons">
                  <button
                    className="speech-button"
                    onClick={startSpeechRecognition}
                  >
                    🎤 Voice
                  </button>

                  <button
                    className="speak-button"
                    onClick={speakText}
                  >
                    🔊 Speak
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ======================================================
            FAVORITES
        ====================================================== */}

        {activePage === "favorites" && (
          <section className="card">
            <div className="section-header">
              <div>
                <h2>⭐ Favorite Messages</h2>
                <p className="section-subtitle">
                  Frequently used communication
                </p>
              </div>
            </div>

            {favorites.length === 0 ? (
              <div className="empty-state">
                ⭐
                <p>
                  No favorite messages yet.
                </p>
              </div>
            ) : (
              <div className="favorite-list">
                {favorites.map((item) => (
                  <div
                    className="favorite-row"
                    key={item}
                  >
                    <span>{item}</span>

                    <div className="buttons">
                      <button
                        className="speak-button"
                        onClick={() =>
                          speakTextValue(item)
                        }
                      >
                        🔊 Speak
                      </button>

                      <button
                        className="backend-button"
                        onClick={() =>
                          setText(item)
                        }
                      >
                        Use
                      </button>

                      <button
                        className="backend-button"
                        onClick={() =>
                          toggleFavorite(item)
                        }
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* ======================================================
            HISTORY
        ====================================================== */}

        {activePage === "history" && (
          <section className="card">
            <div className="section-header">
              <div>
                <h2>🕘 Communication History</h2>
                <p className="section-subtitle">
                  Recent signs, voice and text messages
                </p>
              </div>

              <button
                className="backend-button"
                onClick={async () => {
                  setHistory([]);
                  try {
                    await authFetch("/api/user/history", {
                      method: "DELETE",
                    });
                  } catch (error) {
                    console.error("Clear history error:", error);
                  }
                }}
              >
                Clear History
              </button>
            </div>

            {history.length === 0 ? (
              <div className="empty-state">
                🕘
                <p>No communication history yet.</p>
              </div>
            ) : (
              <div className="history-list">
                {history.map((item) => (
                  <div
                    className="history-row"
                    key={item.id}
                  >
                    <span>{item.type}</span>

                    <strong>{item.value}</strong>

                    <small>{item.time}</small>

                    <button
                      className="speak-button"
                      onClick={() =>
                        speakTextValue(item.value)
                      }
                    >
                      🔊
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* ======================================================
            EMERGENCY
        ====================================================== */}

        {activePage === "emergency" && (
          <>
            <section className="card emergency emergency-center">
              <div className="emergency-header">
                <div>
                  <h2>🚨 Emergency Center</h2>
                  <p>
                    Double-tap the emergency button
                    to open the SMS workflow for your
                    first saved emergency contact.
                  </p>
                </div>

                <span>SAFETY</span>
              </div>

              <button
                className={
                  emergencyTap
                    ? "emergency-button triggered"
                    : "emergency-button"
                }
                onClick={emergencyDoubleTap}
              >
                🚨
                <strong>
                  {emergencyTap
                    ? "Emergency Activated"
                    : "DOUBLE TAP"}
                </strong>
                <small>
                  Double tap to send emergency message
                </small>
              </button>

              <textarea
                value={emergencyMessage}
                onChange={(event) =>
                  setEmergencyMessage(
                    event.target.value
                  )
                }
                placeholder="Emergency message..."
              />
            </section>

            <section className="card">
              <h2>📞 Emergency Contacts</h2>

              <div className="buttons">
                <button
                  className="primary-button"
                  onClick={addEmergencyContact}
                >
                  ➕ Add Contact
                </button>
              </div>

              {emergencyContacts.map(
                (contact) => (
                  <div
                    className="history-row"
                    key={contact}
                  >
                    <strong>{contact}</strong>

                    <button
                      className="backend-button"
                      onClick={() =>
                        removeEmergencyContact(
                          contact
                        )
                      }
                    >
                      Remove
                    </button>
                  </div>
                )
              )}
            </section>

            <section className="card">
              <h2>Quick Emergency Messages</h2>

              <div className="emergency-grid">
                {EMERGENCY_MESSAGES.map(
                  (message) => (
                    <button
                      key={message}
                      onClick={() =>
                        setEmergencyMessage(
                          message
                        )
                      }
                    >
                      {message}
                    </button>
                  )
                )}
              </div>
            </section>
          </>
        )}

        {/* ======================================================
            SETTINGS
        ====================================================== */}

        {activePage === "settings" && (
          <>
            <section className="card">
              <h2>⚙️ Communication Settings</h2>

              <div className="settings-row">
                <div>
                  <strong>Language</strong>
                  <p>
                    Select the communication language.
                  </p>
                </div>

                <select
                  value={language}
                  onChange={(event) =>
                    setLanguage(event.target.value)
                  }
                >
                  <option>English</option>
                  <option>Hindi</option>
                  <option>Marathi</option>
                </select>
              </div>

              <div className="settings-row">
                <div>
                  <strong>Auto Read</strong>
                  <p>
                    Automatically speak detected
                    sentences.
                  </p>
                </div>

                <button
                  className="backend-button"
                  onClick={() =>
                    setAutoRead(
                      (value) => !value
                    )
                  }
                >
                  {autoRead ? "ON" : "OFF"}
                </button>
              </div>

              <div className="settings-row">
                <div>
                  <strong>Accessibility Text Size</strong>
                  <p>
                    Increase interface text size.
                  </p>
                </div>

                <div className="buttons">
                  <button
                    className="backend-button"
                    onClick={() =>
                      setFontScale(
                        Math.max(
                          0.9,
                          fontScale - 0.1
                        )
                      )
                    }
                  >
                    A-
                  </button>

                  <button
                    className="backend-button"
                    onClick={() =>
                      setFontScale(
                        Math.min(
                          1.5,
                          fontScale + 0.1
                        )
                      )
                    }
                  >
                    A+
                  </button>
                </div>
              </div>
            </section>

            <section className="card">
              <h2>🚨 Emergency Settings</h2>

              <div className="settings-row">
                <div>
                  <strong>
                    Optional Location Sharing
                  </strong>

                  <p>
                    Location sharing is disabled by
                    default. Enable only when you want
                    to use location with emergency
                    workflows.
                  </p>
                </div>

                <button
                  className="backend-button"
                  onClick={() =>
                    setLocationEnabled(
                      (value) => !value
                    )
                  }
                >
                  {locationEnabled
                    ? "Enabled"
                    : "Disabled"}
                </button>
              </div>

              <div className="settings-row">
                <div>
                  <strong>
                    Saved Contacts
                  </strong>

                  <p>
                    {emergencyContacts.length} contact(s)
                    saved.
                  </p>
                </div>

                <button
                  className="primary-button"
                  onClick={addEmergencyContact}
                >
                  Add Contact
                </button>
              </div>
            </section>

            <section className="card">
              <h2>🔧 System Information</h2>

              <div className="system-info-grid">
                <div>
                  <span>BACKEND</span>
                  <strong>{backendStatus}</strong>
                </div>

                <div>
                  <span>MODEL</span>
                  <strong>Real ISL Model</strong>
                </div>

                <div>
                  <span>COMMANDS</span>
                  <strong>40</strong>
                </div>

                <div>
                  <span>CAMERA</span>
                  <strong>
                    {cameraOn ? "ON" : "OFF"}
                  </strong>
                </div>
              </div>
            </section>
          </>
        )}

        {/* ======================================================
            QUICK FEATURES (Handicapped Persons)
        ====================================================== */}

        {activePage === "quick" && (
          <QuickFeatures
            onSendMessage={(msg) => {
              setText(msg);
              addHistory("QUICK", msg);
            }}
            onSpeak={speakTextValue}
            emergencyContacts={emergencyContacts}
          />
        )}

        {/* ======================================================
            FOOTER
        ====================================================== */}

        <footer className="footer">
          <strong>
            AI Communication Assistant
          </strong>

          <span>
            Intelligent Sign Language Communication
            Platform
          </span>
        </footer>
      </main>
    </div>
  );
}

export default App;
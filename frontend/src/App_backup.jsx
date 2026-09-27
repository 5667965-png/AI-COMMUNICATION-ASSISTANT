import { useEffect, useState, useRef } from "react";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [signResult, setSignResult] = useState("");
  const [sentence, setSentence] = useState("");
  const [listening, setListening] = useState(false);
  const videoRef = useRef(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [autoDetect, setAutoDetect] = useState(false);
  const lastDetectedSign = useRef("");
  const signCount = useRef(0);
  const committedSign = useRef("");
  const noHandCount = useRef(0);
  const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: true,
    });

    videoRef.current.srcObject = stream;
    setCameraOn(true);
    setSignResult("Camera started. Show a hand sign.");
  } catch (error) {
    console.error("Camera error:", error);
    alert("Could not access camera.");
  }
};
const stopCamera = () => {
  if (videoRef.current && videoRef.current.srcObject) {
    const tracks = videoRef.current.srcObject.getTracks();

    tracks.forEach((track) => track.stop());

    videoRef.current.srcObject = null;
  }
  setAutoDetect(false);
  setCameraOn(false);
  setSignResult("Camera stopped.");
};
const toggleAutoDetect = () => {
  setAutoDetect((previous) => !previous);
};
const captureAndDetectSign = async () => {
  if (!videoRef.current) {
    return;
  }

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

  canvas.toBlob(async (blob) => {
    const formData = new FormData();

    formData.append("file", blob, "camera.jpg");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/sign-camera",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      console.log("Camera sign response:", data);
      setSignResult(data.message);
      
if (data.sign === "No hand detected") {
  noHandCount.current += 1;
  signCount.current = 0;
  setSignResult("🔴 No hand detected");


  if (noHandCount.current >= 4) {
    lastDetectedSign.current = "";
    committedSign.current = "";
  }

  return;
}

noHandCount.current = 0;

let detectedWord = "";

if (data.sign === "1 Finger(s)") {
  detectedWord = "Hello";
} else if (data.sign === "2 Finger(s)") {
  detectedWord = "Yes";
} else if (data.sign === "3 Finger(s)") {
  detectedWord = "Help";
} else if (data.sign === "Fist") {
  detectedWord = "Stop";
} else if (data.sign === "Open Hand") {
  detectedWord = "Thank you";
} else {
  detectedWord = data.sign;
}
if (lastDetectedSign.current === data.sign) {
  signCount.current += 1;
} else {
  lastDetectedSign.current = data.sign;
  signCount.current = 1;
}

if (signCount.current < 5) {
  return;
}

if (committedSign.current === data.sign) {
  return;
}

committedSign.current = data.sign;
signCount.current = 0;

setText(detectedWord);

setSentence((previousSentence) => {
  if (!previousSentence) {
    return detectedWord;
  }

  return previousSentence + " " + detectedWord;
});
  
    } catch (error) {
      console.error("Camera sign error:", error);
      setSignResult("Could not connect to backend.");
    }
  }, "image/jpeg");
};
    const [backendStatus, setBackendStatus] = useState("Checking...");
    const [backendResponse, setBackendResponse] = useState("");
            useEffect(() => {
  fetch("http://127.0.0.1:8000/api/health")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Backend request failed");
      }

      return response.json();
    })
    .then((data) => {
      if (data.status === "ok") {
        setBackendStatus("Connected");
      } else {
        setBackendStatus("Backend Error");
      }
    })
    .catch((error) => {
      console.error("Backend connection error:", error);
      setBackendStatus("Disconnected");
    });
}, []);
useEffect(() => {
  if (!autoDetect || !cameraOn) {
    return;
  }

  const interval = setInterval(() => {
    captureAndDetectSign();
  }, 2000);

  return () => {
    clearInterval(interval);
  };
}, [autoDetect, cameraOn]);
  // Speech to Text
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

    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setListening(true);
    };

    recognition.onresult = (event) => {
      const result =
        event.results[0][0].transcript;

      setText(result);
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

      // Send message to Backend
  const sendMessageToBackend = async () => {
    if (!text.trim()) {
      alert("Please enter a message.");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/message",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: text,
          }),
        }
      );

      const data = await response.json();

      console.log("Backend response:", data);
      setBackendResponse(data.message);
    } catch (error) {
      console.error("Backend error:", error);
      alert("Could not connect to backend.");
    }
  };
         // Send sign to Backend
  const sendSignToBackend = async (sign) => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/sign",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ sign: sign }),
        }
      );

      const data = await response.json();

      console.log("Camera Sign response:", data);
      setSignResult(data.message);
      
    } catch (error) {
      console.error("Sign backend error:", error);
      setSignResult("Could not connect to backend.");
    }
  };
  // Text to Speech
  const speakText = () => {
    if (!text.trim()) {
      alert("Please enter a message.");
      return;
    }

    const speech = new SpeechSynthesisUtterance(sentence || text);

    speech.lang = "en-US";
    speech.rate = 0.9;
    speech.pitch = 1;

    window.speechSynthesis.speak(speech);
  };


  // Emergency message
  const setEmergencyMessage = (message) => {
    setText(message);
  };


  return (
    <div className="app">
<div className="backend-status">
  Backend: {backendStatus}
</div>
      {/* Header */}
      <header className="header">
        <h1>AI Communication Assistant</h1>

        <p>
          Communication support for people
          with hearing and speech disabilities
        </p>
      </header>


      {/* Main */}
      <main className="container">

        {/* Communication Card */}
        <section className="card">

          <h2>💬 Communication</h2>

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
                : "🎤 Speech → Text"}
            </button>


            <button
              className="speak-button"
              onClick={speakText}
            >
              🔊 Text → Speech
            </button>
            <button
  className="speak-button"
  onClick={() => {
    if (!sentence.trim()) {
      alert("No sentence available.");
      return;
    }

    const speech = new SpeechSynthesisUtterance(sentence);
    speech.lang = "en-US";
    speech.rate = 0.9;
    speech.pitch = 1;

    window.speechSynthesis.speak(speech);
  }}
>
  🗣️ Speak Sentence
</button>
<button
  className="backend-button"
  onClick={sendMessageToBackend}
>
  📤 Send to Backend
</button>
<button
  className="backend-button"
  onClick={() => sendSignToBackend("Open Hand")}
>
  ✋ Test Open Hand Sign
</button>
<button
  className="backend-button"
  onClick={startCamera}
  >

  
  📷 Start Camera
  </button>
  <button className="backend-button" onClick={stopCamera}>
  🛑 Stop Camera
</button>
<button
  className="backend-button"
  onClick={toggleAutoDetect}
>
  {autoDetect ? "⏹️ Stop Auto Detect" : "▶️ Start Auto Detect"}
</button>

  <button
  className="backend-button"
  onClick={captureAndDetectSign}
>
  ✋ Detect Sign

</button>
<button
  className="backend-button"
  onClick={speakText}
>
  🔊 Speak Detected Sentence
</button>
<button
  className="backend-button"
  onClick={() => {
    setSentence("");
    setText("");
    setSignResult("");
    lastDetectedSign.current = "";
    signCount.current = 0;
committedSign.current = "";
noHandCount.current = 0;
  }}
>
  🗑️ Clear Sentence
</button>
          </div>
          {backendResponse && (
  <div className="backend-response">
    Backend Response: {backendResponse}
  </div>
)}
{signResult && (
  <div className="backend-response">
    Sign Result: {signResult}
  </div>
)}
{sentence && (
  <div className="backend-response">
    Sentence: {sentence}
  </div>
)}
<div
  className="camera-container"
  style={{ display: cameraOn ? "block" : "none" }}
>
  <video
    ref={videoRef}
    autoPlay
    playsInline
    className="camera-video"
  />
  <div className="camera-overlay">
    <div className="camera-status">
      {signResult || "Waiting for hand..."}
    </div>
  </div>
</div>

        </section>


        {/* Emergency Card */}
        <section className="card emergency">

          <h2>🚨 Emergency Messages</h2>

          <div className="emergency-grid">

            <button
              onClick={() =>
                setEmergencyMessage(
                  "I need help."
                )
              }
            >
              🆘 I Need Help
            </button>


            <button
              onClick={() =>
                setEmergencyMessage(
                  "Please call my family."
                )
              }
            >
              👨‍👩‍👧 Call Family
            </button>


            <button
              onClick={() =>
                setEmergencyMessage(
                  "Please call an ambulance."
                )
              }
            >
              🚑 Ambulance
            </button>


            <button
              onClick={() =>
                setEmergencyMessage(
                  "Please take me to a hospital."
                )
              }
            >
              🏥 Hospital
            </button>

          </div>

        </section>

      </main>

    </div>
  );
}

export default App;
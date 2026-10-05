import { useState } from "react";

const QUICK_MESSAGES = [
  { id: 1, icon: "🍽️", label: "Food", message: "I want to eat food." },
  { id: 2, icon: "💧", label: "Water", message: "I want to drink water." },
  { id: 3, icon: "💊", label: "Medicine", message: "I need my medicine." },
  { id: 4, icon: "🚽", label: "Bathroom", message: "I need to go to the bathroom." },
  { id: 5, icon: "🛌", label: "Rest", message: "I want to rest." },
  { id: 6, icon: "🆘", label: "Help", message: "I need help immediately!" },
  { id: 7, icon: "👨‍⚕️", label: "Doctor", message: "Please call a doctor." },
  { id: 8, icon: "👨‍👩‍👧", label: "Family", message: "Please call my family." },
];

const EMERGENCY_MESSAGES = [
  "I need help.",
  "Please call my family.",
  "Please call an ambulance.",
  "Please take me to a hospital.",
];

export default function QuickFeatures({ onSendMessage, onSpeak, emergencyContacts }) {
  const [showMedical, setShowMedical] = useState(false);
  const [medicalInfo, setMedicalInfo] = useState({
    bloodGroup: "",
    allergies: "",
    medicines: "",
    doctorName: "",
    doctorPhone: "",
  });

  const handleQuickMessage = (message) => {
    onSendMessage(message);
    onSpeak(message);
  };

  const handleEmergency = () => {
    const message = "EMERGENCY! I need help immediately!";
    onSendMessage(message);
    onSpeak(message);

    if (emergencyContacts && emergencyContacts.length > 0) {
      const phone = emergencyContacts[0].phone || emergencyContacts[0];
      const body = encodeURIComponent(message);
      window.location.href = `sms:${phone}?body=${body}`;
    }
  };

  const handleSendAllEmergency = () => {
    EMERGENCY_MESSAGES.forEach((msg, index) => {
      setTimeout(() => {
        onSendMessage(msg);
        onSpeak(msg);
      }, index * 2000);
    });
  };

  return (
    <div className="quick-features">
      <div className="quick-section">
        <h3>⚡ Quick Messages</h3>
        <div className="quick-grid">
          {QUICK_MESSAGES.map((item) => (
            <button
              key={item.id}
              className="quick-btn"
              onClick={() => handleQuickMessage(item.message)}
            >
              <span className="quick-icon">{item.icon}</span>
              <span className="quick-label">{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="quick-section">
        <h3>🚨 Emergency</h3>
        <div className="emergency-buttons">
          <button className="emergency-btn sos" onClick={handleEmergency}>
            🆘 SOS - Send Location
          </button>
          <button className="emergency-btn" onClick={handleSendAllEmergency}>
            📢 Send All Emergency Messages
          </button>
        </div>
      </div>

      <div className="quick-section">
        <h3>🏥 Medical ID</h3>
        <button
          className="medical-toggle"
          onClick={() => setShowMedical(!showMedical)}
        >
          {showMedical ? "Hide Medical Info" : "Show Medical Info"}
        </button>

        {showMedical && (
          <div className="medical-form">
            <input
              placeholder="Blood Group (e.g., O+)"
              value={medicalInfo.bloodGroup}
              onChange={(e) =>
                setMedicalInfo({ ...medicalInfo, bloodGroup: e.target.value })
              }
            />
            <input
              placeholder="Allergies"
              value={medicalInfo.allergies}
              onChange={(e) =>
                setMedicalInfo({ ...medicalInfo, allergies: e.target.value })
              }
            />
            <input
              placeholder="Medicines"
              value={medicalInfo.medicines}
              onChange={(e) =>
                setMedicalInfo({ ...medicalInfo, medicines: e.target.value })
              }
            />
            <input
              placeholder="Doctor Name"
              value={medicalInfo.doctorName}
              onChange={(e) =>
                setMedicalInfo({ ...medicalInfo, doctorName: e.target.value })
              }
            />
            <input
              placeholder="Doctor Phone"
              value={medicalInfo.doctorPhone}
              onChange={(e) =>
                setMedicalInfo({ ...medicalInfo, doctorPhone: e.target.value })
              }
            />
            <button
              className="save-medical"
              onClick={() => {
                const info = `Medical ID:\nBlood: ${medicalInfo.bloodGroup}\nAllergies: ${medicalInfo.allergies}\nMedicines: ${medicalInfo.medicines}\nDoctor: ${medicalInfo.doctorName} (${medicalInfo.doctorPhone})`;
                onSendMessage(info);
                onSpeak("Medical information saved and sent.");
              }}
            >
              💾 Save & Send Medical Info
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

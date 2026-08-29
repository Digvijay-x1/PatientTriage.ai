import { createContext, useContext, useState, type ReactNode } from "react";

type Language = "en" | "hi";

type LanguageContextType = {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (text: string) => string;
};

const translations: Record<string, string> = {
  // Dashboard
  "Emergency Department Coordination": "आपातकालीन विभाग समन्वय",
  "Overview": "अवलोकन",
  "Needs Attention": "ध्यान देने की आवश्यकता",
  "Waiting Queue": "प्रतीक्षा सूची",
  "In Care": "उपचाराधीन",
  "Audit Trail": "ऑडिट ट्रेल",
  "Emergency Department Overview": "आपातकालीन विभाग का अवलोकन",
  "Focus your attention where it matters most.": "सबसे महत्वपूर्ण मामलों पर ध्यान दें।",
  "Add Patient": "मरीज़ जोड़ें",
  "Re-triage": "पुनः ट्रायेज",
  "Reassessment required": "पुनर्मूल्यांकन आवश्यक",
  "ED Capacity": "ED क्षमता",
  "Current utilization": "वर्तमान उपयोग",
  "Current patients awaiting treatment": "उपचार की प्रतीक्षा कर रहे वर्तमान मरीज़",
  "Patients currently receiving treatment.": "वर्तमान में उपचार प्राप्त कर रहे मरीज़।",
  "No patients currently in care": "वर्तमान में कोई मरीज़ उपचाराधीन नहीं है",
  "Patients will appear here when they are moved into care.": "मरीज़ों को उपचार में भेजे जाने के बाद वे यहाँ दिखाई देंगे।",
  "Clinical decisions, overrides, and re-triage events.": "नैदानिक निर्णय, ओवरराइड और पुनः ट्रायेज घटनाएँ।",
  "No audit events yet": "अभी कोई ऑडिट घटना नहीं है",
  "Clinical actions will appear here.": "नैदानिक कार्रवाइयाँ यहाँ दिखाई देंगी।",

  // Common
  "Patient": "मरीज़",
  "Complaint": "शिकायत",
  "Priority": "प्राथमिकता",
  "Status": "स्थिति",
  "Wait Time": "प्रतीक्षा समय",
  "Arrival": "आगमन",
  "Action": "कार्रवाई",
  "Waiting": "प्रतीक्षा में",
  "Update": "अपडेट",
  "Close": "बंद करें",
  "Cancel": "रद्द करें",
  "Complete": "पूरा करें",
  "Loading...": "लोड हो रहा है...",
  "No": "नहीं",

  // Attention
  "Patients surfaced by the triage system for coordinator review":
    "ट्रायेज सिस्टम द्वारा समन्वयक समीक्षा के लिए चिन्हित मरीज़",
  "No patients need attention": "किसी मरीज़ पर तत्काल ध्यान आवश्यक नहीं है",
  "No active re-triage alerts at the moment.":
    "इस समय कोई सक्रिय पुनः ट्रायेज अलर्ट नहीं है",
  "Reassessment due": "पुनर्मूल्यांकन आवश्यक",
  "Clinical review": "नैदानिक समीक्षा",
  "Patient has reached the scheduled reassessment time.":
    "मरीज़ निर्धारित पुनर्मूल्यांकन समय तक पहुँच गया है।",
  "Patient condition requires reassessment.":
    "मरीज़ की स्थिति के पुनर्मूल्यांकन की आवश्यकता है।",
  "Initial triage assessment requires review.":
    "प्रारंभिक ट्रायेज मूल्यांकन की समीक्षा आवश्यक है।",
  "Patient requires clinical review.": "मरीज़ की नैदानिक समीक्षा आवश्यक है।",
  "min waiting": "मिनट से प्रतीक्षा",
  // Patient intake
  "Capture the information available during the patient's initial arrival.":
    "मरीज़ के प्रारंभिक आगमन के समय उपलब्ध जानकारी दर्ज करें।",
  "Patient Information": "मरीज़ की जानकारी",
  "Patient ID": "मरीज़ ID",
  "Age": "आयु",
  "Sex": "लिंग",
  "Chief Complaint": "मुख्य शिकायत",
  "Initial Vitals": "प्रारंभिक जीवन संकेत",
  "Values available during initial assessment.":
    "प्रारंभिक मूल्यांकन के दौरान उपलब्ध मान।",
  "Heart Rate": "हृदय गति",
  "Systolic BP": "सिस्टोलिक BP",
  "Diastolic BP": "डायस्टोलिक BP",
  "Temperature (°C)": "तापमान (°C)",
  "Initial Observation": "प्रारंभिक अवलोकन",
  "Responsiveness": "प्रतिक्रियाशीलता",
  "Breathing": "श्वसन",
  "Distress Level": "तकलीफ़ का स्तर",
  "Unable to process patient": "मरीज़ की जानकारी संसाधित नहीं हो सकी",
  "Registering and assessing...": "पंजीकरण और मूल्यांकन हो रहा है...",
  "Register Patient & Run Triage": "मरीज़ पंजीकृत करें और ट्रायेज चलाएँ",
  "Triage Assessment Complete": "ट्रायेज मूल्यांकन पूरा हुआ",
  "Patient Assessment": "मरीज़ का मूल्यांकन",
  "AI ESI": "AI ESI",
  "Confidence": "विश्वास स्तर",
  "Confidence Band": "विश्वास श्रेणी",
  "Reasoning": "कारण",
  "No reasoning details were provided.": "कोई कारण विवरण उपलब्ध नहीं है।",
  "Coordinator Review Required": "समन्वयक समीक्षा आवश्यक",
  "The assessment has been automatically escalated for coordinator review.":
    "मूल्यांकन को स्वचालित रूप से समन्वयक समीक्षा के लिए भेजा गया है।",
  "Done": "पूर्ण",

  // Queue / event panel
  "Update Patient": "मरीज़ अपडेट करें",
  "Change ESI": "ESI बदलें",
  "Update Vitals": "वाइटल्स अपडेट करें",
  "Condition Worsened": "स्थिति बिगड़ी",
  "New ESI Level": "नया ESI स्तर",
  "Select ESI level": "ESI स्तर चुनें",
  "Reason (optional)": "कारण (वैकल्पिक)",
  "Why is the ESI level changing?": "ESI स्तर क्यों बदला जा रहा है?",
  "Updated Vitals": "अपडेटेड वाइटल्स",
  "Enter the patient's latest vital signs.": "मरीज़ के नवीनतम जीवन संकेत दर्ज करें।",
  "SPO₂ (%)": "SpO₂ (%)",
  "Condition worsened": "स्थिति बिगड़ी",
  "This runs an urgent re-assessment and flags the patient for immediate review.":
    "यह तत्काल पुनर्मूल्यांकन चलाता है और मरीज़ को तुरंत समीक्षा के लिए चिन्हित करता है।",
  "Describe what changed": "क्या बदलाव हुआ, उसका विवरण दें",
  "Trigger Re-triage": "पुनः ट्रायेज शुरू करें",
  "Running re-triage...": "पुनः ट्रायेज चल रहा है...",
  "AI Recommendation": "AI अनुशंसा",
  "New AI Recommendation": "नई AI अनुशंसा",
  "Vital Change Detected": "वाइटल्स में बदलाव पाया गया",
  "Re-triage reasoning": "पुनः ट्रायेज का कारण",
  "Current Approved ESI": "वर्तमान स्वीकृत ESI",
  "Current priority in the waiting queue": "प्रतीक्षा सूची में वर्तमान प्राथमिकता",
  "Why was this recommended?": "यह क्यों अनुशंसित किया गया?",
  "Coordinator Decision": "समन्वयक निर्णय",
  "Confirm AI Recommendation": "AI अनुशंसा की पुष्टि करें",
  "Override Recommendation": "अनुशंसा बदलें",
  "Take Patient to Care": "मरीज़ को उपचार के लिए भेजें",
  "Moving to care...": "मरीज़ को उपचार के लिए भेजा जा रहा है...",

  "Loading waiting queue...": "प्रतीक्षा सूची लोड हो रही है...",
"Unable to load waiting queue": "प्रतीक्षा सूची लोड नहीं हो सकी",
"No patients currently waiting": "वर्तमान में कोई मरीज़ प्रतीक्षा में नहीं है",
"Patients will appear here after coordinator review.": "समन्वयक की समीक्षा के बाद मरीज़ यहाँ दिखाई देंगे।",

  // Review
  "Coordinator Review": "समन्वयक समीक्षा",
  "Loading patient assessment...": "मरीज़ का मूल्यांकन लोड हो रहा है...",
  "Unable to load assessment": "मूल्यांकन लोड नहीं हो सका",
  "Assessment": "मूल्यांकन",
  "New Vital Check": "नया वाइटल चेक",
  "Enter the patient's latest measurements.":
    "मरीज़ के नवीनतम माप दर्ज करें।",
  "Add Vital Check": "वाइटल चेक जोड़ें",
  "Record new vitals and reassess the patient's condition.":
    "नए वाइटल्स दर्ज करें और मरीज़ की स्थिति का पुनर्मूल्यांकन करें।",
  "Run Re-triage": "पुनः ट्रायेज चलाएँ",
  "The AI recommendation does not change the patient's priority automatically.":
    "AI अनुशंसा मरीज़ की प्राथमिकता को स्वतः नहीं बदलती।",
  "Coordinator confirmed": "समन्वयक ने पुष्टि की",
  "Coordinator override": "समन्वयक ओवरराइड",
  "Re-triage assessment": "पुनः ट्रायेज मूल्यांकन",
  "Patient taken to care": "मरीज़ को उपचार के लिए भेजा गया",
  "Re-triage alert": "पुनः ट्रायेज अलर्ट",

  // ESI
  "ESI-1 · Resuscitation": "ESI-1 · पुनर्जीवन",
  "ESI-2 · Emergent": "ESI-2 · आपातकालीन",
  "ESI-3 · Urgent": "ESI-3 · अत्यावश्यक",
  "ESI-4 · Less urgent": "ESI-4 · कम अत्यावश्यक",
  "ESI-5 · Non-urgent": "ESI-5 · गैर-अत्यावश्यक",

  "female": "महिला",
"male": "पुरुष",

"alert": "सचेत",
"confused": "भ्रमित",
"unresponsive": "प्रतिक्रियाहीन",

"normal": "सामान्य",
"labored": "कठिन",
"absent": "अनुपस्थित",

"none": "कोई नहीं",
"mild": "हल्का",
"moderate": "मध्यम",
"severe": "गंभीर",

"high": "उच्च",
"medium": "मध्यम",
"low": "कम",


"Describe the deterioration in the patient's condition...": "मरीज़ की स्थिति में हुए बदलाव का विवरण दें...",

"confidence": "विश्वास",
"Coordinator Assessment": "समन्वयक मूल्यांकन",
"Select the ESI level you believe is appropriate for this patient.": "इस मरीज़ के लिए आपको जो ESI स्तर उचित लगता है, उसे चुनें।",
"Under-triage detected": "अंडर-ट्रायेज पाया गया",
"Over-triage detected": "ओवर-ट्रायेज पाया गया",
"Triage aligned": "ट्रायेज मेल खाता है",
"AI recommendation": "AI अनुशंसा",
"Coordinator assessment": "समन्वयक मूल्यांकन",
"Recommended: take patient to care immediately": "अनुशंसा: मरीज़ को तुरंत उपचार के लिए भेजें",
"This case is flagged for urgent coordinator review": "यह मामला तत्काल समन्वयक समीक्षा के लिए चिन्हित किया गया है",
"This assessment now appears in Needs Attention awaiting coordinator confirmation.": "यह मूल्यांकन अब समन्वयक की पुष्टि के लिए ध्यान देने योग्य मामलों में दिखाई देता है।",
"Submitting...": "जमा किया जा रहा है...",


"Override AI Recommendation": "AI अनुशंसा को बदलें",
"Select the coordinator's final ESI level and record why the recommendation was overridden.":
  "समन्वयक का अंतिम ESI स्तर चुनें और अनुशंसा बदलने का कारण दर्ज करें।",
"Final ESI Level": "अंतिम ESI स्तर",
"Reason for Override": "बदलाव का कारण",
"Explain the clinical reason for overriding the recommendation...":
  "अनुशंसा बदलने का चिकित्सीय कारण बताएं...",

"Save Override": "बदलाव सहेजें",
"Confirmed": "पुष्टि की गई",
"Selected": "चयनित",
"Coordinator confirmed the AI recommendation.":
  "समन्वयक ने AI अनुशंसा की पुष्टि की।",
"Coordinator overrode the AI recommendation.":
  "समन्वयक ने AI अनुशंसा को बदला।",
"Override Reason": "बदलाव का कारण",
"Patient ready for care": "मरीज़ उपचार के लिए तैयार है",
"Mark this patient as having entered active care.":
  "इस मरीज़ को सक्रिय उपचार में भेजा गया के रूप में चिह्नित करें।",
"Updating...": "अपडेट हो रहा है...",


"EMERGENCY DEPARTMENT COORDINATION":
  "आपातकालीन विभाग समन्वय",

"ED Live":
  "ED लाइव",
};

const LanguageContext = createContext<LanguageContextType | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");

  const t = (text: string) => {
    if (language === "en") return text;
    return translations[text] ?? text;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);

  if (!context) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }

  return context;
}
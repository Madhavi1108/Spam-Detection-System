import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState("");
  const [suggestion, setSuggestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [type, setType] = useState("message");
  const [darkMode, setDarkMode] = useState(false);

  const handlePredict = async () => {
    if (!text) return;

    try {
      setLoading(true);
      const res = await axios.post(import.meta.env.VITE_API_URL, {
        text: text,
        type: type,
      });
      console.log(res.data);

      setResult(res.data.prediction);
      setSuggestion(res.data.suggestion);
    } catch (error) {
      setResult("Error");
    } finally {
      setLoading(false);
    }
  };

  const getColor = () => {
    if (result === "ham") return "text-green-600";
    if (result === "spam") return "text-red-600";
    if (result === "smishing") return "text-orange-500";
    return "text-gray-600";
  };

  const getBg = () => {
    if (result === "ham") return "bg-[#81912F]/25 backdrop-blur-md border border-white/30";
    if (result === "spam") return "bg-red-400/20 backdrop-blur-md border border-white/30";
    if (result === "smishing") return "bg-orange-400/20 backdrop-blur-md border border-white/30";
    return "bg-white/20 backdrop-blur-md border border-white/30";
  };

  return (
    


    <div className={`min-h-screen flex items-center justify-center px-4 transition-all duration-500 ${ darkMode
      ? "bg-gradient-to-br from-gray-900 via-gray-800 to-black"
      : "bg-gradient-to-br from-blue-500 via-pink-300 to-cyan-600"
      }`} >

    <div className="absolute top-4 right-4">
      <button onClick={() => setDarkMode(!darkMode)} className={`px-4 py-2 rounded-xl font-semibold transition-all duration-300 ${
      darkMode
        ? "bg-yellow-400 text-black hover:bg-yellow-300"
        : "bg-gray-800 text-white hover:bg-gray-700"
        }`} >
        {darkMode ? "☀️ Light" : "🌙 Dark"} </button>
    </div>


     <div className={`w-full max-w-lg backdrop-blur-xl border rounded-3xl shadow-2xl p-6 sm:p-8 text-center transition-all duration-500 ${
    darkMode
      ? "bg-gray-900/40 border-gray-600"
      : "bg-white/20 border-white/20"
    }`} >
     
     <div className={`w-full max-w-md rounded-2xl shadow-3xl p-6 sm:p-8 text-center mx-auto transition-all duration-500 ${
    darkMode
      ? "bg-gray-800/70 text-white"
      : "bg-[#FAF1E6]/35 text-black" }`} >
        
        <h1 className={`text-3xl font-bold mb-2 ${
        darkMode ? "text-white" : "text-black" }`} >
          📩 Spam Detector
        </h1>


       <p className={`font-semibold text-sm mb-4 ${
        darkMode ? "text-gray-300" : "text-gray-700"
        }`} >
        Analyze messages & emails instantly
        </p>
       
        <div className="flex mb-4 bg-gray-100  rounded-xl overflow-hidden ">
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
             className={`w-full p-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
               darkMode ? "bg-gray-700 text-white" : "bg-white text-black"
             }`}
            >
            <option value="message">Message</option>
            <option value="email">Email</option>
          </select>
        </div>

      
        <textarea
          className={`w-full border border-gray-300 p-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none text-sm sm:text-base transition mt-4 ${
            darkMode ? "bg-gray-700 text-white" : "bg-white text-black"
          }`}
          rows="4"
          placeholder={
            type === "message"
              ? "Type your message..."
              : "Paste your email content..."
          }
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

     
        <button
          onClick={handlePredict}
          className="mt-4 w-full py-3 rounded-xl font-medium bg-indigo-500 text-white hover:bg-indigo-600 active:scale-95 transition-all"
        >
          {loading ? "Analyzing..." : `Analyze ${type}`}
        </button>

        
        {result && (
          <div className="mt-3 border border-gray-300 rounded-xl p-2"> 
          <div
            className={`p-4 rounded-xl font-semibold transition-all duration-300 ${getBg()} ${getColor()}`}
          >
            {result === "ham" && "✅ Safe Message"}
            {result === "spam" && "❌ Spam Detected"}
            {result === "smishing" && "⚠️ Fraud Alert"}
            {result === "Error" && "⚠️ Something went wrong"}
          </div>
          </div>
        )}
        {suggestion && (
          <div className="mt-4 p-4 rounded-lg bg-blue-100">
            <h3 className="font-bold text-lg">
              🤖 AI Suggestion
            </h3>

            <p>{suggestion}</p>
          </div>
        )}
        <button onClick={() => {
        setText("");
        setResult("");
        setType("message");
        }} className="mt-3 w-full py-3 rounded-xl font-medium bg-gray-500 text-white hover:bg-gray-600 transition-all" >
        Reset
        </button>
      </div>

    </div>
    </div>
  );
}

export default App;

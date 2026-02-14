import React from "react";
import UploadForm from "./components/UploadForm";
import "./App.css";

function App() {
  return (
    <div className="app-container">
      <div className="app-card">
        <h1>Social Media Privacy Audit Tool</h1>
        <p className="subtitle">
          Upload an image and optional caption. The app will analyze the image
          and show privacy risks.
        </p>
        <UploadForm />
      </div>
    </div>
  );
}

export default App;

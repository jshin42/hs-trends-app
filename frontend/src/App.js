import React from "react";
import "./App.css";
import SchoolGraph from "./components/SchoolGraph";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>HS Trends App</h1>
      </header>
      <main>
        <SchoolGraph apiUrl="http://localhost:8000/api" />
      </main>
    </div>
  );
}

export default App;

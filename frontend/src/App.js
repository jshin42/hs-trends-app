import React, { useEffect } from "react";
import "./App.css";
import SchoolGraph from "./components/SchoolGraph";

function App() {
  useEffect(() => {
    console.log("Environment:", process.env.NODE_ENV);
    console.log("All env variables:", process.env);
    console.log(
      "Google Maps API Key:",
      process.env.REACT_APP_GOOGLE_MAPS_API_KEY
    );
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>HS Trends App</h1>
      </header>
      <main>
        <SchoolGraph
          apiUrl="http://localhost:8000/api"
          googleMapsApiKey="AIzaSyCs9saJGleZsQVVJFBhrDr-B8QMxDi_RH8"
        />
      </main>
    </div>
  );
}

export default App;

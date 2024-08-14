import React, { createContext, useState } from "react";

export const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [schoolData, setSchoolData] = useState([]);
  // Add other state variables as needed

  return (
    <AppContext.Provider value={{ schoolData, setSchoolData }}>
      {children}
    </AppContext.Provider>
  );
};

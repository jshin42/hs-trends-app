import React from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import SchoolGraph from "./SchoolGraph";
import { AppContext } from "../AppContext";

const theme = createTheme();

// Mock data for the AppContext
const mockContextValue = {
  schoolData: [
    { year: 2020, rank: 10 },
    { year: 2021, rank: 8 },
    { year: 2022, rank: 12 },
    // Add more mock data as needed
  ],
  setSchoolData: () => {},
};

export default {
  title: "Components/SchoolGraph",
  component: SchoolGraph,
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <AppContext.Provider value={mockContextValue}>
          <Story />
        </AppContext.Provider>
      </ThemeProvider>
    ),
  ],
};

export const Default = () => <SchoolGraph />;

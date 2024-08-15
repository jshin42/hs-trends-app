const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

export const fetchSchoolData = async (schoolId) => {
  const response = await fetch(`${API_URL}/schools/${schoolId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch school data");
  }
  return await response.json();
};

export const searchSchools = async (query) => {
  const response = await fetch(
    `${API_URL}/schools/search?name=${encodeURIComponent(query)}`
  );
  if (!response.ok) {
    throw new Error("Failed to search schools");
  }
  return await response.json();
};

export const fetchSchoolRankings = async (schoolId) => {
  const response = await fetch(`${API_URL}/schools/${schoolId}/rankings`);
  if (!response.ok) {
    throw new Error("Failed to fetch school rankings");
  }
  return await response.json();
};

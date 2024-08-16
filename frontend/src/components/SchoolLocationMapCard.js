import React, { useState, useCallback, useEffect } from "react";
import { Paper, Typography, Box, CircularProgress, Alert } from "@mui/material";
import { GoogleMap, LoadScript, Marker } from "@react-google-maps/api";

const SchoolLocationMapCard = ({ school, googleMapsApiKey }) => {
  console.log(
    "SchoolLocationMapCard received Google Maps API Key:",
    googleMapsApiKey
  );
  const apiKey = googleMapsApiKey || process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
  console.log("SchoolLocationMapCard using Google Maps API Key:", apiKey);
  // ... rest of the component

  const [mapCenter, setMapCenter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const geocodeAddress = useCallback(async () => {
    const address = `${school.address}, ${school.city}, ${school.state}`;
    setLoading(true);
    setError(null);
    try {
      if (!apiKey) {
        console.error("Google Maps API key is missing or undefined");
        throw new Error("Google Maps API key is missing or undefined");
      }
      const response = await fetch(
        `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(
          address
        )}&key=${apiKey}`
      );
      const data = await response.json();
      if (data.status === "OK" && data.results && data.results.length > 0) {
        const { lat, lng } = data.results[0].geometry.location;
        setMapCenter({ lat, lng });
      } else {
        throw new Error(data.error_message || "Unable to geocode address");
      }
    } catch (err) {
      console.error("Geocoding error:", err);
      setError(`Failed to load map location: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [school, apiKey]);

  useEffect(() => {
    geocodeAddress();
  }, [geocodeAddress]);

  const mapStyles = {
    height: "300px",
    width: "100%",
  };

  return (
    <Paper
      elevation={3}
      sx={{
        padding: 2,
        marginBottom: 2,
        borderRadius: "8px",
        overflow: "hidden",
      }}
    >
      <Typography variant="h6" gutterBottom>
        {school.name} Key Takeaways
      </Typography>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: 2,
        }}
      >
        <Box>
          <Typography variant="body1">Address: {school.address}</Typography>
          <Typography variant="body1">City: {school.city}</Typography>
          <Typography variant="body1">State: {school.state}</Typography>
        </Box>
        <Box>
          <Typography variant="body1">District: {school.district}</Typography>
          <Typography variant="body1">Grades: {school.grades}</Typography>
        </Box>
      </Box>
      {loading ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: 300,
          }}
        >
          <CircularProgress />
        </Box>
      ) : error ? (
        <Box
          sx={{
            height: 300,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <Alert severity="error" sx={{ width: "100%" }}>
            {error}
          </Alert>
        </Box>
      ) : (
        <LoadScript googleMapsApiKey={apiKey}>
          <GoogleMap mapContainerStyle={mapStyles} zoom={15} center={mapCenter}>
            {mapCenter && <Marker position={mapCenter} />}
          </GoogleMap>
        </LoadScript>
      )}
    </Paper>
  );
};

export default React.memo(SchoolLocationMapCard);

import React, { useState, useEffect, useCallback } from "react";
import { Autocomplete, TextField, CircularProgress } from "@mui/material";
import { debounce } from "lodash";

const SearchableDropdown = ({ apiUrl, onSchoolSelect }) => {
  const [inputValue, setInputValue] = useState("");
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchSchoolOptions = useCallback(
    async (searchTerm) => {
      setLoading(true);
      try {
        const response = await fetch(
          `${apiUrl}/schools/search?name=${encodeURIComponent(searchTerm)}`
        );
        if (!response.ok) throw new Error("Failed to fetch school options");
        const data = await response.json();
        setOptions(data);
      } catch (error) {
        console.error("Error fetching school options:", error);
        setOptions([]);
      } finally {
        setLoading(false);
      }
    },
    [apiUrl]
  );

  const debouncedFetchSchoolOptions = useCallback(
    debounce(fetchSchoolOptions, 300),
    [fetchSchoolOptions]
  );

  useEffect(() => {
    if (inputValue) {
      debouncedFetchSchoolOptions(inputValue);
    } else {
      setOptions([]);
    }
  }, [inputValue, debouncedFetchSchoolOptions]);

  return (
    <Autocomplete
      options={options}
      getOptionLabel={(option) =>
        `${option.name}${
          option.city && option.state
            ? ` - ${option.city}, ${option.state}`
            : ""
        }`
      }
      loading={loading}
      onInputChange={(event, newInputValue) => {
        setInputValue(newInputValue);
      }}
      onChange={(event, newValue) => {
        if (newValue) {
          onSchoolSelect(newValue);
        }
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          label="Search for schools"
          variant="outlined"
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? (
                  <CircularProgress color="inherit" size={20} />
                ) : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      renderOption={(props, option) => (
        <li {...props}>
          <div>
            <div>{option.name}</div>
            {option.city && option.state && (
              <div style={{ fontSize: "0.8em", color: "#666" }}>
                {option.city}, {option.state}
              </div>
            )}
          </div>
        </li>
      )}
    />
  );
};

export default SearchableDropdown;

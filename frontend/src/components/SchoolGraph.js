import React, { useState, useCallback, useMemo, useEffect } from "react";
import {
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  TextField,
  Box,
  Chip,
  CircularProgress,
} from "@mui/material";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import SearchableDropdown from "./SearchableDropdown";
import SchoolLocationMapCard from "./SchoolLocationMapCard";

const SchoolGraph = ({ apiUrl, googleMapsApiKey }) => {
  console.log("SchoolGraph received Google Maps API Key:", googleMapsApiKey);
  // ... rest of the component

  useEffect(() => {
    console.log(
      "SchoolGraph useEffect - Google Maps API Key:",
      googleMapsApiKey
    );
  }, [googleMapsApiKey]);

  const [schoolData, setSchoolData] = useState([]);
  const [selectedSchool, setSelectedSchool] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [orderBy, setOrderBy] = useState("year");
  const [order, setOrder] = useState("asc");
  const [filterText, setFilterText] = useState("");

  const fetchSchoolData = useCallback(
    async (schoolId) => {
      setLoading(true);
      setError(null);
      try {
        const [schoolResponse, rankingsResponse] = await Promise.all([
          fetch(`${apiUrl}/schools/${schoolId}`),
          fetch(`${apiUrl}/schools/${schoolId}/rankings`),
        ]);

        if (!schoolResponse.ok || !rankingsResponse.ok) {
          throw new Error("Failed to fetch school data");
        }

        const schoolDetails = await schoolResponse.json();
        const rankings = await rankingsResponse.json();

        setSelectedSchool(schoolDetails);
        setSchoolData(rankings.sort((a, b) => a.year - b.year));
      } catch (error) {
        console.error("Error fetching school data:", error);
        setError(error.message);
        setSchoolData([]);
      } finally {
        setLoading(false);
      }
    },
    [apiUrl]
  );

  const handleSchoolSelect = useCallback(
    (school) => {
      setSelectedSchool(school);
      fetchSchoolData(school.id);
    },
    [fetchSchoolData]
  );

  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === "asc";
    setOrder(isAsc ? "desc" : "asc");
    setOrderBy(property);
  };

  const sortedData = useMemo(() => {
    const comparator = (a, b) => {
      if (b[orderBy] < a[orderBy]) {
        return order === "asc" ? 1 : -1;
      }
      if (b[orderBy] > a[orderBy]) {
        return order === "asc" ? -1 : 1;
      }
      return 0;
    };
    return [...schoolData].sort(comparator);
  }, [schoolData, order, orderBy]);

  const filteredData = useMemo(() => {
    return sortedData.filter((row) =>
      Object.values(row).some((value) =>
        value?.toString().toLowerCase().includes(filterText.toLowerCase())
      )
    );
  }, [sortedData, filterText]);

  const tableHeaders = [
    "year",
    "national_rank",
    "math_proficiency",
    "reading_proficiency",
    "student_teacher_ratio",
    "college_readiness",
    "college_readiness_index",
    "grades",
    "teachers",
    "students",
    "medal_awarded",
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Paper elevation={3} sx={{ padding: 2, backgroundColor: "white" }}>
          <Typography variant="body2">Year: {label}</Typography>
          {payload.map((entry) => (
            <Typography key={entry.name} variant="body2" color={entry.color}>
              {entry.name}: {entry.value}
            </Typography>
          ))}
        </Paper>
      );
    }
    return null;
  };

  return (
    <Paper
      elevation={3}
      sx={{
        padding: 4,
        marginBottom: 4,
        borderRadius: "8px",
        backgroundColor: "#f7f7f7",
      }}
    >
      <Typography variant="h4" gutterBottom sx={{ color: "#0074E4" }}>
        School National Rank Comparison
      </Typography>
      <SearchableDropdown apiUrl={apiUrl} onSchoolSelect={handleSchoolSelect} />
      {loading && <CircularProgress sx={{ marginTop: 2 }} />}
      {error && <Typography color="error">{error}</Typography>}
      {selectedSchool && schoolData.length > 0 && (
        <>
          <Box sx={{ marginTop: 4, marginBottom: 4 }}>
            <Typography variant="h5" gutterBottom>
              {selectedSchool.name}
            </Typography>
            <Chip
              label={`${selectedSchool.city}, ${selectedSchool.state}`}
              sx={{ marginRight: 1 }}
            />
            <Chip
              label={selectedSchool.district}
              color="primary"
              sx={{ marginRight: 1 }}
            />
            <Chip
              label={`Grades: ${selectedSchool.grades}`}
              color="secondary"
            />
          </Box>
          <SchoolLocationMapCard
            school={selectedSchool}
            googleMapsApiKey={googleMapsApiKey}
          />
          <div style={{ width: "100%", height: 400, marginTop: 20 }}>
            <ResponsiveContainer>
              <LineChart data={schoolData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis
                  dataKey="year"
                  type="number"
                  domain={["dataMin", "dataMax"]}
                  tickCount={13}
                  tick={{ fontSize: 12, fill: "#666" }}
                />
                <YAxis
                  reversed
                  domain={["dataMin", "dataMax"]}
                  tick={{ fontSize: 12, fill: "#666" }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="national_rank"
                  name="National Rank"
                  stroke="#0074E4"
                  strokeWidth={2}
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <TextField
            fullWidth
            margin="normal"
            label="Filter table"
            variant="outlined"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            sx={{
              backgroundColor: "white",
              borderRadius: "8px",
              "& .MuiOutlinedInput-root": {
                "& fieldset": {
                  borderColor: "#ccc",
                },
                "&:hover fieldset": {
                  borderColor: "#0074E4",
                },
                "&.Mui-focused fieldset": {
                  borderColor: "#0074E4",
                },
              },
            }}
          />
          <TableContainer component={Paper} sx={{ marginTop: 3 }}>
            <Table
              aria-label="school data table"
              sx={{
                "& .MuiTableCell-root": {
                  padding: "16px",
                  borderBottom: "1px solid #e0e0e0",
                },
                "& .MuiTableHead-root": {
                  backgroundColor: "#f5f5f5",
                },
                "& .MuiTableSortLabel-root": {
                  color: "#0074E4",
                  "&.Mui-active": {
                    color: "#0059B2",
                  },
                },
              }}
            >
              <TableHead>
                <TableRow>
                  {tableHeaders.map((headCell) => (
                    <TableCell
                      key={headCell}
                      sx={{
                        fontWeight: "bold",
                        color: "#333",
                      }}
                    >
                      <TableSortLabel
                        active={orderBy === headCell}
                        direction={orderBy === headCell ? order : "asc"}
                        onClick={() => handleRequestSort(headCell)}
                      >
                        {headCell.replace("_", " ").toUpperCase()}
                      </TableSortLabel>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredData.map((row) => (
                  <TableRow key={row.year} hover>
                    {tableHeaders.map((header) => (
                      <TableCell key={`${row.year}-${header}`}>
                        {row[header]}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Paper>
  );
};

export default SchoolGraph;

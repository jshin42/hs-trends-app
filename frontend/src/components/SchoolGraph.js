import React, { useState, useCallback, useMemo } from "react";
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
} from "@mui/material";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import SearchableDropdown from "./SearchableDropdown";

const SchoolGraph = ({ apiUrl }) => {
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
        const response = await fetch(`${apiUrl}/schools/${schoolId}/rankings`);
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("No ranking data available for this school");
          }
          throw new Error("Failed to fetch school data");
        }
        const data = await response.json();
        setSchoolData(data.sort((a, b) => a.year - b.year));
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
        value.toString().toLowerCase().includes(filterText.toLowerCase())
      )
    );
  }, [sortedData, filterText]);

  const years = useMemo(() => {
    const currentYear = new Date().getFullYear();
    return Array.from({ length: currentYear - 2011 }, (_, i) => 2012 + i);
  }, []);

  return (
    <Paper elevation={3} sx={{ padding: 3, marginBottom: 3 }}>
      <Typography variant="h4" gutterBottom>
        School National Rank Comparison
      </Typography>
      <SearchableDropdown apiUrl={apiUrl} onSchoolSelect={handleSchoolSelect} />
      {loading && <Typography>Loading...</Typography>}
      {error && <Typography color="error">{error}</Typography>}
      {selectedSchool && schoolData.length > 0 && (
        <>
          <div style={{ width: "100%", height: 400, marginTop: 20 }}>
            <ResponsiveContainer>
              <LineChart data={schoolData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="year"
                  domain={[2012, 2024]}
                  type="number"
                  tickCount={13}
                />
                <YAxis reversed domain={["dataMin", "dataMax"]} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="national_rank"
                  name="National Rank"
                  stroke="#8884d8"
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
          />
          <TableContainer component={Paper} sx={{ marginTop: 3 }}>
            <Table aria-label="school data table">
              <TableHead>
                <TableRow>
                  {[
                    "year",
                    "national_rank",
                    "math_proficiency",
                    "reading_proficiency",
                    "student_teacher_ratio",
                  ].map((headCell) => (
                    <TableCell key={headCell}>
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
                  <TableRow key={row.year}>
                    <TableCell>{row.year}</TableCell>
                    <TableCell>{row.national_rank}</TableCell>
                    <TableCell>{row.math_proficiency}</TableCell>
                    <TableCell>{row.reading_proficiency}</TableCell>
                    <TableCell>{row.student_teacher_ratio}</TableCell>
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

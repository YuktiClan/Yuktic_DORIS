
import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";
function App() {

  const [sro, setSro] = useState("");
  const [locality, setLocality] = useState("");

  const [captchaImage, setCaptchaImage] = useState(null);
  const [captchaValue, setCaptchaValue] = useState("");

  const [records, setRecords] = useState([]);
  const [scraperRunning, setScraperRunning] = useState(false);

  const [status, setStatus] = useState("Select SRO");
  const [sroList, setSroList] = useState([]);
  const [localityList, setLocalityList] = useState([]);

  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");

  const [firstPartySearch, setFirstPartySearch] = useState("");
  const [secondPartySearch, setSecondPartySearch] = useState("");

  const [addressSearch, setAddressSearch] = useState("");
  const [pincodeSearch, setPincodeSearch] = useState("");

  const [minArea, setMinArea] = useState("");
  const [maxArea, setMaxArea] = useState("");
  const [monthFrom, setMonthFrom] = useState("");
  const [monthTo, setMonthTo] = useState("");

  const [showFilters, setShowFilters] = useState(false);

  const [propertyType, setPropertyType] = useState("");

  const [captchaLoaded, setCaptchaLoaded] = useState(false);

  useEffect(() => {
  if (!Array.isArray(records)) {
    console.log("⚠️ FIXING INVALID RECORDS:", records);
    setRecords([]);
  }
}, [records]);

  const startScraper = async () => {

    if (!sro || !locality) {
      alert("Please select SRO and Locality");
      return;
    }

    try {

      setStatus("Starting scraper...");

      const res = await axios.post(
        "http://localhost:8000/start-scraper",
        {
          sro_name: sro,
          locality_name: locality
        }
      );

      setStatus(res.data.status);
      setScraperRunning(true);



    } catch (err) {
      console.log(err);
    }

  };





  const submitCaptcha = async () => {

    try {

      await axios.post(
        "http://localhost:8000/submit-captcha",
        { captcha: captchaValue }
      );

      setCaptchaImage(null);
      setCaptchaValue("");
      setCaptchaLoaded(false);

      setStatus("Captcha submitted. Scraper continuing...");



    } catch (err) {
      console.log(err);
    }

  };


  const checkCaptcha = async () => {

    try {

      const res = await axios.get(
        "http://localhost:8000/captcha",
        { responseType: "blob" }
      );

      if (res.status === 200 && res.data.size > 0) {

        const url = URL.createObjectURL(res.data);

        setCaptchaImage(url);
        setStatus("OCR failed. Please enter captcha manually.");

      }

    } catch (err) {
      console.log("Captcha not ready");
    }

  };


  const loadSRO = async () => {

    try {

      const res = await axios.get(
        "http://localhost:8000/sro"
      );

      setSroList(res.data || []);

    } catch (err) {
      console.log(err);
    }

  };




  const loadLocalities = async (sroName) => {

    try {

      const res = await axios.get(
        `http://localhost:8000/localities?sro_name=${sroName}`
      );

      setLocalityList(res.data || []);

    } catch (err) {
      console.log(err);
    }

  };

  useEffect(() => {

    loadSRO();

    const ws = new WebSocket("ws://127.0.0.1:8000/ws/status");

    ws.onmessage = async (event) => {

      const message = event.data;
      setStatus(message);

      if (
        message.includes("Enter captcha manually") &&
        !captchaLoaded
      ) {

        try {

          const res = await axios.get(
            "http://localhost:8000/captcha",
            { responseType: "blob" }
          );

          if (res.status === 200 && res.data.size > 0) {

            const url = URL.createObjectURL(res.data);

            setCaptchaImage(url);
            setCaptchaLoaded(true);   // prevent multiple calls

          }

        } catch (err) {
          console.log("Captcha image not ready yet");
        }

      }

    };

    ws.onopen = () => {
      ws.send("connected");
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };

  }, []);



  const fetchRecords = async () => {

    if (!sro || !locality) {
      alert("Select SRO and Locality first");
      return;
    }

    try {

      const params = {
        sro_name: sro,
        locality_name: locality
      };

      if (year) params.year = year;
      if (monthFrom) params.month_from = monthFrom;
      if (monthTo) params.month_to = monthTo;
      if (firstPartySearch) params.first_party = firstPartySearch;
      if (secondPartySearch) params.second_party = secondPartySearch;
      if (addressSearch) params.address = addressSearch;
      if (pincodeSearch) params.pincode = pincodeSearch;
      if (minArea) params.min_area = minArea;
      if (maxArea) params.max_area = maxArea;
      if (propertyType) params.property_type = propertyType;

      const res = await axios.get(
        "http://localhost:8000/records",
        { params }
      );

      // 🔥 ADD 
      console.log("FULL API RESPONSE:", res.data);
      console.log("IS ARRAY:", Array.isArray(res.data));

      // DEBUG
      console.log(
        "Total records from API:",
        Array.isArray(res.data) ? res.data.length : 0
      );

      // ALWAYS update records first
      setRecords(Array.isArray(res.data) ? res.data : []);

      const safeData = Array.isArray(res.data) ? res.data : [];

      if (safeData.length === 0) {
        setStatus("No data in DB. Scraper started. Data will appear shortly...");
      } else {
        setStatus(`Data loaded from database (${safeData.length} records)`);
      }

      

    } catch (err) {

      console.log(err);
      alert("Failed to fetch records");

    }

  };


  const stopScraper = async () => {
    try {

      await axios.post("http://localhost:8000/stop-scraper");

      setStatus("Scraper stopped");
      setScraperRunning(false);

      setRecords([]);
      setCaptchaImage(null);

      setSro("");
      setLocality("");

    } catch (err) {
      console.log(err);
    }
  };






  return (

    <div className="container">

      <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
        <h1 className="title">Delhi Property Scraper</h1>

        <button
          style={{
            background:"#ff4d4f",
            color:"white",
            border:"none",
            padding:"8px 14px",
            borderRadius:"6px",
            cursor:"pointer"
          }}
          onClick={stopScraper}
        >
          Stop Scraping
        </button>
      </div>

      <div className="card">

        <label>Select SRO</label>

        <select
          className="input"
          value={sro}

          onChange={(e) => {
            const selectedSRO = e.target.value;

            setSro(selectedSRO);
            setLocality("");

            setStatus("Select Locality");

            loadLocalities(selectedSRO);
          }}
        >

          <option value="">Select SRO</option>

          {sroList.map((s, i) => (
            <option key={i} value={s}>
              {s}
            </option>
          ))}

        </select>

        <label>Select Locality</label>

        <select
          className="input"
          value={locality}
          onChange={(e) => {
            setLocality(e.target.value);
            setStatus("Click Start Scraping");
          }}
        >

          <option value="">Select Locality</option>

          {localityList.map((l, i) => (
            <option key={i} value={l}>
              {l}
            </option>
          ))}

        </select>

        <button
          className="button"
          onClick={fetchRecords}
        >
          Fetch Records
        </button>

        {/* <button
          className="button"
          onClick={startScraper}
        >
          Start Scraping

        </button> */}





        <div className="status">
          Status: {status}
        </div>


        {status.includes("Enter captcha manually") && captchaImage && (

          <div style={{ marginTop: "20px" }}>

            <p>Enter Captcha</p>

            <img
              src={captchaImage}
              alt="captcha"
              style={{ marginBottom: "10px" }}
            />

            <input
              className="input"
              value={captchaValue}
              onChange={(e) => setCaptchaValue(e.target.value)}
              placeholder="Enter captcha"
            />

            <button
              className="button"
              onClick={submitCaptcha}
            >
              Submit Captcha
            </button>

          </div>

        )}

      </div>


      <div className="results-section">





        <button
          className="filter-toggle"
          onClick={() => setShowFilters(true)}
        >
          ☰ Filters
        </button>


        {/* <div className="filter-section">

        <div className="filters">

        <input
        placeholder="Year (2023)"
        value={year}
        onChange={(e)=>setYear(e.target.value)}
        />

        <div>

        <label>Month From</label>

        <select
        value={monthFrom}
        onChange={(e)=>setMonthFrom(e.target.value)}
        >
        <option value="">Start Month</option>
        <option value="1">January</option>
        <option value="2">February</option>
        <option value="3">March</option>
        <option value="4">April</option>
        <option value="5">May</option>
        <option value="6">June</option>
        <option value="7">July</option>
        <option value="8">August</option>
        <option value="9">September</option>
        <option value="10">October</option>
        <option value="11">November</option>
        <option value="12">December</option>
        </select>

        <label>Month To</label>

        <select
        value={monthTo}
        onChange={(e)=>setMonthTo(e.target.value)}
        >
        <option value="">End Month</option>
        <option value="1">January</option>
        <option value="2">February</option>
        <option value="3">March</option>
        <option value="4">April</option>
        <option value="5">May</option>
        <option value="6">June</option>
        <option value="7">July</option>
        <option value="8">August</option>
        <option value="9">September</option>
        <option value="10">October</option>
        <option value="11">November</option>
        <option value="12">December</option>
        </select>

        </div>

        <input
        placeholder="First Party"
        value={firstPartySearch}
        onChange={(e)=>setFirstPartySearch(e.target.value)}
        />

        <input
        placeholder="Second Party"
        value={secondPartySearch}
        onChange={(e)=>setSecondPartySearch(e.target.value)}
        />

        <input
        placeholder="Address"
        value={addressSearch}
        onChange={(e)=>setAddressSearch(e.target.value)}
        />

        <input
        placeholder="Pincode"
        value={pincodeSearch}
        onChange={(e)=>setPincodeSearch(e.target.value)}
        />

        <input
        placeholder="Min Area"
        value={minArea}
        onChange={(e)=>setMinArea(e.target.value)}
        />

        <input
        placeholder="Max Area"
        value={maxArea}
        onChange={(e)=>setMaxArea(e.target.value)}
        />

        <input
        placeholder="Property Type"
        value={propertyType}
        onChange={(e)=>setPropertyType(e.target.value)}
        />

        </div> */}



        {showFilters && (

          <div className="filter-overlay">

            <div className="filter-panel">

              <h3>Filters</h3>

              <div className="filters">

                {/* ROW 1 */}
                <div className="filter-row">

                  <input
                    className="year-input"
                    placeholder="Year (2023)"
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                  />

                  <div className="month-range">

                    <select
                      value={monthFrom}
                      onChange={(e) => setMonthFrom(e.target.value)}
                    >
                      <option value="">Month From</option>
                      <option value="1">January</option>
                      <option value="2">February</option>
                      <option value="3">March</option>
                      <option value="4">April</option>
                      <option value="5">May</option>
                      <option value="6">June</option>
                      <option value="7">July</option>
                      <option value="8">August</option>
                      <option value="9">September</option>
                      <option value="10">October</option>
                      <option value="11">November</option>
                      <option value="12">December</option>
                    </select>

                    <span className="month-separator">-</span>

                    <select
                      value={monthTo}
                      onChange={(e) => setMonthTo(e.target.value)}
                    >
                      <option value="">Month To</option>
                      <option value="1">January</option>
                      <option value="2">February</option>
                      <option value="3">March</option>
                      <option value="4">April</option>
                      <option value="5">May</option>
                      <option value="6">June</option>
                      <option value="7">July</option>
                      <option value="8">August</option>
                      <option value="9">September</option>
                      <option value="10">October</option>
                      <option value="11">November</option>
                      <option value="12">December</option>
                    </select>

                  </div>

                </div>


                {/* ROW 2 */}
                <div className="filter-row">

                  <input
                    placeholder="First Party"
                    value={firstPartySearch}
                    onChange={(e) => setFirstPartySearch(e.target.value)}
                  />

                  <input
                    placeholder="Second Party"
                    value={secondPartySearch}
                    onChange={(e) => setSecondPartySearch(e.target.value)}
                  />

                </div>


                {/* ROW 3 */}
                <div className="filter-row">

                  <input
                    placeholder="Address"
                    value={addressSearch}
                    onChange={(e) => setAddressSearch(e.target.value)}
                  />

                  <input
                    placeholder="Pincode"
                    value={pincodeSearch}
                    onChange={(e) => setPincodeSearch(e.target.value)}
                  />

                </div>


                {/* ROW 4 */}
                <div className="filter-row">

                  <input
                    className="full-width"
                    placeholder="Property Type"
                    value={propertyType}
                    onChange={(e) => setPropertyType(e.target.value)}
                  />

                </div>

              </div>






              <div className="filter-buttons">

                <button onClick={fetchRecords}>Apply Filters</button>

                <button
                  className="clear-btn"
                  onClick={() => setShowFilters(false)}
                >
                  Close
                </button>

              </div>

            </div>

          </div>

        )}

        <div className="table-container">

          <p className="record-count">
            Total Records: {Array.isArray(records) ? records.length : 0}
          </p>

          <table>

            <thead>

              <tr>

                <th>Reg No</th>
                <th>Date</th>
                <th>First Party</th>
                <th>Second Party</th>
                <th>Address</th>
                <th>Area</th>
                <th>Deed Type</th>
                <th>Property Type</th>

              </tr>

            </thead>


            <tbody>

              {Array.isArray(records) &&
                records.map((r, i) => (
                <tr key={r.id}>

                  <td>{r.reg_no}</td>
                  <td>{r.reg_date}</td>
                  <td>{r.first_party}</td>
                  <td>{r.second_party}</td>
                  <td>{r.property_address}</td>
                  <td>{r.area}</td>
                  <td>{r.deed_type}</td>
                  <td>{r.property_type}</td>

                </tr>
              ))}

            </tbody>


          </table>

        </div>

      </div>

    </div>


  );

}




export default App;

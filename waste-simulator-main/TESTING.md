# SWMS Testing

Run the isolated automated suite from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The tests use SQLite only for isolation and exercise the public API: unauthenticated rejection, registration, JWT login, location persistence, person-based waste calculation, a year 0 through year 5 forecast, and GIS feature output. Production uses the `DATABASE_URL` supplied for `swms_db`.

Manual smoke sequence:

1. Start FastAPI and open `/docs`.
2. Register a `SUPER_ADMIN`, log in, and authorize with the bearer token.
3. Create a location and post its seven parameter-category records.
4. Run a simulation and confirm its results feed dashboard, map, and chatbot requests.
5. Import the Postman collection and execute the same sequence.

Expected calculation check: population `10,000` × `0.5 kg/person/day` returns `5,000 kg/day`; at 2% population growth the year-5 forecast is greater than 11,040 people.

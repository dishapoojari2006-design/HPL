# SWMS Postman guide

Import both JSON files, select **SWMS Local**, then run Register, Login, Create location, Calculate waste and Run simulation in that order. The environment stores the JWT and location ID automatically. The API routes for parameter categories use `POST/GET /locations/{locationId}/{category}` where category is one of `demography`, `infrastructure`, `industrial`, `environment`, `terrain`, `economic`, `cultural`, `habitations`, `waste`, `events`, `strategies`, or `scenarios`.

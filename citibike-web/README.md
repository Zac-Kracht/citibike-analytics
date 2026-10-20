# Layout
Web page loads centered on NYC or your current location
Pins mark the location of each station
Pins are color coded by inventory
When a pin is clicked on, a panel appears on the right
The panel contains sections for:
- Current inventory
- Top 5 destinations
- Average use by hour
When a pin is clicked on the map zooms to show the pin + the top 5 destination pins
- selected pin turns gold, destination pins turn blue
- stretch: directions appear to each pin
Toggleable heatmap overlay on map

# API Configuration
Set `VITE_CITIBIKE_API_BASE_URL` in the web app's environment to the API origin, for example `http://localhost:8080` for local development. Vite embeds this value at build time, so production deployments must provide the production API origin during the frontend build.

# TODO Top 5 Destinations Panel
- Database (Dynamo)
- Silver to Gold Glue job
- New API endpoint
- Frontend Integration


# TODO Phase 2
Heatmap
Daily average use graph
Tab icon
Mobile view
Prod infra (secret, cloudFront, R53, domain)

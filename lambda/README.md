source: station_status -> lambda (every 3 min)      -> bronze -> gbfs glue (hourly)       -> silver
source: station_info   -> lambda (daily @ 12 UTC)   -> bronze -> gbfs glue (hourly)       -> silver
source: trips          -> lambda (monthly on 15th)  -> bronze -> trips glue (event based) -> silver
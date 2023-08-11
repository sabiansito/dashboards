SELECT 
    "WellName",
    "WellAPI",
    AVG("Latitude") "Latitude",
    AVG("Longitude") "Longitude",
    AVG("X") "Easting",
    AVG("Y") "Northing" 
FROM 
    "aqueon"."completiondata" 
WHERE 
    "casename"={case_name}
GROUP BY "WellName","WellAPI"
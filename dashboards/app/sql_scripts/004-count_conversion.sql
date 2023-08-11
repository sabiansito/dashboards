SELECT 
    COUNT(DISTINCT("WellAPI")) "conversion_wells" 
FROM (
    SELECT 
        "WellAPI",
        COUNT(DISTINCT("Status")) "status_count" 
    FROM 
        "aqueon"."productiondata" 
    WHERE 
        "casename"={case_name}
    GROUP BY 
        "WellAPI" 
    HAVING 
        COUNT(DISTINCT("Status"))>1
) "sq0"
SELECT 
    COUNT(DISTINCT("WellAPI")) "total_wells" 
FROM 
    "aqueon"."productiondata" 
WHERE 
    "casename"={case_name}
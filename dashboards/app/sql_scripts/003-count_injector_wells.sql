SELECT 
    COUNT(DISTINCT("WellAPI")) "injector_wells" 
FROM "aqueon"."productiondata" 
WHERE 
    "Qs">0 
AND 
    "casename"={case_name}
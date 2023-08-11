SELECT 
    COUNT(DISTINCT("WellAPI")) "producer_wells" 
FROM 
    "aqueon"."productiondata" 
WHERE 
    "Qo"+"Qw"+"Qg">0 
AND 
    "casename"={case_name}
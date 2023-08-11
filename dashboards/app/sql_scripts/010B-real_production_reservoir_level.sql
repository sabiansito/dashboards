SELECT 
    MAKE_DATE("productiondata"."Year","productiondata"."Month",1) "date",
    "completiondata"."Reservoir" "reservoir",
    SUM("productiondata"."Qo") "oil",
    SUM("productiondata"."Qw") "water",
    SUM("productiondata"."Qg") "gas",
    SUM("productiondata"."Qs") "inj" 
FROM "aqueon"."productiondata" 
LEFT JOIN 
    "aqueon"."completiondata" 
    ON "productiondata"."WellAPI"="completiondata"."WellAPI" 
    AND "productiondata"."casename"="completiondata"."casename" 
    AND "productiondata"."CompSubId"="productiondata"."CompSubId" 
WHERE 
    "productiondata"."casename"={case_name} 
GROUP BY 
    "date","reservoir" 
ORDER BY 
    "reservoir","date"
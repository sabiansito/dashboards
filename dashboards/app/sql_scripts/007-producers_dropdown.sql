(
    SELECT 
        DISTINCT 
            "completiondata"."WellName",
            "productiondata"."WellAPI",
            "productiondata"."Status" 
    FROM 
        "aqueon"."productiondata" 
    LEFT JOIN 
        "aqueon"."completiondata" 
    ON "productiondata"."WellAPI"="completiondata"."WellAPI" 
    AND "productiondata"."casename"="completiondata"."casename" 
    WHERE "productiondata"."casename"={case_name} 
    AND "productiondata"."Qo"+"productiondata"."Qw"+"productiondata"."Qg">0) 
UNION (
    SELECT DISTINCT 
        "completiondata"."WellName",
        "productiondata"."WellAPI",
        "productiondata"."Status" 
    FROM 
        "aqueon"."productiondata" 
    LEFT JOIN "aqueon"."completiondata" 
    ON "productiondata"."WellAPI"="completiondata"."WellAPI" 
    AND "productiondata"."casename"="completiondata"."casename" 
    WHERE "productiondata"."casename"={case_name}
    AND "productiondata"."Qs">0
)
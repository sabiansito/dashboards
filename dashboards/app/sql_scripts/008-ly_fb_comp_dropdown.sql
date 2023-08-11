(
    SELECT 
        DISTINCT 
            "Reservoir" "name",
        'layer' "type" 
    FROM 
        "aqueon"."completiondata" 
    WHERE 
        "casename"={case_name}
) 
UNION 
(
    SELECT 
        DISTINCT 
            "FaultBlock" "name",
        'faulblock' "type" 
    FROM 
        "aqueon"."completiondata" 
    WHERE "casename"={case_name}
) 
UNION 
(
    SELECT 
        DISTINCT 
            "Compartment" "name",
        'compartment' "type" 
    FROM "aqueon"."completiondata" 
    WHERE "casename"={case_name}
)
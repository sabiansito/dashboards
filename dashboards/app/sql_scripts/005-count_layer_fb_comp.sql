SELECT 
    COUNT(DISTINCT("Reservoir")) "total_layers",
    COUNT(DISTINCT("FaultBlock")) "total_faultblocks",
    COUNT(DISTINCT("Compartment")) "total_compartments" 
FROM 
    "aqueon"."completiondata" 
WHERE 
    "casename"={case_name}
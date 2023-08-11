SELECT 
    "FitStartDate" "fit_startdate",
    "FitEndDate" "fit_enddate",
    "IsBacktest" "is_backtest",
    "BacktestEndDate" "backtest_enddate",
    "Dt" "dt" 
FROM 
    "aqueon"."fit_info" 
WHERE 
    "casename"={case_name}
LIMIT 1
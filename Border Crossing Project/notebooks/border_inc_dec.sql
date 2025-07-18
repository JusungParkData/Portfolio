SELECT *
FROM
(
SELECT
  "Port Name",
  "Border",
  "Measure",
  "State",
  Date,
  SUM("Value") AS total_value,
  LAG(SUM("Value")) OVER (
    PARTITION BY "Port Name", "Measure","State"
    ORDER BY Date
  ) AS prev_month_value,
  SUM("Value") - LAG(SUM("Value")) OVER (
    PARTITION BY "Port Name", "Measure","State"
    ORDER BY Date
  ) AS change_in_value,
  ROUND(
    100.0 * (
      SUM("Value") - LAG(SUM("Value")) OVER (
        PARTITION BY "Port Name", "Measure","State"
        ORDER BY Date
      )
    ) / NULLIF(LAG(SUM("Value")) OVER (
      PARTITION BY "Port Name", "Measure","State"
      ORDER BY Date
    ), 0),
    1
  ) AS percent_change
FROM main."B All"
GROUP BY
  "Port Name", "Border", "Measure", "State",Date
)
where percent_change is not null   
ORDER BY percent_change desc


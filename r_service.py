You are an expert R programmer specializing in data visualization with ggplot2.
Your task is to generate a complete, well-commented R script to create a chart for the following concept: "{chart_idea}".

Instructions:
1.  The script MUST use the `ggplot2` library.
2.  The script should create its own sample data in a tibble or data frame. Do not assume any external data files.
3.  The chart should be aesthetically pleasing and professional-looking. Use `theme_minimal()` or `theme_bw()`.
4.  The script should be self-contained and ready to run.
5.  CRITICAL: Do NOT include a `ggsave()` command in your script. The calling function will handle saving the plot.
6.  The final line of your script should be the ggplot object itself, so it can be captured by `last_plot()`.

Example for "Supply and Demand Curve":
```r
# Load necessary library
library(ggplot2)

# Create sample data for supply and demand
price <- seq(1, 10, by = 1)
quantity_demanded <- 100 - 6 * price
quantity_supplied <- 10 + 4 * price

demand_curve <- data.frame(price, quantity = quantity_demanded, curve = "Demand")
supply_curve <- data.frame(price, quantity = quantity_supplied, curve = "Supply")

market_data <- rbind(demand_curve, supply_curve)

# Create the plot
ggplot(market_data, aes(x = quantity, y = price, color = curve)) +
  geom_line(linewidth = 1.2) +
  scale_color_manual(values = c("Demand" = "blue", "Supply" = "red")) +
  labs(
    title = "Supply and Demand Curves",
    x = "Quantity",
    y = "Price",
    color = "Curve"
  ) +
  theme_minimal()
```

# Figure 3 Dose Response Curves during intermittent or continuous treatments
# Panels A and B

## Environment
library(tidyverse)
library(magrittr)
library(cowplot)
source("code/Helper_Functions/theme_int_dosing.R")

## Ingest Data
dose_data <- read_csv("data/intermittent_dose_response.csv")
dose_data_longer <- dose_data %>% pivot_longer(!c(sample, rep_number), values_to = "cell_number", names_to = "LGX818")
dose_data_longer$LGX818 %<>% as.numeric()
dose_data_continuous <- filter(dose_data_longer, sample =="Vector Control" | sample =="V600E" | sample =="Week 1" |sample =="Week 2 C" | sample =="Week 3 C" | sample =="Week 4 C")
dose_data_int = filter(dose_data_longer, sample =="Vector Control" | sample =="V600E" | sample =="Week 1" |sample =="Week 2 I" | sample =="Week 3 I" | sample =="Week 4 I")
x_axis_labels = c(0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, "3,000", "10,000")

## Plot Dose Response for Continuously Treated Cells
ggplot(dose_data_continuous, aes(x=LGX818, y = cell_number, group = sample, color = sample))+
  stat_summary(geom = "point", fun=mean, size = 1, shape = 16, show.legend = FALSE)+
  stat_summary(geom = "errorbar", width = .2, size = .5, fun.data = mean_se, show.legend = FALSE)+
  geom_smooth(method = "loess", se = FALSE, span = 0.5, size = .75)+
  geom_vline(xintercept = 500, linetype = "dotted", color = "#222222", alpha = 0.5)+
  scale_x_log10("LGX818 Concentration (nM)", 
                labels = c(0, x_axis_labels),
                breaks = c(0.01, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000), 
                expand = c(0.02,0))+
  annotation_logticks(sides = "b", size = 0.2, 
                      short = unit(0.03, "cm"), mid = unit(0.05, "cm"), long = unit(0.1, "cm"),
                      color = "#222222")+
  scale_y_continuous("Normalized Cell Number", breaks = c(0, .25, .5, .75, 1))+
  scale_color_manual(values = c("#222222", "#777777",  "#92c5de","#EF8A63", "#2767AB", "#B11F30"))+
  coord_cartesian(xlim = c(0.01, 10000), ylim = c(0, 1.05))+
  theme_int_dosing(legend = "none", aspect = 0.875, base_size = 9)+
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        plot.margin = margin(t = 0, r = 0, b = 0, l = 0, unit = "pt"))
ggsave("results/fig3_a_continuous_dose_response.pdf", height = 2.65, width = 3, units = "in")

## Plot Dose Response for Intermittently Treated Cells
ggplot(dose_data_int, aes(x=LGX818, y = cell_number, group = sample, color = sample, linetype = sample))+
  stat_summary(geom = "point", fun=mean, size = 1, shape = 16, show.legend = FALSE)+
  stat_summary(geom = "errorbar", width = .2, size = .5, fun.data = mean_se, show.legend = FALSE)+
  geom_smooth(method = "loess", se = FALSE, span = 0.5, size = .75)+
  geom_vline(xintercept = 500, linetype = "dotted", color = "#222222", alpha = 0.5)+
  scale_x_log10("LGX818 Concentration (nM)", 
                labels = c(0, x_axis_labels),
                breaks = c(0.01, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000), 
                expand = c(0.02,0))+
  annotation_logticks(sides = "b", size = 0.2, 
                      short = unit(0.03, "cm"), mid = unit(0.05, "cm"), long = unit(0.1, "cm"),
                      color = "#222222")+
  scale_y_continuous("Normalized Cell Number", breaks = c(0, .25, .5, .75, 1))+
  scale_linetype_manual(values = c("solid", "solid", "solid", "dashed", "solid", "dashed"))+
  scale_color_manual(values = c("#222222", "#777777",  "#92c5de","#EF8A63", "#2767AB", "#B11F30"))+
  coord_cartesian(xlim = c(0.01, 10000), ylim = c(0, 1.05))+
  theme_int_dosing(legend = "none", aspect = 0.875, base_size = 9)+
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        plot.margin = margin(t = 0, r = 0, b = 0, l = 0, unit = "pt"))
ggsave("results/fig3_b_intermittent_dose_response.pdf", height = 2.65, width = 3, units = "in")
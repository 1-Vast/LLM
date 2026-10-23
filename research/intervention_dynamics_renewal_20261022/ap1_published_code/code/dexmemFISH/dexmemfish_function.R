
library(ggplot2)
library(dplyr)
library(tidyr)

# Function to safely convert to numeric
convert_to_numeric <- function(df, cols_to_convert) {
  existing_cols <- intersect(cols_to_convert, names(df))
  df[existing_cols] <- lapply(df[existing_cols], function(x) as.numeric(as.character(x)))
  return(df)
}

# Function to extract identifier from filename
extract_identifier <- function(filename) {
  sub(".*-(.*)\\.csv$", "\\1", basename(filename))
}

# Main function to process and plot data
process_and_plot_data <- function(inputdirectory, outputdirectory) {

  
  
  # Columns to convert
  cols_to_convert <- c("cy3", "a594", "cy5", "cy7","cell.Blob.Blob.metrics...Area","cell.Blob.Blob.metrics...Perimeter","cell.Blob.Blob.metrics...Centroid...y","cell.Blob.Blob.metrics...Centroid...x")
  
  extract_identifier <- function(filename) {
    # Extracting everything after the last "-" and before the ".csv"
    sub(".*-(.*)\\.csv$", "\\1", basename(filename))
  }
  
  # Step 1: Import Data, Convert Types, and Add Identifier
  files <- list.files(path = inputdirectory, pattern = "*.csv", full.names = TRUE)
  data_list <- lapply(files, function(f) {
    df <- read.csv(f, stringsAsFactors = FALSE)
    df <- convert_to_numeric(df, cols_to_convert)
    df$file_identifier <- extract_identifier(f) # Adding the identifier
    return(df)
  })
  
  
  # Combining all data into one dataframe
  all_data <- bind_rows(data_list, .id = "file_id")
  
  # Reshape the data for plotting
  melted_data_filtered <- all_data %>%
    dplyr::select(cy3, a594, cy5, cy7, file_identifier) %>%
    gather(key = "variable", value = "value", -file_identifier) %>%
    dplyr::filter(variable %in% c("cy3", "a594", "cy5", "cy7"))
  
  # Convert the 'value' column to numeric and handle conversion issues
  melted_data_filtered$value <- as.numeric(as.character(melted_data_filtered$value))
  
  # Omit NA values if any exist after conversion
  melted_data_filtered <- na.omit(melted_data_filtered)
  
  # Normalize cy3, a594, and cy5 by cy7
  all_data <- all_data %>%
  dplyr::mutate(cy3_norm = cy3 / cy7,
           a594_norm = a594 / cy7,
           cy5_norm = cy5 / cy7)
  
  # Reshape the normalized data for plotting
  melted_normalized_data <- all_data %>%
    dplyr::select(file_identifier, cy3_norm, a594_norm, cy5_norm) %>%
    gather(key = "variable", value = "value", -file_identifier)
  
  #normalize by area
  all_data <- all_data %>%
  dplyr::mutate(micron2 = `cell.Blob.Blob.metrics...Area` * 0.0467) %>%
  dplyr::mutate(cy3_areanorm_RNApermicron2 = cy3 / `micron2`,
           a594_areanorm_RNApermicron2 = a594 / `micron2`,
           cy5_areanorm_RNApermicron2 = cy5 / `micron2`)
  
  # Reshape the normalized data for plotting
  melted_areanormalized_data <- all_data %>%
    dplyr::select(file_identifier, cy3_areanorm_RNApermicron2, a594_areanorm_RNApermicron2, cy5_areanorm_RNApermicron2) %>%
    gather(key = "variable", value = "value", -file_identifier) %>%
    na.omit()
  
  
  #save plots
  rawcounts_plot <- ggplot(melted_data_filtered, aes(x = file_identifier, y = value, fill = variable)) +
    geom_boxplot(outlier.shape = NA) +  # Exclude outliers
    facet_wrap(~ variable, scales = "free") +
    theme_minimal() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5)) +
    labs(title = "Box Plot Comparison of cy3, a594, cy5, cy7 Across Files",
         x = "Variable",
         y = "Value") +
    scale_fill_brewer(palette = "Set3")
  
  rawcounts_plot
  
  normalized_plot <- ggplot(melted_normalized_data, aes(x = file_identifier, y = value, fill = variable)) +
    geom_boxplot(outlier.shape = NA) +  # Exclude outliers
    facet_wrap(~ variable, scales = "free") +
    theme_minimal() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5)) +
    labs(title = "Box Plot Comparison of Normalized cy3, a594, cy5 Across Files",
         x = "Normalized Variable",
         y = "Normalized Value") +
    scale_fill_brewer(palette = "Set3")
  
  normalized_plot
  
  areanormalized_plot <- ggplot(melted_areanormalized_data, aes(x = file_identifier, y = value, fill = variable)) +
    geom_boxplot(outlier.shape = NA) +  # Exclude outliers outlier.shape = NA
   # geom_jitter(aes(color = variable), width = 0.3, alpha = 0.3) + 
    facet_wrap(~ variable, scales = "free") +
    theme_minimal() +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5)) +
    labs(title = "Box Plot Comparison of area Normalized cy3, a594, cy5 Across Files",
         x = "Normalized Variable",
         y = "Normalized Value") +
    scale_fill_brewer(palette = "Set3") +
    scale_color_brewer(palette = "Set3")
  
  areanormalized_plot
  
  # Save the plot as a PDF
  ggsave(filename = paste0(outputdirectory, "/normalized_boxplots.pdf"), plot = normalized_plot, width = 11, height = 8, device = "pdf")
  ggsave(filename = paste0(outputdirectory, "/rawcounts_boxplots.pdf"), plot = rawcounts_plot, width = 11, height = 8, device = "pdf")
  ggsave(filename = paste0(outputdirectory, "/normalized_boxplots_area.pdf"), plot = areanormalized_plot, width = 11, height = 8, device = "pdf")
  
}

# Example usage of the function
#process_and_plot_data("/path/to/input/directory", "/path/to/output/directory")


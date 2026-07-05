import pandas as pd

# Read dataset
mozilla = pd.read_csv("dataset/mozilla/mozilla_bugs.csv")

# Keep only required columns
mozilla = mozilla[["Description", "Severity"]]

# Remove empty rows
mozilla = mozilla.dropna()

# Save cleaned dataset
mozilla.to_csv(
    "dataset/mozilla/clean_mozilla.csv",
    index=False
)

print("Dataset cleaned successfully!")
print(mozilla.head())
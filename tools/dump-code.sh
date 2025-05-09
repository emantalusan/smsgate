#!/bin/bash

# Check if a destination file is provided as an argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <destination_file>"
  exit 1
fi

destination_file="$1"

# Function to recursively find and concatenate files
concatenate_files() {
  local directory="$1"
  local dest_file="$2"
  find "$directory" -type f -exec grep -Iq . {} \; -print0  | while IFS= read -r -d $'\0' file; do
  #find "$directory" -type f \( -name "*.py" -o -name "*.html" -o -name "*.json" -o -name "*.txt" -o -name "*.sh" \) -print0 | while IFS= read -r -d $'\0' file; do
    if [ -f "$file" ]; then
      echo "--- $file ---" >> "$dest_file"
      cat "$file" >> "$dest_file"
      echo "" >> "$dest_file" # Add a newline separator
    fi
  done
}

# Start the concatenation from the current directory
concatenate_files "." "$destination_file"

echo "Concatenation complete. Files written to: $destination_file"
